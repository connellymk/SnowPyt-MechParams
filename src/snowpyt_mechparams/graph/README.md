# Parameter Graph Module

The `snowpyt_mechparams.graph` module defines the dependency graph used to
discover calculation pathways for layer-level and slab-level snow mechanical
parameters.

The graph is declarative: nodes describe quantities, edges describe data flow or
calculation methods, and the algorithm module walks the graph to enumerate every
valid pathway from measured snow-pit inputs to a requested target.

## Files

```text
graph/
├── __init__.py          # Public exports for graph classes, graph, and key nodes
├── structures.py        # Node, Edge, Graph, and GraphBuilder
├── parameter_graph.py   # The complete SnowPyt-MechParams parameter graph
└── README.md            # This file
```

## Core Concepts

### Nodes

The graph has two node types:

- `parameter` nodes represent measured inputs or calculated outputs.
- `merge` nodes collect multiple required inputs before a method edge.

Calculated parameter nodes are also tagged with a level:

- `layer`: values computed independently for each `Layer`
- `slab`: values computed once for a whole `Slab`
- `None`: root, measured-input, layer-property, and merge nodes

The current layer targets are:

```python
graph.layer_params == frozenset({
    "density",
    "elastic_modulus",
    "poissons_ratio",
    "shear_modulus",
})
```

The current slab targets are:

```python
graph.slab_params == frozenset({
    "A11",
    "B11",
    "D11",
    "A55",
    "slab_weight",
    "slab_weight_shear",
    "slab_weight_shear_with_elasticity",
})
```

### Edges

The graph has two edge types:

- Data-flow edges have `method_name is None` and pass values forward without a
  calculation. Examples include `snow_pit -> measured_density` and
  `measured_density -> density`.
- Method edges have a `method_name` and correspond to dispatcher registrations,
  such as `bergfeld`, `lame_relationship`, or `weissgraeber_rosendahl`.

`find_parameterizations()` reports data-flow edges as `"data_flow"` in pathway
descriptions even though the graph edge itself stores `None`.

## Current Graph

### Measured Inputs

All measured-input nodes flow from the root `snow_pit` node:

```text
snow_pit
├── measured_density
├── measured_hand_hardness
├── measured_grain_form
├── measured_grain_size
├── measured_layer_thickness
└── measured_slope_angle
```

`measured_layer_thickness` represents `Layer.thickness`; it is a measured layer
property, not a calculated method.

`measured_slope_angle` represents `Slab.angle` and is used by the slab-weight
shear target.

### Layer Parameters

```text
measured_density ----------------------------------------------> density

measured_hand_hardness --> merge_hand_hardness_grain_form -----> density
measured_grain_form ----/        | geldsetzer
                                 | kim_jamieson_table2

merge_hand_hardness_grain_form --> merge_hand_hardness_grain_form_grain_size
measured_grain_size ------------/        | kim_jamieson_table5
                                         v
                                      density

density + measured_grain_form --> merge_density_grain_form --> elastic_modulus
                                                             --> poissons_ratio

measured_grain_form -------------------------------------------> poissons_ratio

elastic_modulus + poissons_ratio --> merge_elastic_modulus_poissons_ratio
                                      -> shear_modulus
```

Available layer methods:

| Target | Method | Inputs |
| --- | --- | --- |
| `density` | `data_flow` | measured density |
| `density` | `geldsetzer` | hand hardness, grain form |
| `density` | `kim_jamieson_table2` | hand hardness, grain form |
| `density` | `kim_jamieson_table5` | hand hardness, grain form, grain size |
| `elastic_modulus` | `bergfeld` | density, grain form |
| `elastic_modulus` | `kochle` | density, grain form |
| `elastic_modulus` | `wautier` | density, grain form |
| `elastic_modulus` | `schottner` | density, grain form |
| `poissons_ratio` | `kochle` | grain form |
| `poissons_ratio` | `srivastava` | density, grain form |
| `shear_modulus` | `lame_relationship` | elastic modulus, Poisson's ratio |

The shear-modulus method uses the isotropic Lame relationship:

```text
G = E / (2 * (1 + nu))
```

### Slab Stiffness Parameters

```text
elastic_modulus + poissons_ratio --> merge_E_nu

measured_layer_thickness + merge_E_nu --> merge_hi_E_nu --> A11
                                                        --> B11
                                                        --> D11

measured_layer_thickness + shear_modulus --> merge_hi_G --> A55
```

Available slab stiffness methods:

| Target | Method | Required per-layer values |
| --- | --- | --- |
| `A11` | `weissgraeber_rosendahl` | thickness, elastic modulus, Poisson's ratio |
| `B11` | `weissgraeber_rosendahl` | thickness, elastic modulus, Poisson's ratio |
| `D11` | `weissgraeber_rosendahl` | thickness, elastic modulus, Poisson's ratio |
| `A55` | `weissgraeber_rosendahl` | thickness, shear modulus |

The stiffness methods use the Weißgraeber and Rosendahl (2023) layered-slab
formulation. `A11`, `B11`, and `D11` consume the same `merge_hi_E_nu` input
combination; `A55` consumes `merge_hi_G`.

### Slab-Weight Coverage Targets

The graph also includes slab-weight targets used for coverage analyses:

```text
density + measured_layer_thickness
    -> merge_slab_weight_inputs
    -> slab_weight

slab_weight + measured_slope_angle
    -> merge_slab_weight_slope_angle
    -> slab_weight_shear

slab_weight_shear + elastic_modulus + poissons_ratio
    -> merge_slab_weight_shear_elasticity
    -> slab_weight_shear_with_elasticity
```

Available slab-weight methods:

| Target | Method | Meaning |
| --- | --- | --- |
| `slab_weight` | `sum_layer_weight` | Integrates layer density through layer thickness |
| `slab_weight_shear` | `slope_parallel_component` | Projects slab weight by slope angle |
| `slab_weight_shear_with_elasticity` | `combine_shear_weight_and_elasticity` | Returns `slab_weight_shear` only when elastic modulus and Poisson's ratio are also available on all layers |

`slab_weight_shear_with_elasticity` does not change the numerical value of
`slab_weight_shear`; it is a coverage target that records when density,
thickness, slope angle, elastic modulus, and Poisson's ratio are all available
for the selected pathway.

Roch and WEAC stability criteria are not represented directly as graph targets.
They remain available as direct stability-criteria functions for analyses that
provide the required weak-layer inputs explicitly.

## Pathway Counts

The current graph has 28 nodes and 45 edges. With deduplication in
`find_parameterizations()`, the current target counts are:

| Target | Unique pathways |
| --- | ---: |
| `density` | 4 |
| `elastic_modulus` | 16 |
| `poissons_ratio` | 5 |
| `shear_modulus` | 32 |
| `A11` | 32 |
| `B11` | 32 |
| `D11` | 32 |
| `A55` | 32 |
| `slab_weight` | 4 |
| `slab_weight_shear` | 4 |
| `slab_weight_shear_with_elasticity` | 32 |

The 32-pathway targets come from:

```text
4 density methods * 4 elastic-modulus methods * 2 Poisson's-ratio methods
```

The `density` node is shared by elastic modulus and by the Srivastava Poisson's
ratio method. That means a pathway using Srivastava cannot choose a separate
density method for Poisson's ratio; the method fingerprinting step in
`find_parameterizations()` deduplicates structurally different traversals that
resolve to the same method combination.

## Public API

Most users should import from `snowpyt_mechparams.graph`:

```python
from snowpyt_mechparams.graph import graph, D11, GraphBuilder

d11_node = graph.get_node("D11")
assert d11_node is D11
```

The package exports the graph classes and commonly used graph nodes:

- `Node`, `Edge`, `Graph`, `GraphBuilder`, `NodeType`
- `graph`
- root and measured nodes, such as `snow_pit`, `measured_density`,
  `measured_layer_thickness`, and `measured_slope_angle`
- layer targets, such as `density` and `elastic_modulus`
- slab targets, such as `D11`, `A55`, and `slab_weight_shear`
- slab-weight merge nodes

The complete graph definition in `parameter_graph.py` also defines
`LAYER_PARAMS` and `SLAB_PARAMS`, but `graph.layer_params` and
`graph.slab_params` are the preferred level-derived accessors.

## Using the Graph

### Find Calculation Pathways

```python
from snowpyt_mechparams.algorithm import find_parameterizations
from snowpyt_mechparams.graph import graph

target = graph.get_node("D11")
pathways = find_parameterizations(graph, target)

print(len(pathways))  # 32
```

### Inspect Incoming Methods

```python
from snowpyt_mechparams.graph import graph

density_node = graph.get_node("density")

for edge in density_node.incoming_edges:
    method = edge.method_name or "data_flow"
    print(edge.start.parameter, "->", method, "->", edge.end.parameter)
```

### Inspect Dependencies for a Merge Node

```python
from snowpyt_mechparams.graph import graph

merge = graph.get_node("merge_slab_weight_shear_elasticity")
inputs = sorted(edge.start.parameter for edge in merge.incoming_edges)

print(inputs)
# ["elastic_modulus", "poissons_ratio", "slab_weight_shear"]
```

## Data Structures

`structures.py` provides the small graph model used by `parameter_graph.py` and
the pathfinding algorithm:

- `Node`: hashable by `(type, parameter)` and stores incoming/outgoing edges
- `Edge`: directed connection with an optional `method_name`; creating an edge
  updates the connected nodes
- `Graph`: stores nodes and edges, validates edge endpoints, and provides
  `get_node()`, `layer_params`, and `slab_params`
- `GraphBuilder`: convenience API for creating parameter nodes, merge nodes,
  data-flow edges, and method edges

Example:

```python
from snowpyt_mechparams.graph import GraphBuilder

builder = GraphBuilder()
snow_pit = builder.param("snow_pit")
density = builder.param("density", level="layer")

builder.flow(snow_pit, density)
custom_graph = builder.build()
```

## Adding a Method

To add a new calculation method:

1. Implement the calculation in the appropriate `layer_parameters/` or
   `slab_parameters/` module.
2. Register the method in `execution/dispatcher.py` with a `MethodSpec`.
3. Add the corresponding method edge in `graph/parameter_graph.py`.
4. Add or update tests so graph edges and dispatcher registrations stay in sync.

Example graph update for a new elastic-modulus method that uses density and
grain form:

```python
build_graph.method_edge(merge_d_gf, elastic_modulus, "new_method")
```

Example dispatcher registration:

```python
self._register(MethodSpec(
    parameter="elastic_modulus",
    method_name="new_method",
    level=ParameterLevel.LAYER,
    function=lambda density, grain_form: calculate_elastic_modulus(
        "new_method",
        density=density,
        grain_form=grain_form,
    ),
    required_inputs=["density", "grain_form"],
    optional_inputs={},
))
```

If a method needs a new input combination, create a new merge node and connect
all required inputs to it before adding the method edge.

## Related Documentation

- `docs/code_description.md`: package-level description of the graph and
  parameterization algorithm
- `docs/execution_engine.md`: execution behavior, dispatcher methods, and
  target handling
- `tests/test_graph.py`: structural tests for graph nodes, merge nodes, exports,
  and dispatcher consistency

## References

- Bergfeld, B., van Herwijnen, A., Bobillier, G., Larose, E., & Gaume, J.
  (2023). Temporal evolution of crack propagation propensity in snow.
  The Cryosphere, 17(5), 1487-1502. https://doi.org/10.5194/tc-17-1487-2023
- Kim, H., & Jamieson, J. B. (2010). Multivariate characterization of avalanche
  weak layers. Cold Regions Science and Technology, 60(3), 202-213.
  https://doi.org/10.1016/j.coldregions.2009.11.001
- Koechle, B., & Schneebeli, M. (2014). Three-dimensional microstructure and
  numerical calculation of elastic properties of alpine snow with a focus on
  weak layers. Journal of Glaciology, 60(222), 705-713.
  https://doi.org/10.3189/2014JoG13J220
- Schöttner, L., Hagenmuller, P., & Proksch, M. (2024). A micromechanical
  finite element model for density and microstructure evolution during dry snow
  metamorphism. The Cryosphere, 18(4), 1579-1600.
  https://doi.org/10.5194/tc-18-1579-2024
- Srivastava, P. K., Mahajan, P., Satyawali, P. K., & Kumar, V. (2016).
  Observation of temperature gradient metamorphism in snow by X-ray computed
  microtomography. Cold Regions Science and Technology, 125, 63-70.
  https://doi.org/10.1016/j.coldregions.2016.01.010
- Wautier, A., Geindreau, C., & Flin, F. (2015). Linking snow microstructure to
  its macroscopic elastic stiffness tensor: A numerical homogenization method
  and its application to 3-D images from X-ray tomography. Geophysical Research
  Letters, 42(19), 8031-8041. https://doi.org/10.1002/2015GL065227
- Weissgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for layered
  snow slabs. The Cryosphere, 17(4), 1475-1496.
  https://doi.org/10.5194/tc-17-1475-2023
