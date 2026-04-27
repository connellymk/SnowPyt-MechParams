# Pathway Execution

The execution engine has two distinct stages:

1. Build or reuse the registry-generated parameter graph.
2. Execute every discovered pathway against a specific `Slab`.

```python
from snowpyt_mechparams.execution import ExecutionEngine

engine = ExecutionEngine()
results = engine.execute_all(slab, "D11")
```

`ExecutionResults` keeps the original input slab unchanged and returns one
`PathwayResult` per pathway description.

## Success And Failure

A pathway succeeds when the requested target is produced. Failed pathways remain
in the result object with computation traces and error messages, so missing data
and unsupported method ranges are visible instead of silently discarded.

```python
successful = results.get_successful_pathways()
failed = results.get_failed_pathways()
```

## Caching

The engine clears its cache at the start of each `execute_all` call. During that
call, layer-scoped values declared cacheable by the registry can be reused across
pathways for the same slab. In the built-in registry, density methods are
cacheable; downstream modulus and slab outputs are recomputed per pathway so
their upstream method context and uncertainty budgets remain correct.

## Running A Specific Method Combination

```python
result = engine.execute_single(
    slab,
    target_parameter="D11",
    methods={
        "density": "geldsetzer",
        "elastic_modulus": "bergfeld",
        "poissons_ratio": "kochle",
    },
)
```

`execute_single` returns `None` if the requested method combination is not a
registered pathway for the target.
