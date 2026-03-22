# Code Review Report

**Date:** 2026-03-22
**Branch:** mkc/add-stability-criterion → main
**PR:** [#5](https://github.com/connellymk/SnowPyt-MechParams/pull/5) — Implement stability criterion
**Scope:** `src/snowpyt_mechparams/stability_criteria/` (focused review)
**Files Changed:** 8 source files, 2 test files

---

## Overall Rating: B

| Metric | Count |
|--------|-------|
| Critical Issues | 0 |
| Required Improvements | 2 |
| Recommendations | 3 |

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `stability_criteria/roch/shear_stress.py`:44–50** — *NaN sentinel inconsistent with codebase convention*

> **What:** `calculate_shear_stress` returns `float('nan')` when a layer is missing `thickness` or `density_calculated`. Every other function in this codebase that encounters missing inputs returns `None` (see all layer parameter methods in `layer_parameters/`). The NaN sentinel forces callers to use the awkward `_nominal(tau)` + `math.isnan()` double-check instead of a simple `if tau is None` guard.
>
> **Why:** This is the only function in the codebase that uses NaN as a sentinel for "missing data". The inconsistency makes the calling pattern in `roch_criterion.py` harder to read and creates a silent failure mode: if a caller forgets the `isnan` check (easy to do since `float` is a valid `UncertainValue`), they pass NaN downstream without realizing it. The docstring warning "the caller should check `math.isnan(float(result))` before use" is a sign the API is fighting the language's conventions.
>
> **Fix:** Change the return type to `Optional[UncertainValue]` and return `None` for missing-data cases. Update the callers in `roch_criterion.py`:
> ```python
> # shear_stress.py
> def calculate_shear_stress(slab: Slab) -> Optional[UncertainValue]:
>     ...
>     for layer in slab.layers:
>         if layer.thickness is None or layer.density_calculated is None:
>             return None   # was: return float('nan')
>         ...
>
> # roch_criterion.py — caller simplifies to:
> tau = calculate_shear_stress(slab)
> if tau is None:
>     return None
> tau_val = _nominal(tau)
> if tau_val is None or tau_val < 0:
>     return None
> ```
> The `math.isnan` check is no longer needed once NaN can't appear.

---

**[REQUIRED] `stability_criteria/roch/roch_criterion.py`:36** — *tau_c unit mismatch risk not flagged at the call boundary*

> **What:** `calculate_roch` expects `tau_c` in **N/m² (Pa)**, but `WeakLayer.tau_c` — the natural source for this value — is documented and stored in **kPa**. The conversion (`× 1000`) is performed correctly in `dispatcher.py` line 517, but nothing in `calculate_roch`'s signature or docstring warns callers of this asymmetry. The function is part of the public API (exported from `stability_criteria.__init__`), so a notebook user or future caller is likely to pass `slab.weac_layer.tau_c` directly and get a stability index that is 1000× too small — appearing as S_r ≈ 0.001 for a stable slope instead of S_r ≈ 1.5.
>
> **Why:** This is the most likely incorrect-usage mistake a downstream caller can make. The formula is correct; the risk is at the interface.
>
> **Fix:** Add an explicit unit note to the docstring parameter description:
> ```python
> tau_c : UncertainValue
>     Shear strength of the weak layer [Pa = N/m²].
>     Note: ``WeakLayer.tau_c`` is stored in kPa — convert before calling:
>     ``tau_c=slab.weac_layer.tau_c * 1000``.
> ```
> Alternatively, consider accepting kPa and converting internally, but that would require changing the dispatcher.

---

## Recommendations *(worth doing, not blocking)*

**[REC] `stability_criteria/weac/weac_criterion.py`:190** — *Replace `getattr` with direct attribute access*

> `getattr(slab.weak_layer, "density_calculated", None)` should be `slab.weak_layer.density_calculated`. The `Layer` dataclass always has this field; the defensive `getattr` implies it might not, which is misleading. Direct attribute access is cleaner and consistent with how every other `Layer` field is accessed in this file.

---

**[REC] `stability_criteria/weac/weac_result.py`:34** — *Rename `critical_skier_weight` to `critical_skier_mass_kg`*

> The field stores **mass in kg**, not weight in N. The docstring acknowledges the inconsistency ("Stored as mass despite the 'weight' name — this mirrors the field name used by `weac`"), but this is a case where staying consistent with an upstream naming error is worse than diverging from it. `critical_skier_mass_kg` or `critical_skier_mass` is unambiguous. The docstring note becomes unnecessary.

---

**[REC] `stability_criteria/roch/roch_result.py` and `weac_result.py`** — *Consider `frozen=True` on result dataclasses*

> Both `RochResult` and `WeacSkierResult` are result objects — they're computed once and should not be mutated. Adding `@dataclass(frozen=True)` makes that intent explicit, prevents accidental mutation, and provides `__hash__`, which is useful if results are ever used in sets or as dict keys. There is no runtime cost.

---

## Summary

This is a solid implementation. The module structure is clean: one sub-package per criterion, a clear `__init__.py` at each level, result dataclasses for structured return values, and a well-designed `_utils.py` for shared helpers. The WEAC adapter in particular is impressive — it correctly handles lazy imports, UFloat stripping at the solver boundary, optional SIGALRM timeout, and RecursionError from non-converging solabs, all with clear documentation explaining the design choices.

The Roch tests are thorough: they cover both variants, all None-return conditions, UFloat propagation, numerical correctness against hand-computed values, and the `stable / unstable` boundary. The WEAC tests correctly gate integration tests with `@requires_weac` and cover validation paths without needing a real solver.

The two required items are low effort to fix: one is an API convention inconsistency (NaN vs None sentinel), and the other is a one-line docstring addition to prevent a silent unit-mismatch bug at the public call boundary. Neither reflects a flaw in the underlying physics or algorithm — the formulas are correct, units are consistent in the execution path, and the science is sound.
