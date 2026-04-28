# Contributor Guide

Most new scientific methods should enter the framework through the method
registry. The registry is the single source of truth for graph construction,
pathway discovery, dispatch, caching, and method documentation.

## Add A Method

1. Implement the focused formula in `methods/layer` or `methods/slab`.
2. Add one `MethodSpec` in `methods/registry.py`.
3. Include canonical `citation` and useful `description` metadata.
4. Add numerical tests for the formula and consistency tests for registry,
   graph, pathway, and execution behavior.
5. Regenerate the method catalog.

`MethodSpec` currently records:

| Field | Purpose |
| --- | --- |
| `target` | Parameter being calculated, such as `density`, `D11`, or `slab_weight_shear`. |
| `method_name` | Stable method identifier shown in pathway descriptions. |
| `level` | `ParameterLevel.LAYER` or `ParameterLevel.SLAB`. |
| `source_nodes` | Graph dependencies required by the method. |
| `required_inputs` | Runtime values read from a layer, slab, or execution context. |
| `function` | Callable formula implementation. |
| `output_attr` | Model attribute where the result is stored. |
| `cache_scope` | `"none"` or `"layer"`. |
| `description` | Short user-facing method summary. |
| `citation` | Canonical source label for docs and provenance. |

## Documentation Checks

After method metadata changes, regenerate and check the catalog:

```bash
uv run --extra dev python docs/_scripts/generate_method_catalog.py
uv run --extra dev python docs/_scripts/generate_method_catalog.py --check
```

Build docs with warnings as errors:

```bash
uv run --extra dev sphinx-build -W -b html docs /tmp/snowpyt_docs_html
```

## Notebook Checks

Smoke active notebooks when public imports, pathway counts, method provenance,
or scientific outputs change. The root README lists the highest-value notebook
commands for routine checks.
