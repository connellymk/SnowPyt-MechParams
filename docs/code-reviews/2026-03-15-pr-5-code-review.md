# Code Review Report

**Date:** 2026-03-15
**Branch:** `mkc/add-stability-criterion` → `main`
**PR:** [#5](https://github.com/connellymk/SnowPyt-MechParams/pull/5) — Implement stability criterion
**Files Changed:** 110 (+70,596 / −21,170)

---

## Overall Rating: B

| Metric | Count |
|--------|-------|
| Critical Issues | 1 |
| Required Improvements | 3 |
| Recommendations | 4 |

---

## Critical Issues *(must fix before merge)*

**[CRITICAL] `tests/` — No pytest tests for `calculate_roch` or `calculate_shear_stress`**

> **What:** The Roch stability criterion (`roch_criterion.py`, `shear_stress.py`) is the headline contribution of this PR, but there are zero pytest tests for it. The WEAC criterion has 435 lines of tests covering unit validation, edge cases, UFloat stripping, and integration. The Roch criterion has none. MEMORY.md mentions "6 smoke tests pass," but those appear to be notebook-based, not part of the pytest suite.
>
> **Why:** This is a function used in a peer-reviewed paper. Missing tests mean the formula and edge-case handling are unverified by the CI system. Regressions (e.g., from a refactor) will go undetected.
>
> **Fix:** Add `tests/test_roch_criterion.py` covering at minimum:
> - `calculate_shear_stress` on a known single-layer slab: e.g., ρ=300 kg/m³, h=0.5 m, θ=38° → τ = 300 × 0.5 × 9.81 × sin(38°) ≈ 904 N/m²
> - `calculate_roch` natural variant returns correct S_r = τ_c / τ
> - `calculate_roch` skier variant returns correct S_sk = (τ_c − τ) / τ_sk
> - Returns `None` when `slab.angle is None`
> - Returns `None` when a layer is missing `density_calculated`
> - Returns `None` for flat terrain (τ = 0, natural variant)
> - Returns `None` for negative τ (see Required Improvement below)

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `src/snowpyt_mechparams/stability_criteria/roch/shear_stress.py` + `roch_criterion.py` — Negative slope angle produces unphysical stability index**

> **What:** If `slab.angle < 0` (a counter-slope), `calculate_shear_stress` returns a negative τ. `calculate_roch` then passes the `tau_val != 0` check and computes `S_r = τ_c / τ` with a negative denominator, yielding a negative stability index — physically meaningless.
>
> **Why:** Real dataset slabs occasionally have negative or zero slope angles. A negative S_r will propagate silently into results and paper statistics without triggering any error.
>
> **Fix:** Add a guard in `calculate_roch` immediately after extracting `tau_val`:
> ```python
> if tau_val is None or math.isnan(tau_val) or tau_val < 0:
>     return None
> ```
> Alternatively, clamp in `calculate_shear_stress` and document that negative angles are treated as flat terrain.

---

**[REQUIRED] `src/snowpyt_mechparams/models/pit.py:287` — `FutureWarning`: UFloat comparison with `<=` / `<`**

> **What:** `layer.depth_top <= failure_depth < layer.depth_bottom` compares `UncertainValue` (which may be `uncertainties.UFloat`) with a plain float using `<=` and `<`. The `uncertainties` library emits `AffineScalarFunc.__gt__()` is deprecated; this will become a hard error in a future `uncertainties` release.
>
> **Why:** This warning fires on every call to `create_slabs` with ECTP/CT results (confirmed by the test run warnings). It will break silently when `uncertainties` bumps its major version.
>
> **Fix:** Strip to nominal values before comparison:
> ```python
> dt = float(layer.depth_top)
> db = float(layer.depth_bottom)
> if dt <= failure_depth < db:
>     weak_layer = layer
>     break
> ```

---

**[REQUIRED] `src/snowpyt_mechparams/stability_criteria/weac/weac_criterion.py:255` — `assert` in production code**

> **What:** `assert total_h is not None` is used as a runtime guard inside `calculate_weac_skier`.
>
> **Why:** Python assertions are stripped when running with `python -O` (optimized mode), so this guard disappears in optimized deployments. If `total_h` is somehow `None` (e.g., if `slab.total_thickness` returns `None` for an empty slab), the function crashes with an `AttributeError` on the next line instead of returning `None` gracefully.
>
> **Fix:** Replace with an explicit guard:
> ```python
> if total_h is None:
>     return None
> ```

---

## Recommendations *(worth doing, not blocking)*

**[REC] `src/snowpyt_mechparams/stability_criteria/roch/roch_result.py:28` — Docstring formatting bug**

> The `skier_stress` field description is outdented to column 0, breaking the docstring's indentation structure:
> ```
>     variant : {"natural", "skier"}
>         Which form of the criterion was evaluated.
> skier_stress : UncertainValue, optional      ← outdented
>         Additional skier shear stress τ_sk...
> ```
> This will render incorrectly in any documentation generator. Fix: indent `skier_stress :` to align with the other attribute descriptions.

---

**[REC] `tests/test_weac_criterion.py:33` — Non-standard `conftest` import**

> `from conftest import requires_weac` is unusual. Pytest auto-discovers marks from `conftest.py`; typically test files use the mark directly via `@requires_weac` without importing from `conftest`. This pattern works but is fragile — it breaks if the test file is run in isolation outside the project root. Standard pattern:
> ```python
> import pytest
> requires_weac = pytest.mark.skipif(...)  # or just rely on auto-discovery
> ```

---

**[REC] `tests/test_copy_optimization.py:62–63` — Dead `id()` calls**

> ```python
> id(slab.layers[0])   # result discarded
> id(slab.layers[1])   # result discarded
> ```
> These calls do nothing. The actual assertions at lines 77–78 use `is not slab.layers[0]`, not the stored IDs. Delete these two lines.

---

**[REC] `tests/test_elastic_modulus_methods.py:83` — Discarded `ufloat` assignment**

> ```python
> ufloat(10000.0, 0.0)   # assigned to nothing
> ```
> This was `E_ice = ufloat(10000.0, 0.0)` before the refactor. The variable is no longer used in the test (the constant is accessed via `E_ICE_POLYCRYSTALLINE`). Delete this line.

---

## Summary

This is a substantial PR that delivers two new stability criteria (Roch and WEAC), a complete domain model reorganization (`data_structures` → `models`), new weak layer parameter functions, and a full dispatcher integration. The architecture is clean: both criteria follow the same module pattern, `RochResult` and `WeacSkierResult` are proper dataclasses, `_utils._nominal` is correctly centralized, and the optional WEAC import guard is well-handled.

The WEAC criterion in particular is well-tested (435 lines covering validation, edge cases, UFloat stripping, and integration). That standard needs to be applied to the Roch criterion before merge — it's the simpler of the two criteria and shouldn't take long to cover.

The negative-slope-angle physics bug and the `FutureWarning` from UFloat comparisons in `pit.py` are both real issues that will surface in production. The `assert` guard in `weac_criterion.py` is a minor risk but worth fixing while you're in the file.

The PR description is empty — add a summary of what changed (the criteria, the model rename, the new weak layer parameters) so future maintainers can understand it at a glance.
