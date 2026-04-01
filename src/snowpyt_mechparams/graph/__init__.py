"""
Parameter graph module for SnowPyt-MechParams.

This module defines the directed graph of all available calculation methods
for snow mechanical parameters at both layer and slab levels.

The graph represents:
- **Parameter nodes**: Measured or calculated parameters
- **Merge nodes**: Combinations of inputs required for methods
- **Edges**: Calculation methods or data flow connections

The graph is used by the execution engine to find all possible calculation
pathways from measured inputs to target parameters.

Quick Start
-----------
>>> from snowpyt_mechparams.graph import graph
>>> from snowpyt_mechparams.algorithm import find_parameterizations
>>>
>>> # Find all ways to calculate D11
>>> D11_node = graph.get_node("D11")
>>> parameterizations = find_parameterizations(graph, D11_node)
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
- zi: Represents spatial/thickness information for layers
- merge_E_nu: Combines E and ν from all layers (for plane-strain modulus)
- merge_zi_E_nu: Combines spatial info with E/ν (for D11 bending calculation)
- merge_hi_G: Combines thickness with shear modulus (for A55)
- merge_hi_E_nu: Combines thickness with E/ν (for A11, B11)

See Also
--------
graph.parameter_graph : The complete graph definition
graph.structures : Graph data structures (Node, Edge, Graph)
algorithm : Functions to find calculation pathways
"""

from snowpyt_mechparams.graph.structures import (
    Node,
    Edge,
    Graph,
    GraphBuilder,
    NodeType,
)

from snowpyt_mechparams.graph.parameter_graph import (
    graph,
    # Root
    snow_pit,
    # Measured parameters
    measured_density,
    measured_hand_hardness,
    measured_grain_form,
    measured_grain_size,
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
    # Weak-layer placeholder and stability criterion targets
    weak_layer_info,
    slab_elasticity_parameters,
    g_delta,
    s_r,
    # Merge nodes
    merge_weac_inputs,
    merge_roch_inputs,
    # Parameter classification sets
    WEAK_LAYER_PARAMS,
    STABILITY_PARAMS,
)

from snowpyt_mechparams.graph.visualize import (
    generate_mermaid_diagram,
    save_mermaid_diagram,
    print_mermaid_diagram,
    generate_mermaid_overview,
    generate_mermaid_layer_detail,
    generate_mermaid_slab_detail,
    generate_mermaid_stability_detail,
    save_mermaid_overview,
    save_mermaid_layer_detail,
    save_mermaid_slab_detail,
    save_mermaid_stability_detail,
    generate_mermaid_full_detail,
    save_mermaid_full_detail,
)

__all__ = [
    # Classes
    "Node",
    "Edge",
    "Graph",
    "GraphBuilder",
    "NodeType",
    # Graph instance
    "graph",
    # Root
    "snow_pit",
    # Measured parameters
    "measured_density",
    "measured_hand_hardness",
    "measured_grain_form",
    "measured_grain_size",
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
    # Weak-layer placeholder and stability criterion targets
    "weak_layer_info",
    "slab_elasticity_parameters",
    "g_delta",
    "s_r",
    # Merge nodes
    "merge_weac_inputs",
    "merge_roch_inputs",
    # Parameter classification sets
    "WEAK_LAYER_PARAMS",
    "STABILITY_PARAMS",
    # Visualization — full graph (backwards compat)
    "generate_mermaid_diagram",
    "save_mermaid_diagram",
    "print_mermaid_diagram",
    # Visualization — focused diagrams
    "generate_mermaid_overview",
    "generate_mermaid_layer_detail",
    "generate_mermaid_slab_detail",
    "generate_mermaid_stability_detail",
    "save_mermaid_overview",
    "save_mermaid_layer_detail",
    "save_mermaid_slab_detail",
    "save_mermaid_stability_detail",
    "generate_mermaid_full_detail",
    "save_mermaid_full_detail",
]
