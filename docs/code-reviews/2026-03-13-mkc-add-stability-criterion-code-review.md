# Code Review Report

**Date:** 2026-03-13
**Branch:** mkc/add-stability-criterion → main
**PR:** mkc/add-stability-criterion — Add WEAC skier stability criterion and Roch criterion
**Files Changed:** 34 (+30,650 / -374)

---

## Overall Rating: B

| Metric | Count |
|--------|-------|
| Critical Issues | 0 |
| Required Improvements | 2 |
| Recommendations | 4 |

**Rating guide:**
- **A** — Ready to merge with minor nits only
- **B** — A few things to fix but solid overall; can merge after addressing required items
- **C** — Significant issues; needs meaningful rework before merge
- **D** — Fundamental problems; needs a rethink or substantial rewrite

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `stability_models/weac/weac_criterion.py`:285-295** — *SIGALRM timeout crashes in non-main threads*

> **What:** The `_use_timeout` guard (line 285) checks for non-Windows + SIGALRM availability, but does not check whether the caller is on the main thread. `signal.signal()` raises `ValueError: signal only works in main thread` if called from a worker thread.
>
> **Why:** This matters as soon as a user runs batch processing with `ThreadPoolExecutor` or `multiprocessing.pool.ThreadPool` and sets `weac_timeout_seconds`. The exception propagates out of `calculate_weac_skier` uncaught (since the `except` clause only catches `RecursionError` and `_WeacTimeout`), crashing the worker. The user's batch loop fails with a confusing error.
>
> **Fix:** Add a main-thread check to `_use_timeout`:
> ```python
> import threading
> _use_timeout = (
>     timeout_seconds is not None
>     and sys.platform != "win32"
>     and hasattr(signal, "SIGALRM")
>     and threading.current_thread() is threading.main_thread()
> )
> ```
> Also update the `calculate_weac_skier` docstring: "Only supported on POSIX systems **in the main thread**; silently skipped otherwise."

---

**[REQUIRED] `stability_models/weac/weac_result.py`:35** — *`critical_skier_weight` documented with wrong units*

> **What:** The docstring says `critical_skier_weight` is in [kg], but the field name is "weight" (a force) and the value is passed through directly from WEAC's `result.critical_skier_weight`. WEAC internally computes forces in Newtons.
>
> **Why:** If the unit is actually N (as the name "weight" implies), the docstring is wrong and will mislead anyone interpreting the result. If it truly is kg (mass), the field should be named `critical_skier_mass`. Either way, the current state is ambiguous.
>
> **Fix:** Confirm what unit WEAC returns for `result.critical_skier_weight`. Then either:
> - Update the docstring to `[N]` (most likely correct), or
> - Rename the field to `critical_skier_mass` with unit `[kg]` if WEAC returns mass.
>
> Also add a unit assertion to `test_critical_skier_weight_positive` — e.g., `assert result.critical_skier_weight > 100` (a 80 kg skier weighs ~785 N) so the test catches a silent unit swap.

---

## Recommendations *(worth doing, not blocking)*

**[REC] `tests/test_weac_criterion.py`:172-186** — *Dead-code object in `test_returns_none_when_angle_is_none`*

> The test creates a `slab` object at line 181 (`Slab(layers=[layer], angle=None)`) and immediately discards it. Only `slab_no_angle` (built from `_make_minimal_slab()`) is actually used. Remove the dead `layer`/`slab` construction at lines 174–183; the test reads more clearly with just:
> ```python
> slab = _make_minimal_slab()
> slab.angle = None
> assert self.fn(slab) is None
> ```

---

**[REC] `tests/test_weac_criterion.py` and `tests/test_weak_layer_engine.py`** — *Duplicate WEAC guard boilerplate; should be in `conftest.py`*

> Both files repeat the same 8-line block:
> ```python
> try:
>     import weac as _weac_pkg
>     _WEAC_AVAILABLE = True
> except ImportError:
>     _WEAC_AVAILABLE = False
> requires_weac = pytest.mark.skipif(...)
> ```
> Move this to `tests/conftest.py` as a session-scoped fixture or module-level mark so future test files can just import `requires_weac` from conftest.

---

**[REC] `tests/test_weac_criterion.py` — integration test class** — *Repeated local imports inside test methods*

> `calculate_weac_skier` is imported inside ~10 individual `@requires_weac` test methods. Move it to `setup_method` once (or use a module-level import with a `pytest.importorskip` guard). Repeated local imports add noise without providing isolation benefit since WEAC availability is already checked by the `@requires_weac` mark.

---

**[REC] `execution/executor.py`:428** — *Missing `Optional` in `_get_or_compute_layer_param` signature*

> ```python
> def _get_or_compute_layer_param(
>     self, layer, layer_index, parameter, method,
>     config: 'ExecutionConfig' = None   # ← typed as ExecutionConfig but default is None
> )
> ```
> The type annotation should be `Optional['ExecutionConfig']`. Mypy will catch this as a type error if strict mode is enabled. Minor, but the project targets type-correctness.

---

## Summary

This is a well-executed, substantial addition. The adapter pattern for wrapping the external `weac` library is clean: the lazy-import guard (importable without weac, ImportError deferred until call time), UFloat stripping at the adapter boundary, and SIGALRM-based timeout are all good design decisions. The `WeakLayer` / `WeacSkierResult` dataclasses follow the existing project conventions closely, the graph extension is minimal and self-consistent, and the dispatcher registration is straightforward.

The test coverage is the strongest part of this PR. At 850+ lines across two files, it distinguishes unit paths (no weac required) from integration paths (WEAC optional), tests every early-return `None` condition, covers the `_nominal()` helper exhaustively, and validates the full pipeline from `Slab → g_delta`. That's a high bar.

The two required fixes are both mechanical and low-risk: add `threading.current_thread() is threading.main_thread()` to the timeout guard, and clarify/correct the `critical_skier_weight` unit. The thread-safety fix is the more important one — it will silently fail for anyone running parallel batches, which is the most natural use pattern for processing 14,951 ECTP slabs.

The recommendations (conftest deduplication, dead test code, type annotation) are housekeeping items that don't affect correctness.
