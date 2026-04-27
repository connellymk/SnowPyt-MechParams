# methods

Extensibility center for the calculation framework.

`MethodSpec` describes one method: target parameter, method name, layer/slab level, graph source nodes, runtime input names, callable implementation, output attribute, cache scope, and short metadata. `MethodRegistry` stores those specs and is the single source of truth for graph construction and dispatch.

To add a method:

1. Implement the formula in `methods/layer` or `methods/slab`.
2. Add one `MethodSpec` to `registry.py`.
3. Include the target, method name, source nodes, required inputs, output attribute, and callable.
4. Add tests for the formula and registry/graph consistency.

After a spec is registered, `graph.build_graph()` creates the corresponding nodes and edges, `pathway.find_parameterizations()` discovers new routes, and `execution.MethodDispatcher` can call the function.
