# Code Review Report

**Date:** 2026-03-22
**Branch:** `mkc/add-stability-criterion` → `main`
**PR:** [#5](https://github.com/connellymk/SnowPyt-MechParams/pull/5) — Implement stability criterion
**Scope:** `src/snowpyt_mechparams/layer_parameters/` (4 files)

---

## Overall Rating: A

| Metric | Count |
|--------|-------|
| Critical Issues | 0 |
| Required Improvements | 2 |
| Recommendations | 3 |

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `layer_parameters/density.py`:128–131, 222–225, 327–330** — *Case-sensitive grain form validation inconsistent with other modules*

> **What:** All three density functions validate grain forms against hard-coded uppercase string lists without normalizing the input to uppercase first (e.g., `if grain_form not in valid_grain_forms:`). Every other module in this PR (`elastic_modulus.py`, `poissons_ratio.py`, `shear_modulus.py`) now normalizes via `grain_form[:2].upper()` before comparing.
>
> **Why:** If a caller supplies a lowercase grain form (e.g., `'pp'`, `'fc'`), all three density functions return `ufloat(NaN, NaN)` silently. The new `test_lowercase_grain_form_normalized` tests in the Poisson's ratio tests would document this behavior if backfilled — but they don't exist for density. The asymmetry means the same grain form string succeeds in `calculate_elastic_modulus` and silently fails in `calculate_density`.
>
> **Fix:** Add `.upper()` normalization at the top of each private density function before the validity check. Note that Geldsetzer uses multi-character subtypes (`PPgp`, `RGmx`, `FCmx`), so a full `grain_form.upper()` (not `[:2].upper()`) is appropriate there, while Table 2/5 can use whichever normalization matches their lookup key format. At minimum, add a `test_lowercase_grain_form_normalized` test matching the pattern in `test_poissons_ratio_methods.py`.

---

**[REQUIRED] `layer_parameters/density.py`:336** — *`grain_size=None` crashes with TypeError in `_calculate_density_kim_jamieson_table5`*

> **What:** The function guards against `hand_hardness_index is None` (line 332) but has no equivalent guard for `grain_size`. The new `_to_ufloat` helper is called on `grain_size` unconditionally at line 336. When `grain_size` is None, `isinstance(None, (int, float))` is False, so `_to_ufloat` falls through to `cast(ufloat, None)` — which is a no-op at runtime and returns `None`. Subsequent arithmetic `a * h + b * None + c` raises a `TypeError`.
>
> **Why:** `grain_size` is an optional measurement that can realistically be missing from SnowPilot records. The function contract (returning `ufloat(NaN, NaN)` on missing inputs) is broken for this case, and the caller gets an unhandled exception rather than a graceful NaN.
>
> **Fix:**
> ```python
> if grain_size is None:
>     logger.debug("_calculate_density_kim_jamieson_table5: grain_size is None")
>     return ufloat(np.nan, np.nan)
> gs = _to_ufloat(grain_size)
> ```
> Also add a test: `calculate_density("kim_jamieson_table5", hand_hardness_index=ufloat(2.0, 0.0), grain_form="FC", grain_size=None)` should return NaN, not raise.

---

## Recommendations *(worth doing, not blocking)*

**[REC] `layer_parameters/elastic_modulus.py`:385–449** — *Schottner has no density range check*

> All other elastic modulus methods (`bergfeld`, `kochle`, `wautier`) return NaN when density falls outside the empirically validated range. `_calculate_elastic_modulus_schottner` does not. If the Schöttner et al. (2026) paper specifies a density range for the fits, add a range guard and document it. If no range is published, add a comment stating this explicitly so it's clear the omission is intentional.

---

**[REC] `layer_parameters/density.py`:21–25** — *`_to_ufloat` does not handle None*

> The function handles `int | float | ufloat` correctly, but silently passes `None` through via `cast`. Since the caller must still guard `None` separately, consider either documenting this explicitly or adding `if val is None: raise TypeError(...)` to make misuse fail loudly at the conversion boundary rather than at downstream arithmetic.

---

**[REC] `layer_parameters/elastic_modulus.py` (kochle) and density tests** — *Missing plain-float input tests for `_to_ufloat` path*

> The `_to_ufloat` helper exists specifically to accept `UncertainValue = Union[float, ufloat]`. There are no tests that exercise the plain-float (non-ufloat) input path for any density function. A one-liner — passing a bare Python float as `hand_hardness_index` and asserting the result is valid — would close the gap and document the intended API contract.

---

## Summary

This is a clean, well-structured set of changes to the `layer_parameters` module. Two genuine bugs are fixed: the `'RC'` → `'FC'` typo in kochle's valid grain form list (which was silently returning NaN for all FC layers), and the `math.e ** (b * h)` → `umath.exp(b * h)` substitution in the kim_jamieson_table2 RG nonlinear formula (ensuring uncertainty propagates through the exponential correctly). The `_to_ufloat` helper is a well-reasoned defensive pattern that correctly handles the `Union[float, ufloat]` type. The conversion of inline lambdas to named `def _u(...)` helpers improves readability and fixes a Python typing edge case. The `grain_form[:2].upper()` normalization applied across elastic modulus, Poisson's ratio, and shear modulus closes a real robustness gap.

Test coverage is strong: all methods have numerical validation against hand-computed expected values, uncertainty behavior is explicitly verified, and the new `test_FC_rho_300` test for kochle correctly documents the grain-form typo fix.

The two required items are both small: a missing None-guard for `grain_size` in `kim_jamieson_table5` (would crash rather than return NaN if grain size is absent from a SnowPilot record), and the lack of case-normalization in density functions that creates an inconsistency with the other three modules in this same directory.
