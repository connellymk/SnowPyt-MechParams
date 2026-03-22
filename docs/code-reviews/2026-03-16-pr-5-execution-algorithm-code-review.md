# Code Review Report

**Date:** 2026-03-16
**Branch:** mkc/add-stability-criterion → main
**PR:** [#5](https://github.com/connellymk/SnowPyt-MechParams/pull/5) — Implement stability criterion
**Scope:** `src/snowpyt_mechparams/execution/` and `src/snowpyt_mechparams/algorithm.py`

---

## Overall Rating: B

| Metric | Count |
|--------|-------|
| Critical Issues | 0 |
| Required Improvements | 4 |
| Recommendations | 4 |

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `execution/executor.py`:593** — *Runtime import inside method body*

> **What:** `_get_inputs_summary` contains a runtime `from snowpyt_mechparams.execution.dispatcher import _get_layer_input` inside the method body.
> **Why:** It imports a private function from the same package at call time. This is unexpected — module-level imports are the convention, it's harder to spot during code review, and it won't benefit from Python's module cache until the first call. Private functions (`_get_layer_input`) should either be made importable at module level or the dependency inverted.
> **Fix:** Move the import to the top of `executor.py` with the other dispatcher imports: `from snowpyt_mechparams.execution.dispatcher import MethodDispatcher, _get_layer_input`

---

**[REQUIRED] `execution/dispatcher.py`:38, 510, 526** — *Magic number for kPa→Pa unit conversion*

> **What:** The Roch criterion lambdas multiply `tau_c` by `1000` to convert from kPa to Pa. `1000` appears as a bare literal with only an inline comment explaining it.
> ```python
> calculate_roch(slab, tau_c=slab.weac_layer.tau_c * 1000)
> ```
> **Why:** For a codebase that will support a peer-reviewed paper, every unit conversion should be a named constant. If `tau_c`'s storage unit ever changes, a bare `1000` is easy to miss. The pattern is already well-established here: `STANDARD_SKIER_MASS_KG` and `STANDARD_SKI_CONTACT_AREA_M2` are named constants imported from `constants.py`.
> **Fix:** Add a named constant in `dispatcher.py` (or `constants.py`):
> ```python
> _KPA_TO_PA: float = 1000.0  # 1 kPa = 1000 N/m²
> ```
> Then use it: `tau_c=slab.weac_layer.tau_c * _KPA_TO_PA`

---

**[REQUIRED] `execution/executor.py`:390–396** — *`_build_pathway_description` silently drops stability method*

> **What:** `_build_pathway_description` only iterates over `["density", "elastic_modulus", "poissons_ratio", "shear_modulus"]`. When the target is a stability criterion (`g_delta`, `s_r`, `s_sk`), the stability method name (e.g., `roch_natural`, `weac_skier`) is never included in the description.
> **Why:** The pathway description is used as the dict key in `engine.execute_all` (`results[result.pathway_description] = result`). For two different stability criteria targeting the same upstream methods (not possible in a single `execute_all` call today, but plausible as the graph expands), their descriptions would collide and one result would be silently dropped. Even without a collision, a human reading the description cannot tell which stability criterion was used.
> **Fix:** Extend the order list with weak-layer and stability params, or add a catch-all that appends any `methods_used` entries not already covered:
> ```python
> order = ["density", "elastic_modulus", "poissons_ratio", "shear_modulus",
>          "G_c", "G_Ic", "G_IIc", "sigma_c", "tau_c", "sigma_comp",
>          "g_delta", "s_r", "s_sk"]
> ```

---

**[REQUIRED] Tests** — *`execute_single` and `list_available_pathways` have zero test coverage*

> **What:** `ExecutionEngine.execute_single` (engine.py:197) and `list_available_pathways` (engine.py:298) are public API methods with no dedicated tests. The `test_executor_dynamic_programming.py` and `test_integration.py` suites cover `execute_all` extensively but never call these methods.
> **Why:** `execute_single` has non-trivial logic: it re-traverses the graph, extracts methods, matches against the requested `methods` dict via `_methods_match`, and only then executes. A bug in `_methods_match` (e.g., partial match when full match is required) would go undetected. Both methods call internal (`_`-prefixed) methods of `PathwayExecutor` from `ExecutionEngine`, which is a design smell that also lacks test cover.
> **Fix:** Add a test class `TestExecuteSingle` with at least: (1) successful execution with a valid `methods` dict, (2) returns `None` when no matching pathway exists, (3) confirms only the specified method combination is run. Add a `TestListAvailablePathways` with a basic smoke test.

---

## Recommendations *(worth doing, not blocking)*

**[REC] `execution/engine.py`:169, 256, 319** — *`find_parameterizations` re-traversed for every slab and every `execute_single` call*

> `find_parameterizations(self.graph, target_node)` is called on every invocation of `execute_all`, `execute_single`, and `list_available_pathways`. The traversal result is identical for a given `(graph, target_parameter)` pair — it's a pure function of the graph structure. With 14,951 slabs × multiple targets, this traverses the graph ~50k+ times when the result never changes. Cache it at engine init or lazily per target parameter:
> ```python
> self._pathway_cache: dict[str, list[Parameterization]] = {}
> # in execute_all:
> if target_parameter not in self._pathway_cache:
>     self._pathway_cache[target_parameter] = find_parameterizations(self.graph, target_node)
> parameterizations = self._pathway_cache[target_parameter]
> ```

---

**[REC] `execution/engine.py`:260, 323** — *Engine accesses private `PathwayExecutor` methods*

> `execute_single` and `list_available_pathways` both reach into `self.executor._extract_methods_from_parameterization`, `_build_pathway_description`, and `_build_pathway_id` (all `_`-prefixed). Calling private methods of a collaborator leaks implementation detail and makes refactoring harder.
> Either make these three methods public (drop the leading underscore) or expose a `describe_parameterization(param) -> dict` method on `PathwayExecutor` that returns the id, description, and methods dict in one call.

---

**[REC] `execution/executor.py`:192–193** — *`needs_computation` flag is always equal to `bool(execution_order)`*

> ```python
> needs_computation = any(param in methods_used for param in execution_order)
> ```
> `_determine_execution_order` already filters its output to only include params that are in `methods_used`, so every element of `execution_order` is guaranteed to be in `methods_used`. The `any(...)` expression is therefore always `True` when `execution_order` is non-empty and `False` when it is empty. Replace with:
> ```python
> needs_computation = bool(execution_order)
> ```

---

**[REC] `tests/test_executor_dynamic_programming.py`:38–39** — *Test accesses private `cache._stats` directly*

> ```python
> executor.cache._stats.hits = 10
> executor.cache._stats.misses = 5
> ```
> The `CacheStats` dataclass fields are `hits` and `misses` (public attributes on a public class). But `cache._stats` itself is private. The `test_clear_cache` test should manipulate the public cache API and then check stats via `executor.get_cache_stats()`, e.g.:
> ```python
> executor.cache.set_layer_param(0, "density", "geldsetzer", ufloat(250, 10))
> executor.cache.get_layer_param(0, "density", "geldsetzer")  # hit
> executor.cache.get_layer_param(0, "density", "kim_t2", )      # miss
> ```

---

## Summary

The execution module is well-architected. The three-level result hierarchy (`ComputationTrace` → `PathwayResult` → `ExecutionResults`) is clean and easier to navigate than typical layered execution engines. The documentation is unusually thorough — the multi-paragraph justification in `executor.py`'s module docstring for *why* only density is cached is exactly the kind of reasoning that belongs in scientific software. The dynamic programming cache design is correct and the decision to *not* cache downstream parameters is clearly explained and properly tested.

`algorithm.py` is solid. The backward traversal with memoization is correct, the `_method_fingerprint` deduplication is a well-placed fix for the Cartesian-product blowup, and the conversion from `PathTree` to `Parameterization` handles the branch-and-merge structure faithfully. No logic errors found.

The four required items are all minor but worth addressing before merge: the runtime import is unusual enough to confuse future contributors, the bare `1000` multiplier is risky in physical-units code, the incomplete pathway description is a latent key-collision bug, and the untested public API on `ExecutionEngine` is an obvious gap given the strong test coverage elsewhere.

The main architectural recommendation (caching `find_parameterizations` results at the engine level) is genuinely worth doing before the large-scale paper runs — calling it 14,951 times is wasted work.
