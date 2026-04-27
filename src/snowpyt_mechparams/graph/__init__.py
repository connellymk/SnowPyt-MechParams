"""
Parameter graph module for SnowPyt-MechParams.

This module defines the directed graph of all available calculation methods
for snow mechanical parameters at both layer and slab levels.

The graph represents:
- **Parameter nodes**: Measured or calculated parameters
- **Merge nodes**: Combinations of inputs required for methods
- **Edges**: Calculation methods or data flow connections

The default graph is generated from the method registry so method metadata,
dependencies, dispatcher registrations, and graph edges share one source of
truth.

Quick Start
-----------
>>> from snowpyt_mechparams.graph import default_graph
>>> from snowpyt_mechparams.pathway import find_parameterizations
>>>
>>> # Find all ways to calculate D11
>>> D11_node = default_graph.get_node("D11")
>>> parameterizations = find_parameterizations(default_graph, D11_node)
>>> print(f"Found {len(parameterizations)} pathways to calculate D11")

Key Concepts
------------
**Layer Properties**: Thickness is already available on Layer objects as
`layer.thickness`. The node `measured_layer_thickness` represents it in the graph
but requires no calculation - it is direct data flow from measurements.

**Slab Parameters**: A11, B11, D11, A55 require ALL layers to have necessary
properties computed. The execution engine handles this by completing all
layer-level calculations before attempting slab-level calculations.

**Merge Nodes**: Special nodes that combine multiple inputs:
- merge_elastic_modulus_poissons_ratio: Combines layer-level E and ν for G
- merge_layer_thickness_elastic_modulus_poissons_ratio: Combines thickness, E, and ν
- merge_layer_thickness_shear_modulus: Combines thickness with shear modulus
- merge_density_layer_thickness: Combines density with thickness for slab weight
- merge_slab_weight_slope_angle: Combines slab weight with slope angle
- merge_slab_weight_shear_elastic_modulus_poissons_ratio: Combines slope-parallel slab weight with E and ν

See Also
--------
graph.build : Registry-to-graph construction
graph.parameter_graph : Default graph exports
graph.structures : Graph data structures (Node, Edge, Graph)
pathway : Functions to find calculation pathways
"""

from snowpyt_mechparams.graph.build import build_graph
from snowpyt_mechparams.graph.structures import (
    Node,
    Edge,
    Graph,
    GraphBuilder,
    NodeType,
)

from snowpyt_mechparams.graph.parameter_graph import (
    default_graph,
    graph,
    registry,
    # Root
    snow_pit,
    # Measured parameters
    measured_density,
    measured_hand_hardness,
    measured_grain_form,
    measured_grain_size,
    measured_slope_angle,
    # Layer properties (measured)
    measured_layer_thickness,
    # Layer parameters (calculated)
    density,
    elastic_modulus,
    poissons_ratio,
    shear_modulus,
    # Slab parameters (calculated)
    A11,
    B11,
    D11,
    A55,
    slab_weight,
    slab_weight_shear,
    slab_weight_shear_with_elasticity,
    # Merge nodes
    merge_slab_weight_inputs,
    merge_slab_weight_slope_angle,
    merge_slab_weight_shear_elasticity,
)

__all__ = [
    # Classes
    "build_graph",
    "Node",
    "Edge",
    "Graph",
    "GraphBuilder",
    "NodeType",
    # Graph instance
    "default_graph",
    "graph",
    "registry",
    # Root
    "snow_pit",
    # Measured parameters
    "measured_density",
    "measured_hand_hardness",
    "measured_grain_form",
    "measured_grain_size",
    "measured_slope_angle",
    # Layer properties (measured)
    "measured_layer_thickness",
    # Layer parameters (calculated)
    "density",
    "elastic_modulus",
    "poissons_ratio",
    "shear_modulus",
    # Slab parameters (calculated)
    "A11",
    "B11",
    "D11",
    "A55",
    "slab_weight",
    "slab_weight_shear",
    "slab_weight_shear_with_elasticity",
    # Merge nodes
    "merge_slab_weight_inputs",
    "merge_slab_weight_slope_angle",
    "merge_slab_weight_shear_elasticity",
]
