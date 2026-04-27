# graph

Registry-generated parameter dependency graph.

The graph contains measured inputs, calculated targets, merge nodes for multi-input methods, and method edges. It is generated from `methods.default_registry()` so method metadata and graph structure stay synchronized.

## Public Entry Points

```python
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.pathway import find_parameterizations

d11 = default_graph.get_node("D11")
pathways = find_parameterizations(default_graph, d11)
```

`build_graph(registry)` can build an alternate graph for an experimental registry. `default_graph` is the graph used by `ExecutionEngine()` when no graph is passed.

## Important Files

- `structures.py`: `Node`, `Edge`, `Graph`, and `GraphBuilder`.
- `build.py`: converts method specs into measured nodes, target nodes, merge nodes, and method edges.
- `parameter_graph.py`: default graph exports and convenience node aliases.

## Node Types

- Parameter nodes represent measured inputs or calculated outputs.
- Merge nodes represent required input combinations for methods with more than one source.

Measured inputs currently include density, hand hardness, grain form, grain size, layer thickness, and slope angle. Calculated layer targets are density, elastic modulus, Poisson's ratio, and shear modulus. Calculated slab targets are `A11`, `B11`, `D11`, `A55`, `slab_weight`, `slab_weight_shear`, and `slab_weight_shear_with_elasticity`.

## Merge Names

Merge node names are derived from method `source_nodes`. For example:

- `("density", "measured_grain_form")` -> `merge_density_grain_form`
- `("measured_layer_thickness", "elastic_modulus", "poissons_ratio")` -> `merge_layer_thickness_elastic_modulus_poissons_ratio`
- `("slab_weight_shear", "elastic_modulus", "poissons_ratio")` -> `merge_slab_weight_shear_elastic_modulus_poissons_ratio`

Researchers usually should not add merge nodes directly. Add a `MethodSpec`; graph construction will create the needed merge.

## Adding Graph Pathways

Add or update graph pathways by editing the registry, not this package:

1. Implement the formula in `methods/layer` or `methods/slab`.
2. Add a `MethodSpec` in `methods/registry.py`.
3. Set `source_nodes` to the graph inputs required by the method.
4. Set `required_inputs` to the runtime values the dispatcher must read from `Layer` or `Slab`.
5. Add tests for registry-to-graph consistency and expected pathway counts.

After that, `build_graph()` creates the graph edge and `find_parameterizations()` discovers the affected pathways.
