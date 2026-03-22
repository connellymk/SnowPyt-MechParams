# Code Review Report

**Date:** 2026-03-22
**Branch:** mkc/add-stability-criterion → main
**PR:** [#5](https://github.com/connellymk/SnowPyt-MechParams/pull/5) — Implement stability criterion
**Focus:** `src/snowpyt_mechparams/weak_layer_parameters/`
**Files Reviewed:** 7 (all files in the module)

---

## Overall Rating: B

| Metric | Count |
|--------|-------|
| Critical Issues | 0 |
| Required Improvements | 2 |
| Recommendations | 2 |

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `weak_layer_parameters/fracture_energy.py` + `__init__.py`** — *`calculate_Gc` naming inconsistent with sibling functions*

> **What:** The public function for total fracture energy is named `calculate_Gc` (no underscore before `c`), while the mode-I and mode-II equivalents are `calculate_G_Ic` and `calculate_G_IIc` (with underscore). The graph/dispatcher parameter node is named `G_c`, not `Gc`.
>
> **Why:** This is a public API inconsistency. A user or future contributor reading `__init__.py` will see `calculate_Gc`, `calculate_G_Ic`, `calculate_G_IIc` and reasonably assume `Gc` and `G_Ic` follow different naming conventions. It also makes the function name disagree with the string parameter name `"G_c"` used in the dispatcher and graph.
>
> **Fix:** Rename to `calculate_G_c` in `fracture_energy.py` and `__init__.py`. Update the dispatcher import accordingly. This is a one-line change in three files and keeps the public API consistent: `calculate_G_c`, `calculate_G_Ic`, `calculate_G_IIc`.

---

**[REQUIRED] Missing direct unit tests for new functions** — *All four new functions lack module-level unit tests*

> **What:** `calculate_Gc`, `calculate_G_Ic`, `calculate_G_IIc`, and `calculate_tau_c` have no direct pytest coverage. `test_weak_layer_engine.py` tests the dispatcher/executor integration (via lambdas), which verifies the numerical values end-to-end, but doesn't test the functions themselves — invalid method strings, the `**kwargs`-passthrough contract, or return types.
>
> **Why:** The integration tests in `TestDispatcherExecuteWeakLayer` partially cover numerical output, but they only exercise the `'weissgraeber_rosendahl'` path through the dispatcher. If a function's dispatch logic were broken (e.g., the `method.lower()` guard), the integration test would still pass as long as the lambda wrapper works. Direct tests are also needed to verify `ValueError` is raised for unrecognised method strings — a contract the docstrings promise but no test currently validates.
>
> **Fix:** Add a `tests/test_weak_layer_parameters.py` with:
> - One test per new function confirming the nominal value and zero uncertainty of the reference constant
> - One test per function confirming `ValueError` is raised for an unknown method string
> - Tests for `calculate_sigma_c_minus('mellor', density=ufloat(250, 0))` and `calculate_sigma_c_plus('sigrist', density=ufloat(250, 0))` to cover the density-dependent paths (these already existed but have no direct tests either)

---

## Recommendations *(worth doing, not blocking)*

**[REC] `sigma_c_minus.py`** — *`'reiweger'` and `'weissgraeber_rosendahl'` return the same value — consider consolidating or clarifying intent*

> Both `_calculate_sigma_c_minus_reiweger()` and `_calculate_sigma_c_minus_weissgraeber_rosendahl()` return `ufloat(2.6, 0.0)` kPa, and the docstring acknowledges they share the same original source (Reiweger et al. 2015). Having two method strings that produce identical output is a potential footgun: a user who picks `'reiweger'` expecting density-dependent output (like the Mellor method) will get a constant, and the reason for the `'weissgraeber_rosendahl'` alias won't be obvious without reading the docs.
>
> Consider either: (a) deprecating `'reiweger'` in favour of `'weissgraeber_rosendahl'` once the WEAC integration is the canonical path, or (b) making the docstring note on duplication more prominent in the public `calculate_sigma_c_minus` docstring, not just in the private function.

---

**[REC] `sigma_c_minus.py` / `sigma_c_plus.py`** — *`rho_ice` → `RHO_ICE` fix is worth a brief commit note*

> The diff replaces `density / rho_ice` with `density / RHO_ICE` in both power-law formulas. Depending on the original code, this either removes a local alias (`rho_ice = RHO_ICE`) or fixes a latent `NameError` that would have surfaced the first time `'mellor'` or `'sigrist'` was called. Either way, the current code is correct. If it was a NameError, it's worth flagging in the PR description so reviewers know this is a bug fix, not just a style change.

---

## Summary

This is a solid, well-scoped addition. The new files — `fracture_energy.py`, `mode_i_fracture_toughness.py`, `mode_ii_fracture_toughness.py`, and `tau_c.py` — all follow the same clean structure: dispatcher pattern, consistent use of `ufloat`, accurate reference values cross-checked against WEAC's built-in defaults, and good docstrings with DOI-linked citations. The updates to `sigma_c_minus.py` and `sigma_c_plus.py` correctly add the `'weissgraeber_rosendahl'` method and fix the `rho_ice` variable usage.

The two required items are both straightforward: a one-line function rename (`Gc` → `G_c`) and a new test file. Neither touches the physics or the integration logic. The integration tests in `test_weak_layer_engine.py` are thorough and give good confidence the dispatcher wiring is correct — the missing tests are complementary unit coverage, not a substitute.

Address the naming inconsistency and add the direct unit tests and this is ready to merge.
