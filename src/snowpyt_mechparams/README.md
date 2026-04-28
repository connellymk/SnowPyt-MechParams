# snowpyt_mechparams

Top-level package for estimating snow mechanical parameters from snow pit data.

The package is organized around four steps:

1. `models` stores field observations and computed values on `Layer`, `Slab`, and `Pit` objects.
2. `methods` declares every calculation method in a `MethodRegistry`.
3. `graph` builds the dependency graph from that registry.
4. `pathway` and `execution` enumerate and run every valid route from measurements to a requested target.

Most research workflows should start with:

```python
from snowpyt_mechparams import ExecutionEngine

engine = ExecutionEngine()
results = engine.execute_all(slab, "D11")
```

Use `methods.default_registry()` when adding or inspecting built-in methods, and `graph.default_graph` when manually exploring pathways.
