"""Registry of calculation methods available to the framework."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

from snowpyt_mechparams.methods.layer import (
    calculate_density,
    calculate_elastic_modulus,
    calculate_poissons_ratio,
    calculate_shear_modulus,
)
from snowpyt_mechparams.methods.slab import (
    calculate_A11,
    calculate_A55,
    calculate_B11,
    calculate_D11,
)
from snowpyt_mechparams.methods.slab.coverage import (
    calculate_slab_weight,
    calculate_slab_weight_shear,
    calculate_slab_weight_shear_with_elasticity,
)
from snowpyt_mechparams.methods.specs import MethodSpec, ParameterLevel


class MethodRegistry:
    """Container and lookup API for method specifications."""

    def __init__(self, specs: Iterable[MethodSpec] = ()) -> None:
        self._specs: Dict[Tuple[str, str], MethodSpec] = {}
        self._by_target: Dict[str, List[MethodSpec]] = defaultdict(list)
        for spec in specs:
            self.register(spec)

    def register(self, spec: MethodSpec) -> None:
        """Register a method specification."""
        key = (spec.target, spec.method_name)
        if key in self._specs:
            raise ValueError(f"Duplicate method specification: {key}")
        self._specs[key] = spec
        self._by_target[spec.target].append(spec)

    def get(self, target: str, method_name: str) -> Optional[MethodSpec]:
        """Return a method specification by target and method name."""
        return self._specs.get((target, method_name))

    def require(self, target: str, method_name: str) -> MethodSpec:
        """Return a method specification, raising for unknown methods."""
        spec = self.get(target, method_name)
        if spec is None:
            raise KeyError(f"Unknown method: {target}.{method_name}")
        return spec

    def methods_for(self, target: str) -> List[MethodSpec]:
        """Return all method specs registered for a target parameter."""
        return list(self._by_target.get(target, ()))

    def default_method_for(self, target: str) -> Optional[MethodSpec]:
        """Return the only method for a target, or the first registered method."""
        methods = self.methods_for(target)
        return methods[0] if methods else None

    def all(self) -> List[MethodSpec]:
        """Return all method specs in registration order."""
        return list(self._specs.values())

    def targets_by_level(self, level: ParameterLevel) -> frozenset[str]:
        """Return target names with at least one method at the given level."""
        return frozenset(
            spec.target for spec in self._specs.values() if spec.level == level
        )

    def as_method_dict(self) -> Dict[str, List[str]]:
        """Return registered method names grouped by target."""
        return {
            target: [spec.method_name for spec in specs]
            for target, specs in self._by_target.items()
        }


def default_registry() -> MethodRegistry:
    """Build the default SnowPyt-MechParams method registry."""
    return MethodRegistry(_default_specs())


def _default_specs() -> List[MethodSpec]:
    """Return all built-in method specifications."""
    layer = ParameterLevel.LAYER
    slab = ParameterLevel.SLAB
    return [
        MethodSpec(
            target="density",
            method_name="data_flow",
            level=layer,
            source_nodes=("measured_density",),
            required_inputs=("density_measured",),
            function=lambda density_measured: density_measured,
            output_attr="density_calculated",
            cache_scope="layer",
            description="Use directly measured density.",
        ),
        MethodSpec(
            target="density",
            method_name="geldsetzer",
            level=layer,
            source_nodes=("measured_hand_hardness", "measured_grain_form"),
            required_inputs=("hand_hardness_index", "grain_form"),
            function=lambda hand_hardness_index, grain_form, include_method_uncertainty=True: calculate_density(
                "geldsetzer",
                hand_hardness_index=hand_hardness_index,
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="density_calculated",
            cache_scope="layer",
            citation="Geldsetzer and Jamieson",
        ),
        MethodSpec(
            target="density",
            method_name="kim_jamieson_table2",
            level=layer,
            source_nodes=("measured_hand_hardness", "measured_grain_form"),
            required_inputs=("hand_hardness_index", "grain_form"),
            function=lambda hand_hardness_index, grain_form, include_method_uncertainty=True: calculate_density(
                "kim_jamieson_table2",
                hand_hardness_index=hand_hardness_index,
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="density_calculated",
            cache_scope="layer",
            citation="Kim and Jamieson",
        ),
        MethodSpec(
            target="density",
            method_name="kim_jamieson_table5",
            level=layer,
            source_nodes=(
                "measured_hand_hardness",
                "measured_grain_form",
                "measured_grain_size",
            ),
            required_inputs=("hand_hardness_index", "grain_form", "grain_size"),
            function=lambda hand_hardness_index, grain_form, grain_size, include_method_uncertainty=True: calculate_density(
                "kim_jamieson_table5",
                hand_hardness_index=hand_hardness_index,
                grain_form=grain_form,
                grain_size=grain_size,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="density_calculated",
            cache_scope="layer",
            citation="Kim and Jamieson",
        ),
        MethodSpec(
            target="elastic_modulus",
            method_name="bergfeld",
            level=layer,
            source_nodes=("density", "measured_grain_form"),
            required_inputs=("density", "grain_form"),
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "bergfeld",
                density=density,
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="elastic_modulus",
            citation="bergfeld",
        ),
        MethodSpec(
            target="elastic_modulus",
            method_name="kochle",
            level=layer,
            source_nodes=("density", "measured_grain_form"),
            required_inputs=("density", "grain_form"),
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "kochle",
                density=density,
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="elastic_modulus",
            citation="kochle",
        ),
        MethodSpec(
            target="elastic_modulus",
            method_name="wautier",
            level=layer,
            source_nodes=("density", "measured_grain_form"),
            required_inputs=("density", "grain_form"),
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "wautier",
                density=density,
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="elastic_modulus",
            citation="wautier",
        ),
        MethodSpec(
            target="elastic_modulus",
            method_name="schottner",
            level=layer,
            source_nodes=("density", "measured_grain_form"),
            required_inputs=("density", "grain_form"),
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "schottner",
                density=density,
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="elastic_modulus",
            citation="schottner",
        ),
        MethodSpec(
            target="poissons_ratio",
            method_name="kochle",
            level=layer,
            source_nodes=("measured_grain_form",),
            required_inputs=("grain_form",),
            function=lambda grain_form, include_method_uncertainty=True: calculate_poissons_ratio(
                "kochle",
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="poissons_ratio",
            citation="Kochle and Schneebeli",
        ),
        MethodSpec(
            target="poissons_ratio",
            method_name="srivastava",
            level=layer,
            source_nodes=("density", "measured_grain_form"),
            required_inputs=("density", "grain_form"),
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_poissons_ratio(
                "srivastava",
                density=density,
                grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="poissons_ratio",
            citation="Srivastava",
        ),
        MethodSpec(
            target="shear_modulus",
            method_name="lame_relationship",
            level=layer,
            source_nodes=("elastic_modulus", "poissons_ratio"),
            required_inputs=("elastic_modulus", "poissons_ratio"),
            function=lambda elastic_modulus, poissons_ratio, include_method_uncertainty=True: calculate_shear_modulus(
                "lame_relationship",
                elastic_modulus=elastic_modulus,
                poissons_ratio=poissons_ratio,
                include_method_uncertainty=include_method_uncertainty,
            ),
            output_attr="shear_modulus",
            description="Isotropic Lame relationship.",
        ),
        MethodSpec(
            target="slab_weight",
            method_name="sum_layer_weight",
            level=slab,
            source_nodes=("density", "measured_layer_thickness"),
            required_inputs=("slab",),
            function=calculate_slab_weight,
            output_attr="slab_weight",
            description="Integrate computed density through slab thickness.",
        ),
        MethodSpec(
            target="slab_weight_shear",
            method_name="slope_parallel_component",
            level=slab,
            source_nodes=("slab_weight", "measured_slope_angle"),
            required_inputs=("slab",),
            function=calculate_slab_weight_shear,
            output_attr="slab_weight_shear",
            description="Project slab weight parallel to slope angle.",
        ),
        MethodSpec(
            target="slab_weight_shear_with_elasticity",
            method_name="combine_shear_weight_and_elasticity",
            level=slab,
            source_nodes=("slab_weight_shear", "elastic_modulus", "poissons_ratio"),
            required_inputs=("slab",),
            function=calculate_slab_weight_shear_with_elasticity,
            output_attr="slab_weight_shear_with_elasticity",
            description="Coverage target requiring W_s, E, and nu.",
        ),
        MethodSpec(
            target="A11",
            method_name="weissgraeber_rosendahl",
            level=slab,
            source_nodes=(
                "measured_layer_thickness",
                "elastic_modulus",
                "poissons_ratio",
            ),
            required_inputs=("slab",),
            function=lambda slab: calculate_A11("weissgraeber_rosendahl", slab=slab),
            output_attr="A11",
            citation="Weissgraeber and Rosendahl",
        ),
        MethodSpec(
            target="B11",
            method_name="weissgraeber_rosendahl",
            level=slab,
            source_nodes=(
                "measured_layer_thickness",
                "elastic_modulus",
                "poissons_ratio",
            ),
            required_inputs=("slab",),
            function=lambda slab: calculate_B11("weissgraeber_rosendahl", slab=slab),
            output_attr="B11",
            citation="Weissgraeber and Rosendahl",
        ),
        MethodSpec(
            target="D11",
            method_name="weissgraeber_rosendahl",
            level=slab,
            source_nodes=(
                "measured_layer_thickness",
                "elastic_modulus",
                "poissons_ratio",
            ),
            required_inputs=("slab",),
            function=lambda slab: calculate_D11("weissgraeber_rosendahl", slab=slab),
            output_attr="D11",
            citation="Weissgraeber and Rosendahl",
        ),
        MethodSpec(
            target="A55",
            method_name="weissgraeber_rosendahl",
            level=slab,
            source_nodes=("measured_layer_thickness", "shear_modulus"),
            required_inputs=("slab",),
            function=lambda slab: calculate_A55("weissgraeber_rosendahl", slab=slab),
            output_attr="A55",
            citation="Weissgraeber and Rosendahl",
        ),
    ]
