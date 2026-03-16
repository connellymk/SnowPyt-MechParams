# Code Review Report

**Date:** 2026-03-16
**Branch:** `mkc/add-stability-criterion` → `main`
**PR:** [#5](https://github.com/connellymk/SnowPyt-MechParams/pull/5) — Implement stability criterion
**Scope:** `src/snowpyt_mechparams/models/` (moved from `data_structures/`) and related tests
**Files Changed:** 115 total (+71,437 / -21,174)

---

## Overall Rating: B

| Metric | Count |
|--------|-------|
| Critical Issues | 0 |
| Required Improvements | 2 |
| Recommendations | 4 |

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `tests/test_pit_layer_slab_creation.py`:491–530** — *ECTP propagation filter is never actually tested*

> **What:** The test `test_create_slabs_ectp_returns_empty_when_no_propagation` intends to verify that ECT results without propagation are excluded. But `Mock()` auto-creates any accessed attribute as a truthy child Mock, so `ect.propagation` is truthy for every Mock regardless of what you set on `ect.score`. The test passes because the single layer has no layers above it (depth_top = 0.0), not because the propagation filter rejected the result.
>
> `test_create_slabs_with_ectp_failure_layer` has the same issue in reverse — the ECT result is included by propagation matching, but only because Mock auto-creates a truthy `propagation` attribute, not because the "ECTP" score string path is being exercised.
>
> **Why:** Both tests pass for the wrong reason. If you removed the propagation filter from `_get_matching_ect_results`, all ECTP tests would still pass. This means the filter has zero test coverage against regression.
>
> **Fix:** Explicitly configure the `propagation` attribute on ECT mock objects:
> ```python
> # No-propagation case — must suppress auto-truthy Mock attribute
> ect_result = Mock(spec=["depth_top", "fracture_character", "test_score"])
> ect_result.depth_top = 5.0
> ect_result.test_score = "ECT15"   # no "ECTP" → should be filtered out
>
> # Or more simply:
> ect_result = Mock()
> ect_result.propagation = False     # explicit False overrides auto-Mock
> ect_result.test_score = "ECT15"
>
> # Propagation case:
> ect_result = Mock()
> ect_result.propagation = True
> ect_result.test_score = "ECTP15"
> ```
> Add a second test that exercises the `test_score`-based path (no `propagation` attr, score contains "ECTP").

---

**[REQUIRED] `README.md`:multiple lines** — *All `data_structures` import examples are now broken*

> **What:** `README.md` still references the deleted module in multiple code examples:
> ```python
> from snowpyt_mechparams.data_structures import Layer
> from snowpyt_mechparams.data_structures import Slab, Layer
> from snowpyt_mechparams.data_structures import Pit
> ```
> and has a directory tree listing `data_structures/` as a real path.
>
> **Why:** Anyone following the README (users, collaborators, reviewers) will immediately hit `ModuleNotFoundError`. The README is the first thing a new user reads.
>
> **Fix:** Replace all `data_structures` import examples with `snowpyt_mechparams.models`. Also update the directory tree to show `models/` and remove `data_structures/`. The `docs/2026-03-13-roch-stability-criterion.md` code examples have the same stale imports — worth cleaning up too.

---

## Recommendations *(worth doing, not blocking)*

**[REC] `src/snowpyt_mechparams/models/pit.py`:275–278** — *Public class importing a private function from its own factory module*

> `Pit._create_slab_from_test_result` does a deferred import of `_get_value_safe` (prefixed `_`, i.e., private) from `pit_parser`. This inverts the intended dependency: `Pit` is the domain model; `pit_parser` is the factory. Having the model reach back into the factory's private implementation to borrow a utility is a design smell. `_get_value_safe` is a generic "extract scalar from array-or-scalar" helper — it has nothing specifically to do with pit parsing and belongs in a shared utilities module (e.g., `models/utils.py` or `models/_utils.py`), or could be inlined at the one call site in `Pit` since it's a three-liner.

---

**[REC] `src/snowpyt_mechparams/models/pit.py`:46** — *`slope_angle: Any` is unnecessarily loose*

> The field is typed `Any` but in practice it is either `float` (NaN) or `uncertainties.UFloat`. Typing it as `Union[float, UncertainValue]` (where `UncertainValue` comes from `_types.py`) makes the intent explicit and lets type checkers flag accidental misuse downstream. The `Any` annotation also weakens typing across everything that reads `slab.angle`, since `Slab.angle: UncertainValue` gets assigned from `pit.slope_angle` without any type narrowing.

---

**[REC] `src/snowpyt_mechparams/models/__init__.py`** — *`WeakLayerDef` is a public-facing type that isn't exported*

> `WeakLayerDef = Literal["layer_of_concern", "CT_failure_layer", "ECTP_failure_layer"]` is defined in `pit.py` and is part of the public API of `create_slabs`. Users who want to write type-annotated code that passes a `WeakLayerDef` to `create_slabs` have no way to import it cleanly without reaching into `snowpyt_mechparams.models.pit` directly. Add it to `models/__init__.py` and `__all__`.

---

**[REC] `src/snowpyt_mechparams/models/pit_parser.py`:100** — *`include_density` parameter on `_create_layers` is never used with `False`*

> The `include_density: bool = True` parameter exists but `_create_layers` is called exactly once (from `parse_pit`) with no argument, always using the default. It's dead optionality. Either add a call site that uses `include_density=False`, or remove the parameter — having an untested code path behind a flag is a liability.

---

## Summary

This is a clean, well-executed refactor. The core structural improvements are solid:

- **Separation of parsing from domain model** is the right call. The old `Pit.__post_init__` was doing too much — it held a reference to the raw snowpylot `SnowPit` for the object's entire lifetime, mixed parsing with storage, and made `Pit` awkward to construct in tests. The new split (`Pit` as a pure data container, `pit_parser.parse_pit()` as the factory) is textbook SRP.
- **Removing `snow_pit: Any` from `Pit`** eliminates an unnecessary memory hold on the raw snowpylot object and decouples the domain model from the external library's schema.
- **Removing the `pit: Pit` back-reference from `Slab`** was the right move — that circular reference was a serialization and memory hazard.
- **`WeakLayerDef = Literal[...]`** replacing a stringly-typed `Optional[str]` is a concrete API improvement.
- **Circular import handling** (deferred `from pit_parser import parse_pit` inside `from_snow_pit`) is handled cleanly without module-level hacks.
- **Test coverage breadth** is good: 21 tests cover all four `weak_layer_def` paths, multiple ECT/CT results, missing slope angle/pit ID, and the grain form precedence logic.

The two required items are both fixable quickly. The ECTP test issue is the more substantive one — Mock's auto-attribute behavior is a known pitfall and the fix is a one-liner per fixture.
