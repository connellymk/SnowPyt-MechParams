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
`layer.thickness`. The node `layer_thickness` represents it in the graph but
requires no calculation - it is direct data flow from measurements.

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
graph.definitions : The complete graph definition
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

from snowpyt_mechparams.graph.definitions import (
    graph,
    # Root
    snow_pit,
    # Measured parameters
    measured_density,
    measured_hand_hardness,
    measured_grain_form,
    measured_grain_size,
    # Layer properties (measured)
    layer_thickness,
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
    "layer_thickness",
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
]
