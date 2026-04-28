"""Default parameter graph generated from the method registry."""

from __future__ import annotations

from snowpyt_mechparams.graph.build import build_graph
from snowpyt_mechparams.methods import default_registry

registry = default_registry()
default_graph = build_graph(registry)

# Backward-friendly alias. Project docs and notebooks prefer ``default_graph``.
graph = default_graph

LAYER_PARAMS: frozenset[str] = default_graph.layer_params
SLAB_PARAMS: frozenset[str] = default_graph.slab_params

snow_pit = default_graph.get_node("snow_pit")
measured_density = default_graph.get_node("measured_density")
measured_hand_hardness = default_graph.get_node("measured_hand_hardness")
measured_grain_form = default_graph.get_node("measured_grain_form")
measured_grain_size = default_graph.get_node("measured_grain_size")
measured_slope_angle = default_graph.get_node("measured_slope_angle")
measured_layer_thickness = default_graph.get_node("measured_layer_thickness")
measured_layer_location = default_graph.get_node("measured_layer_location")

density = default_graph.get_node("density")
elastic_modulus = default_graph.get_node("elastic_modulus")
poissons_ratio = default_graph.get_node("poissons_ratio")
shear_modulus = default_graph.get_node("shear_modulus")

A11 = default_graph.get_node("A11")
B11 = default_graph.get_node("B11")
D11 = default_graph.get_node("D11")
A55 = default_graph.get_node("A55")
slab_weight = default_graph.get_node("slab_weight")
slab_weight_shear = default_graph.get_node("slab_weight_shear")
slab_weight_shear_with_elasticity = default_graph.get_node(
    "slab_weight_shear_with_elasticity"
)

merge_slab_weight_inputs = default_graph.get_node("merge_density_layer_thickness")
merge_slab_weight_slope_angle = default_graph.get_node("merge_slab_weight_slope_angle")
merge_slab_weight_shear_elasticity = default_graph.get_node(
    "merge_slab_weight_shear_elastic_modulus_poissons_ratio"
)

__all__ = [
    "registry",
    "default_graph",
    "graph",
    "LAYER_PARAMS",
    "SLAB_PARAMS",
    "snow_pit",
    "measured_density",
    "measured_hand_hardness",
    "measured_grain_form",
    "measured_grain_size",
    "measured_slope_angle",
    "measured_layer_thickness",
    "measured_layer_location",
    "density",
    "elastic_modulus",
    "poissons_ratio",
    "shear_modulus",
    "A11",
    "B11",
    "D11",
    "A55",
    "slab_weight",
    "slab_weight_shear",
    "slab_weight_shear_with_elasticity",
    "merge_slab_weight_inputs",
    "merge_slab_weight_slope_angle",
    "merge_slab_weight_shear_elasticity",
]
