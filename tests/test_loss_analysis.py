"""Independent method-domain checks and loss-accounting regression scenarios."""

import sys
from pathlib import Path

import numpy as np
import pytest
from uncertainties import ufloat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paper_analysis"))
from loss_analysis_utils import (  # noqa: E402
    DENSITY_RANGES,
    GRAIN_DOMAINS,
    HARDNESS_RANGES,
    Issue,
    analyze_losses,
    diagnose_layer,
    failure_category,
    finite,
    plot_histogram,
)
from snowpyt_mechparams.constants import HARDNESS_MAPPING  # noqa: E402
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher  # noqa: E402
from snowpyt_mechparams.models import Layer, Slab  # noqa: E402


def test_absent_and_unsupported_grain_forms_are_distinct():
    missing = diagnose_layer(Layer(hand_hardness="1F"), "density", "geldsetzer")
    unsupported = diagnose_layer(
        Layer(grain_form="MF", hand_hardness="1F"), "density", "geldsetzer"
    )
    assert {i.category for i in missing} == {"missing"}
    assert {i.category for i in unsupported} == {"validity"}
    assert unsupported[0].grain_form == "MF"
    assert unsupported[0].resolved_grain_form == ""


@pytest.mark.parametrize("method", list(HARDNESS_RANGES))
def test_density_domains_match_dispatcher_for_every_grain_and_hardness(method):
    """Check actual methods at all recorded HH values, including both bounds."""
    grains = set(HARDNESS_RANGES[method]) | {"RGwp", "RGxf", "FCxr", "MFcr", "SH", "IF"}
    dispatcher = MethodDispatcher()
    for grain in grains:
        for hardness in HARDNESS_MAPPING:
            layer = Layer(
                grain_form=grain,
                hand_hardness=hardness,
                grain_size_avg=ufloat(0.5, 0.1),
            )
            output, error = dispatcher.execute(
                "density", method, layer=layer, include_method_uncertainty=False
            )
            issues = diagnose_layer(
                layer, "density", method, output=output, error=error
            )
            assert finite(output) == (not issues), (method, grain, hardness, issues)
            assert not any(i.category == "other" for i in issues)


def test_density_subclasses_resolve_without_losing_original_code():
    layer = Layer(grain_form="RGxf", hand_hardness="F-")
    issues = diagnose_layer(layer, "density", "geldsetzer")
    assert len(issues) == 1
    assert issues[0].field == "hand_hardness_index"
    assert issues[0].grain_form == "RGxf"
    assert issues[0].resolved_grain_form == "RG"
    assert issues[0].lower == 1.0


@pytest.mark.parametrize("method", list(DENSITY_RANGES))
def test_elastic_density_boundaries_match_actual_method(method):
    low, high = DENSITY_RANGES[method]
    dispatcher = MethodDispatcher()
    for density in [low - 0.001, low, low + 0.001, high - 0.001, high, high + 0.001]:
        layer = Layer(grain_form="RG", density_calculated=ufloat(density, 1))
        output, error = dispatcher.execute(
            "elastic_modulus", method, layer=layer, include_method_uncertainty=False
        )
        issues = diagnose_layer(
            layer,
            "elastic_modulus",
            method,
            density=layer.density_calculated,
            output=output,
            error=error,
        )
        assert finite(output) == (not issues)
        assert not any(i.category == "other" for i in issues)


@pytest.mark.parametrize("grain", ["RG", "FC", "PP"])
def test_srivastava_density_bounds_and_unbounded_non_rg(grain):
    dispatcher = MethodDispatcher()
    for density in [199.999, 200, 200.001, 580, 580.001, 1000]:
        layer = Layer(grain_form=grain, density_calculated=ufloat(density, 1))
        output, error = dispatcher.execute(
            "poissons_ratio",
            "srivastava",
            layer=layer,
            include_method_uncertainty=False,
        )
        issues = diagnose_layer(
            layer,
            "poissons_ratio",
            "srivastava",
            density=layer.density_calculated,
            output=output,
            error=error,
        )
        assert finite(output) == (not issues)
        assert not any(i.category == "other" for i in issues)


@pytest.mark.parametrize("parameter,method", list(GRAIN_DOMAINS))
def test_elastic_grain_domains_match_actual_methods(parameter, method):
    dispatcher = MethodDispatcher()
    for grain in ["PP", "DF", "RGwp", "FCxr", "DH", "SH", "MFcr", "IF"]:
        layer = Layer(grain_form=grain, density_calculated=ufloat(250, 1))
        output, error = dispatcher.execute(
            parameter, method, layer=layer, include_method_uncertainty=False
        )
        issues = diagnose_layer(
            layer,
            parameter,
            method,
            density=layer.density_calculated,
            output=output,
            error=error,
        )
        assert finite(output) == (not issues), (parameter, method, grain, issues)
        assert not any(i.category == "other" for i in issues)


def test_all_evaluable_causes_and_blocking_are_preserved():
    layer = Layer(grain_form="IF")
    density_issues = diagnose_layer(layer, "density", "kim_jamieson_table6")
    assert {i.field for i in density_issues} == {
        "grain_form",
        "hand_hardness",
        "grain_size",
    }
    assert failure_category(density_issues) == "mixed"
    downstream = diagnose_layer(layer, "elastic_modulus", "bergfeld")
    assert {i.category for i in downstream} == {"blocked", "validity"}
    assert not any(i.category == "missing" for i in downstream)
    # When density exists, both independently violated constraints are reported.
    observed = diagnose_layer(layer, "elastic_modulus", "bergfeld", density=500)
    assert {i.field for i in observed} == {"grain_form", "density"}
    assert {i.category for i in observed} == {"validity"}


def test_unrecognized_hardness_is_not_missing_or_a_published_range():
    issues = diagnose_layer(
        Layer(grain_form="RG", hand_hardness="unknown"), "density", "geldsetzer"
    )
    assert {i.category for i in issues} == {"other"}
    assert issues[0].observed == "unknown"


def _slab(layer, index, angle=30):
    return Slab(layers=[layer], angle=angle, slab_id=f"slab_{index}", pit_id="pit")


@pytest.mark.parametrize("target", ["D11", "slab_weight_shear_with_elasticity"])
def test_shared_branches_and_layers_are_deduplicated_and_funnels_reconcile(target):
    source = Layer(
        depth_top=0, thickness=10, grain_form="RG", density_measured=ufloat(250, 25)
    )
    slabs = [_slab(source, 0), _slab(source, 1)]
    result = analyze_losses(slabs, target, progress=False)
    assert len(result.attempts) == 64
    rows = result.method_summary
    missing = rows[
        (rows.parameter == "density")
        & (rows.method == "geldsetzer")
        & (rows.category == "missing")
    ].iloc[0]
    assert missing.slabs == 2 and missing.layers == 1
    emod = rows[
        (rows.parameter == "elastic_modulus")
        & (rows.method == "bergfeld")
        & (rows.density_context == "geldsetzer")
        & (rows.category == "blocked")
    ].iloc[0]
    assert emod.slabs == 2 and emod.layers == 1
    assert not result.attempts.loc[
        result.attempts.density_method != "data_flow", "success"
    ].any()
    assert result.attempts.loc[
        result.attempts.density_method == "data_flow", "success"
    ].any()
    assert result.histogram.sum() == 2
    assert len(result.histogram) == 33
    assert (result.stages.newly_lost.sum() + result.attempts.success.sum()) == 64


def test_zero_weight_and_nonfinite_slope_and_mixed_loss():
    valid = Layer(
        depth_top=0,
        thickness=10,
        grain_form="RG",
        hand_hardness="1F",
        density_measured=ufloat(250, 25),
        grain_size_avg=ufloat(0.5, 0.1),
    )
    invalid = Layer(depth_top=0, thickness=10, grain_form="IF")
    slabs = [_slab(valid, 0, angle=0), _slab(valid, 1, angle=np.nan), _slab(invalid, 2)]
    result = analyze_losses(slabs, "slab_weight_shear", progress=False)
    assert result.attempts[result.attempts.slab_index == 0].success.sum() == 3
    assert (
        result.attempts.loc[result.attempts.slab_index == 0, "value"]
        .dropna()
        .eq(0)
        .all()
    )
    assert not result.attempts[result.attempts.slab_index == 1].success.any()
    mixed = result.attempts[
        (result.attempts.slab_index == 2)
        & (result.attempts.density_method == "geldsetzer")
    ]
    assert mixed.iloc[0].failure_category == "mixed"
    assert list(result.histogram.index) == list(range(5))
    figure = plot_histogram(result)
    assert len(figure.axes[0].patches) == 5
    assert figure.axes[0].get_ylabel() == "Slab count"
    import matplotlib.pyplot as plt

    plt.close(figure)


def test_missing_geometry_is_observation_loss_and_nonpositive_d11_is_other():
    missing = Layer(depth_top=0, grain_form="RG", density_measured=ufloat(250, 1))
    result = analyze_losses([_slab(missing, 0)], "D11", progress=False)
    assert not result.attempts.success.any()
    assert result.details("geometry").iloc[0].category == "missing"
    zero = Layer(
        depth_top=0, thickness=0, grain_form="RG", density_measured=ufloat(250, 1)
    )
    result = analyze_losses([_slab(zero, 0)], "D11", progress=False)
    direct = result.attempts[result.attempts.density_method == "data_flow"]
    assert set(direct.first_failed_step) == {"D11"}
    assert set(direct.failure_category) == {"other"}


def test_failure_partition_covers_all_cases():
    assert failure_category([Issue("missing", "absent", "hh")]) == "missing_only"
    assert failure_category([Issue("validity", "unsupported", "gf")]) == "validity_only"
    assert (
        failure_category(
            [Issue("missing", "absent", "hh"), Issue("validity", "unsupported", "gf")]
        )
        == "mixed"
    )
    assert failure_category([Issue("other", "error", "output")]) == "other"


@pytest.mark.parametrize("target", ["D11", "slab_weight_shear_with_elasticity"])
def test_heatmap_uses_starting_cohort_not_step_survivors(target):
    """After one of three slabs fails density, another loss is 33%, not 50%."""
    from loss_analysis_utils import plot_loss_heatmap
    import matplotlib.pyplot as plt

    missing = Layer(depth_top=0, thickness=10, grain_form="RG")
    unsupported = Layer(
        depth_top=0, thickness=10, grain_form="IF", density_measured=ufloat(250, 1)
    )
    valid = Layer(
        depth_top=0, thickness=10, grain_form="RG", density_measured=ufloat(250, 1)
    )
    result = analyze_losses(
        [_slab(layer, i) for i, layer in enumerate([missing, unsupported, valid])],
        target,
        progress=False,
    )
    figure = plot_loss_heatmap(result)
    measured = figure.axes[0].images[0].get_array()
    assert measured[0, 0] == pytest.approx(100 / 3)
    emod_step = 1 if target == "D11" else 2
    assert measured[0, emod_step] == pytest.approx(100 / 3)
    assert (
        sum(ax.images[0].get_array().shape[0] for ax in figure.axes if ax.images) == 32
    )
    plt.close(figure)


def test_elastic_shear_matches_weight_without_requiring_depth_and_allows_zero():
    layer = Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1))
    result = analyze_losses(
        [_slab(layer, 0, angle=0)],
        "slab_weight_shear_with_elasticity",
        progress=False,
    )
    direct = result.attempts[result.attempts.density_method == "data_flow"]
    assert direct.success.all()
    assert direct.value.eq(0).all()
    assert result.histogram.loc[8] == 1
    assert "geometry" not in set(result.reasons.parameter)
    figure = plot_histogram(result)
    assert len(figure.axes[0].patches) == 33
    assert "Shear weight with elasticity" in figure.axes[0].get_title()
    import matplotlib.pyplot as plt

    plt.close(figure)


def test_elastic_shear_loses_missing_thickness_or_slope_before_elasticity():
    # PP independently fails Köchle E, but missing geometry is first in the
    # paper's reporting order. Missing thickness must not become "blocked" loss.
    missing_thickness = Layer(grain_form="PP", density_measured=ufloat(250, 1))
    missing_slope = Layer(
        thickness=10, grain_form="PP", density_measured=ufloat(250, 1)
    )
    result = analyze_losses(
        [_slab(missing_thickness, 0), _slab(missing_slope, 1, angle=None)],
        "slab_weight_shear_with_elasticity",
        progress=False,
    )
    direct = result.attempts[result.attempts.density_method == "data_flow"]
    assert set(direct.first_failed_step) == {"slab_weight_shear"}
    assert set(direct.failure_category) == {"missing_only"}
    assert not result.attempts.success.any()
    assert not result.details("elastic_modulus", "kochle").empty
    stages = result.stages[result.stages.pathway == "Measured → Köchle → Köchle"]
    assert stages.surviving.tolist() == [2, 0, 0, 0]


def test_cause_bars_keep_overlapping_grain_and_density_failures_separate():
    """One observed layer can violate two limits; neither bar becomes a sum."""
    from loss_analysis_utils import plot_method_causes, plot_stepwise_losses
    import matplotlib.pyplot as plt

    layer = Layer(
        depth_top=0, thickness=10, grain_form="IF", density_measured=ufloat(500, 1)
    )
    result = analyze_losses([_slab(layer, 0)], "D11", progress=False)
    figure = plot_method_causes(result, "elastic_modulus", "bergfeld", "data_flow")
    bars = figure.axes[0].patches
    assert len(bars) == 2
    assert all(b.get_x() == 0 and b.get_width() == 1 for b in bars)
    labels = [tick.get_text() for tick in figure.axes[0].get_yticklabels()]
    assert any("unsupported grain form" in label for label in labels)
    assert any("363 kg/m³" in label for label in labels)
    plt.close(figure)
    with pytest.raises(ValueError, match="Unknown pathway"):
        plot_stepwise_losses(result, "not a pathway")
