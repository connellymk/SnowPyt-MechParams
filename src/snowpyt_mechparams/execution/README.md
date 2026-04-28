# execution

Runtime layer for applying pathways to `Slab` objects.

- `ExecutionEngine` finds or accepts pathways and executes them for a target.
- `PathwayExecutor` runs one parameterization against a slab.
- `ExecutionPlanner` derives layer and slab execution order from the registry.
- `MethodDispatcher` calls registry specs instead of hard-coded method tables.
- `ExecutionContext` isolates pathway-computed layer values and materializes result slabs without mutating the source slab.
- `ComputationCache` caches only layer-scoped values declared by method specs.

Use `ExecutionEngine()` for normal workflows. It defaults to `graph.default_graph` and `methods.default_registry()`.
