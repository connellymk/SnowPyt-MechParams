# Interpreting Results

`ExecutionResults` is the main return type from `ExecutionEngine.execute_all`.
It stores the requested target, the unchanged source slab, pathway results, and
cache statistics.

```python
print(results.successful_pathways, results.total_pathways)
print(results.cache_stats)
```

## Pathway Results

Each `PathwayResult` stores:

| Field | Meaning |
| --- | --- |
| `methods_used` | Mapping from parameter names to selected method names. |
| `slab` | Result slab with pathway-specific computed values. |
| `computation_trace` | Ordered trace of layer and slab computations. |
| `success` | Whether the requested target was produced. |
| `warnings` | Non-fatal issues recorded during execution. |

## Computation Traces

Traces are the best place to audit why a pathway succeeded or failed:

```python
for trace in pathway_result.get_failed_traces():
    print(trace.parameter, trace.method_name, trace.error)
```

Layer traces have a `layer_index`; slab-level traces use `layer_index=None`.
Cached traces show `cached=True`, which helps separate reused values from fresh
formula calls.

## Comparing Pathways

For scientific comparisons, group results by `methods_used` and compare the
target value on each successful result slab. For example, `pathway.slab.D11`
contains the computed bending stiffness for a successful `D11` pathway.
