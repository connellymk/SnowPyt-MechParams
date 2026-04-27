# Code Description

This document describes the current SnowPyt-MechParams module structure and the data flow through the registry-driven calculation framework.

## Data Flow

```text
CAAML / SnowPilot data
  -> models.Pit
  -> models.Slab and models.Layer
  -> methods.default_registry()
  -> graph.default_graph
  -> pathway.find_parameterizations()
  -> execution.ExecutionEngine()
  -> result Slab objects with computed values
```

The registry is the single source of truth for methods, dependencies, execution metadata, and graph edges. Researchers should be able to add most new methods by implementing a formula and registering one `MethodSpec`.

## Models

`snowpyt_mechparams.models` contains the domain objects that carry data through the package.

- `Layer` stores field observations for one snow layer: depth, thickness, measured density, hand hardness, grain form, grain size, and calculated layer outputs.
- `WeakLayer` extends `Layer` for the weak layer below a slab.
- `Slab` stores an ordered set of slab layers, slope angle, weak-layer metadata, slab stiffness outputs, slab-weight outputs, and optional stability-criterion results.
- `Pit` converts parsed SnowPilot observations into slabs for downstream analysis.

Model classes should remain lightweight data containers. They expose measured inputs and output slots, while formula logic lives in `methods`.

## Methods

`snowpyt_mechparams.methods` is the extensibility center.

`MethodSpec` records:

- `target`: output parameter name, such as `density` or `D11`.
- `method_name`: method identifier used in pathways and traces.
- `level`: layer or slab.
- `source_nodes`: graph dependencies.
- `required_inputs`: runtime values the dispatcher reads from a `Layer` or `Slab`.
- `function`: callable implementation.
- `output_attr`: model attribute that receives the result.
- `cache_scope`: whether layer-level values may be reused across pathways.
- short metadata such as description or citation.

`MethodRegistry` stores specs and provides lookup APIs used by graph construction, dispatch, and execution planning. `default_registry()` returns the built-in method set.

Formula modules are organized by level:

- `methods/layer`: density, elastic modulus, Poisson's ratio, and shear modulus formulas.
- `methods/slab`: laminate-theory stiffnesses and slab-weight coverage helpers.

## Graph

`snowpyt_mechparams.graph` builds a directed parameter graph from a registry.

- `structures.py` defines `Node`, `Edge`, `Graph`, and `GraphBuilder`.
- `build.py` turns method specs into measured nodes, target nodes, merge nodes, and method edges.
- `parameter_graph.py` exports `default_graph` and common node aliases.

The graph has parameter nodes and merge nodes. Parameter nodes represent measured inputs or calculated outputs. Merge nodes collect multiple inputs needed by a method. For example, a slab stiffness method with `source_nodes=("measured_layer_thickness", "elastic_modulus", "poissons_ratio")` gets a generated merge node named `merge_layer_thickness_elastic_modulus_poissons_ratio`.

Because graph edges are generated from `MethodSpec`, adding a registry entry updates graph search automatically.

## Pathway

`snowpyt_mechparams.pathway` searches the graph for all structural routes from measured inputs to a target node.

- `types.py` defines `PathSegment`, `Branch`, `Parameterization`, and internal `PathTree`.
- `search.py` provides `find_parameterizations(graph, target_node)`.
- `fingerprint.py` deduplicates traversals that have different branch shapes but the same `(parameter, method)` choices.

Pathway search is independent of any real snow pit. It answers "what could be computed from the graph?" Execution answers "does this slab have the measurements needed for that pathway?"

Current expected pathway counts include:

- `density`: 4
- `elastic_modulus`: 16
- `poissons_ratio`: 5
- `shear_modulus`: 32
- `A11`, `B11`, `D11`, `A55`: 32 each
- `slab_weight`: 4
- `slab_weight_shear`: 4
- `slab_weight_shear_with_elasticity`: 32

## Execution

`snowpyt_mechparams.execution` applies parameterizations to real `Slab` objects.

- `ExecutionEngine()` is the public entry point and defaults to `default_graph` and `default_registry()`.
- `PathwayExecutor` executes one `Parameterization`.
- `ExecutionPlanner` derives layer and slab execution order from registry dependencies.
- `MethodDispatcher` consumes registry specs and reads required inputs from model objects.
- `ExecutionContext` isolates pathway-computed layer values and materializes result slabs without mutating the source slab.
- `ComputationCache` caches only values declared cacheable by the registry.

Layer calculations run per layer in dependency order. Slab calculations run only when the requested target is a slab target, and only for the requested target plus any slab-level prerequisites. Pre-existing slab outputs are preserved for layer-only executions.

## Stability Criteria

`snowpyt_mechparams.stability_criteria` exposes direct Roch and WEAC APIs. They are kept outside the parameter graph because they require weak-layer strength or fracture properties that are not generally computable from standard pit observations.

Use the stability criteria after executing the needed layer and slab mechanical properties, or when those inputs are supplied directly.

## Notebook Workflow

Active notebooks should use the current public imports:

```python
from snowpyt_mechparams.execution import ExecutionEngine
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.pathway import find_parameterizations
```

For ordinary execution:

```python
engine = ExecutionEngine()
results = engine.execute_all(slab, "D11")
```

For pathway inspection:

```python
target = default_graph.get_node("slab_weight_shear_with_elasticity")
pathways = find_parameterizations(default_graph, target)
```

Current active notebooks:

- `examples/slab_weight_inputs.ipynb`
- `examples/all_D11_pathways.ipynb`
- `examples/all_density_pathways.ipynb`
- `examples/all_e_mod_pathways.ipynb`
- `examples/all_poissons_ratio_pathways.ipynb`

## Adding A Method

1. Implement the formula in `methods/layer` or `methods/slab`.
2. Register one `MethodSpec` in `methods/registry.py`.
3. Add formula tests and registry/graph consistency tests.
4. Check pathway counts for affected targets.
5. Update package README files and notebooks if the public workflow changes.

Do not hand-wire graph edges or dispatcher tables for normal method additions. The registry should be the only place where method dependency metadata is declared.
