"""Registry validation and method dispatch must preserve numerical contracts."""

from dataclasses import replace

import pytest
from uncertainties import nominal_value, std_dev, ufloat

from snowpyt_mechparams.execution.dispatcher import (
    MethodDispatcher,
    _get_layer_input,
    _is_nan_result,
)
from snowpyt_mechparams.methods import default_registry, ParameterLevel
from snowpyt_mechparams.methods.layer import (
    calculate_density,
    calculate_elastic_modulus,
    calculate_poissons_ratio,
    calculate_shear_modulus,
)
from snowpyt_mechparams.models import Layer


def test_registry_duplicate_rejected_without_changing_entries():
    registry = default_registry()
    spec = registry.require("density", "geldsetzer")
    before = registry.all()
    with pytest.raises(ValueError, match="Duplicate method specification"):
        registry.register(replace(spec, description="replacement"))
    assert registry.all() == before
    assert registry.require("density", "geldsetzer") is spec
    assert registry.methods_for("density").count(spec) == 1


def test_registry_unknown_alias_defaults_and_level_partition():
    registry = default_registry()
    assert registry.get("density", "absent") is None
    with pytest.raises(KeyError, match="Unknown method: density.absent"):
        registry.require("density", "absent")
    assert registry.methods_for("absent") == []
    assert registry.default_method_for("absent") is None
    assert registry.default_method_for("density").method_name == "data_flow"
    assert registry.require("density", "kim_jamieson_table5") is registry.require(
        "density", "kim_jamieson_table6"
    )
    methods = registry.as_method_dict()
    assert methods["density"] == [
        "data_flow",
        "geldsetzer",
        "kim_jamieson_table2",
        "kim_jamieson_table6",
    ]
    methods["density"].clear()
    assert len(registry.methods_for("density")) == 4
    layers = registry.targets_by_level(ParameterLevel.LAYER)
    slabs = registry.targets_by_level(ParameterLevel.SLAB)
    assert layers == {"density", "elastic_modulus", "poissons_ratio", "shear_modulus"}
    assert not layers & slabs
    assert layers | slabs == {s.target for s in registry.all()}


@pytest.mark.parametrize(
    "target,method,required",
    [
        (s.target, s.method_name, name)
        for s in default_registry().all()
        if s.level == ParameterLevel.LAYER
        for name in s.required_inputs
    ],
)
def test_each_registered_layer_method_rejects_each_missing_input(
    target, method, required
):
    layer = Layer(
        density_measured=250,
        density_calculated=250,
        hand_hardness="1F",
        grain_form="FC",
        grain_size_avg=1,
        elastic_modulus=20,
        poissons_ratio=0.2,
    )
    attribute = {
        "density": "density_calculated",
        "grain_size": "grain_size_avg",
        "hand_hardness_index": "hand_hardness",
    }.get(required, required)
    setattr(layer, attribute, None)
    result, error = MethodDispatcher().execute(target, method, layer=layer)
    assert result is None
    assert error == f"Missing required inputs for {target}.{method}"


@pytest.mark.parametrize(
    "target,method", [(s.target, s.method_name) for s in default_registry().all()]
)
def test_each_registered_method_requires_correct_container(target, method):
    result, error = MethodDispatcher().execute(target, method)
    assert result is None
    level = default_registry().require(target, method).level
    assert error == (
        "Layer required for layer-level method"
        if level == ParameterLevel.LAYER
        else "Slab required for slab-level method"
    )


def test_dispatcher_unknown_introspection_and_exception_boundary():
    dispatcher = MethodDispatcher()
    assert dispatcher.execute("density", "absent") == (
        None,
        "Unknown method: density.absent",
    )
    assert not dispatcher.supports_method_uncertainty("density", "absent")
    assert not dispatcher.supports_method_uncertainty("density", "data_flow")
    assert dispatcher.supports_method_uncertainty("density", "geldsetzer")
    assert dispatcher.get_all_methods() == default_registry().as_method_dict()
    result, error = dispatcher.execute(
        "shear_modulus",
        "lame_relationship",
        layer=Layer(elastic_modulus="bad", poissons_ratio=0.2),
    )
    assert result is None
    assert error.startswith("Execution error:")
    assert "unsupported operand" in error


def test_input_conversion_identity_and_no_measured_density_fallback():
    measured = ufloat(250, 25)
    layer = Layer(density_measured=measured, grain_size_avg=2)
    assert _get_layer_input(layer, "density_measured") is measured
    assert _get_layer_input(layer, "density") is None
    assert _get_layer_input(layer, "unknown") is None
    size = _get_layer_input(layer, "grain_size")
    assert nominal_value(size) == 2
    assert std_dev(size) == 0
    result, error = MethodDispatcher().execute("density", "data_flow", layer=layer)
    assert result is measured
    assert error is None


@pytest.mark.parametrize(
    "grain,method,expected",
    [
        ("PPgp", "geldsetzer", 157),
        ("RGxf", "geldsetzer", 154 + 1.51 * 2**3.15),
        ("FCxr", "kim_jamieson_table2", 186),
        ("PPgp", "kim_jamieson_table5", 132.1),
    ],
)
def test_dispatcher_preserves_subgrain_coefficients_and_alias(grain, method, expected):
    layer = Layer(hand_hardness="4F", grain_form=grain, grain_size_avg=1)
    value, error = MethodDispatcher().execute(
        "density", method, layer=layer, include_method_uncertainty=False
    )
    assert error is None
    assert nominal_value(value) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize(
    "grain,hardness", [("SH", "4F"), (None, "4F"), ("FC", "unknown")]
)
def test_dispatcher_unsupported_observations(grain, hardness):
    value, error = MethodDispatcher().execute(
        "density", "geldsetzer", layer=Layer(grain_form=grain, hand_hardness=hardness)
    )
    assert value is None
    assert error == "Missing required inputs for density.geldsetzer"


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        (2, False),
        (float("nan"), True),
        (ufloat(float("nan"), 1), True),
        (ufloat(2, 1), False),
        ("metadata", False),
    ],
)
def test_nan_result_classification(value, expected):
    assert _is_nan_result(value) is expected


@pytest.mark.parametrize(
    "calculate,method,kwargs",
    [
        (calculate_density, "geldsetzer", {"grain_form": "PP"}),
        (calculate_density, "kim_jamieson_table2", {"grain_form": "PP"}),
        (
            calculate_density,
            "kim_jamieson_table6",
            {"grain_form": "PP", "hand_hardness_index": 1},
        ),
        (calculate_elastic_modulus, "bergfeld", {"grain_form": "RG"}),
        (calculate_elastic_modulus, "kochle", {"grain_form": "RG"}),
        (calculate_elastic_modulus, "wautier", {"grain_form": "RG"}),
        (calculate_elastic_modulus, "schottner", {"grain_form": "RG"}),
        (calculate_poissons_ratio, "kochle", {}),
        (calculate_poissons_ratio, "srivastava", {"grain_form": "RG"}),
        (calculate_shear_modulus, "lame_relationship", {"elastic_modulus": 20}),
    ],
)
def test_direct_methods_require_arguments(calculate, method, kwargs):
    with pytest.raises(TypeError, match="required positional argument"):
        calculate(method, **kwargs)
