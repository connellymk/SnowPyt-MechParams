# Refactor Plan

**Created**: 2025-02-23
**Branch**: `mkc/add-input-uncertainties`
**Scope**: Correctness fixes, structural improvements, and hardening based on code review

---

## Phase 1 — Correctness (science-critical)

These issues affect numerical output or silently mask errors. Fix before any new analysis.

### 1.1 Add numerical validation tests for parameterization functions

**Problem**: No tests verify that `calculate_density`, `calculate_elastic_modulus`,
`calculate_poissons_ratio`, `calculate_shear_modulus`, or the slab parameter functions
produce correct values for known inputs. The existing test suite covers infrastructure
(algorithm, caching, dispatcher) but not the scientific calculations themselves.

**Action**: Create `tests/test_density_methods.py`, `tests/test_elastic_modulus_methods.py`,
`tests/test_poissons_ratio_methods.py`, `tests/test_shear_modulus_methods.py`, and
`tests/test_slab_parameters.py`. Each test file should:

- Test every method with at least 2 input/output pairs drawn from the source papers
  (table values, figure readings, or worked examples)
- Test boundary conditions (min/max valid density, edge grain forms)
- Test that unsupported grain forms return `ufloat(NaN, NaN)`
- Test that `include_method_uncertainty=True` vs `False` produces different std_dev
  values (where the flag actually has an effect — see 1.2)

**Files**:
- `tests/test_density_methods.py` (new)
- `tests/test_elastic_modulus_methods.py` (new)
- `tests/test_poissons_ratio_methods.py` (new)
- `tests/test_shear_modulus_methods.py` (new)
- `tests/test_slab_parameters.py` (new)

### 1.2 Fix `include_method_uncertainty` being silently ignored

**Problem**: Several methods accept the flag but hardcode zero uncertainty on their
coefficients, so the flag has no effect:

| Method | File | Line | Issue |
|--------|------|------|-------|
| `_calculate_elastic_modulus_kochle` | `elastic_modulus.py` | 152 | Coefficients `C_0`, `C_1` are plain floats; `E_ice` is `ufloat(10000, 0)`. Flag unused. |
| `_calculate_elastic_modulus_wautier` | `elastic_modulus.py` | 262 | `A = ufloat(0.78, 0.0)`, `n = ufloat(2.34, 0.0)`. Flag unused. |
| `_calculate_shear_modulus_wautier` | `shear_modulus.py` | 49 | `A = ufloat(0.92, 0.0)`, `n = ufloat(2.51, 0.0)`. Flag unused. |

**Action**: For each method, decide one of:

- **If uncertainty values are available in the paper** (e.g., confidence intervals on
  fitted coefficients): add them, gated on `include_method_uncertainty`, matching the
  pattern used in `bergfeld` and `schottner`.
- **If uncertainty values are not available**: document this explicitly in the docstring
  (e.g., "Wautier et al. (2015) do not report uncertainty on coefficients A and n;
  method uncertainty cannot be separated from input uncertainty for this parameterization")
  and either remove the parameter or keep it as a no-op with a comment.

Do not leave the parameter silently doing nothing.

**Files**:
- `layer_parameters/elastic_modulus.py`
- `layer_parameters/shear_modulus.py`

### 1.3 Investigate and document Kim-Jamieson RG nonlinear SE value

**Problem**: In `density.py:218`, the `RG` nonlinear regression has `SE = 0.2`, which
is orders of magnitude smaller than every other SE in the table (25-63 kg/m^3). This
could be:
- Correct (SE of a log-transformed or exponential coefficient, not a density SE)
- A transcription error from the paper

**Action**:
1. Verify against Kim & Jamieson (2014) Table 2.
2. If `0.2` is the SE of the coefficient `B=0.270` (not a density SE in kg/m^3),
   the uncertainty propagation is wrong — it's being added in quadrature with the
   density std_dev as if it were in the same units. Fix the propagation or convert
   to the correct units.
3. Add a comment documenting the source and interpretation.

**Files**:
- `layer_parameters/density.py`

### 1.4 Fix potential unbound variable in wautier/shear_modulus

**Problem**: In `_calculate_elastic_modulus_wautier` (line 343-353) and
`_calculate_shear_modulus_wautier` (line 132-143), the variable (`E_snow`/`G_snow`)
is assigned inside an `if/else` block but returned unconditionally afterward. If a
code path were added that bypassed the `if/else`, the variable would be unbound.

**Action**: Initialize the variable before the `if/else` block:

```python
E_snow = ufloat(np.nan, np.nan)  # default: out-of-range
if rho_snow.nominal_value < 103 or rho_snow.nominal_value > 544:
    pass  # E_snow stays NaN
else:
    ...
    E_snow = E_ice * (A * ((rho_snow / RHO_ICE) ** n))
return E_snow
```

**Files**:
- `layer_parameters/elastic_modulus.py`
- `layer_parameters/shear_modulus.py`

---

## Phase 2 — Structural improvements

These reduce maintenance burden and make the code easier to extend. No behavioral
changes when done correctly.

### 2.1 Extract shared slab parameter computation

**Problem**: `A11.py`, `B11.py`, `D11.py`, and `A55.py` duplicate ~80% of their code:
validation, layer iteration, Poisson's ratio bounds check, plane-strain modulus
calculation, unit conversion. The only difference is the accumulation formula.

**Action**: Create `slab_parameters/_common.py` with a shared helper:

```python
def _integrate_over_layers(
    slab: Slab,
    accumulate: Callable[[UncertainValue, UncertainValue, UncertainValue, UncertainValue, UncertainValue], UncertainValue],
) -> ufloat:
    """
    Validate slab, iterate layers, compute plane-strain modulus, and call
    `accumulate(plane_strain_modulus, h_i, z_top, z_bottom, running_sum)` per layer.
    """
```

Each slab parameter file becomes a thin wrapper calling `_integrate_over_layers` with
its specific accumulation function. Target: reduce ~780 lines across 4 files to ~250.

**Files**:
- `slab_parameters/_common.py` (new)
- `slab_parameters/A11.py` (simplify)
- `slab_parameters/A55.py` (simplify)
- `slab_parameters/B11.py` (simplify)
- `slab_parameters/D11.py` (simplify)

### 2.2 Add `__init__.py` to `layer_parameters/`

**Problem**: `layer_parameters/` is the only subdirectory in the package without an
`__init__.py`. It works because the dispatcher imports functions directly, but it's
inconsistent and prevents `from snowpyt_mechparams.layer_parameters import ...`.

**Action**: Create `layer_parameters/__init__.py` exporting the public functions:

```python
from snowpyt_mechparams.layer_parameters.density import calculate_density
from snowpyt_mechparams.layer_parameters.elastic_modulus import calculate_elastic_modulus
from snowpyt_mechparams.layer_parameters.poissons_ratio import calculate_poissons_ratio
from snowpyt_mechparams.layer_parameters.shear_modulus import calculate_shear_modulus
```

**Files**:
- `layer_parameters/__init__.py` (new)

### 2.3 Clean up minor code quality issues

**Action** (batch these into a single commit):

- `density.py:3`: Replace `from math import e` with explicit `math.e` usage or
  `from math import e as EULER` to avoid shadowing.
- `density.py:134`: Remove `cast(float, ...)` calls — they do nothing at runtime.
  The dict values are already floats.
- `weak_layer_parameters/Gc.py`: Either add a placeholder docstring with a TODO, or
  delete the file and remove any references.

**Files**:
- `layer_parameters/density.py`
- `weak_layer_parameters/Gc.py`

---

## Phase 3 — Hardening and usability

These improve the experience for users outside of the batch-analysis notebooks.

### 3.1 Add logging for NaN returns

**Problem**: Every calculation function returns `ufloat(NaN, NaN)` on invalid input
with no indication of why. In batch analysis this is fine (the notebooks count
successes). For interactive use, debugging a NaN result requires reading source code
to understand which validation failed.

**Action**: Add `logging.debug()` calls at each NaN return point, e.g.:

```python
logger = logging.getLogger(__name__)

if grain_form not in valid_grain_forms:
    logger.debug(
        "density.geldsetzer: unsupported grain_form=%r (valid: %s)",
        grain_form, valid_grain_forms
    )
    return ufloat(np.nan, np.nan)
```

Use `debug` level so batch analysis is unaffected. Users who want diagnostics can
set `logging.getLogger("snowpyt_mechparams").setLevel(logging.DEBUG)`.

**Files**:
- `layer_parameters/density.py`
- `layer_parameters/elastic_modulus.py`
- `layer_parameters/poissons_ratio.py`
- `layer_parameters/shear_modulus.py`
- `slab_parameters/A11.py`, `A55.py`, `B11.py`, `D11.py`

### 3.2 Split `data_structures.py`

**Problem**: `data_structures.py` is 809 lines containing three dataclasses and
complex CAAML parsing logic. The `Pit` class (~440 lines) is tightly coupled to
snowpylot's data format.

**Action**: Split into:
- `data_structures/layer.py` — `Layer` dataclass
- `data_structures/slab.py` — `Slab` dataclass
- `data_structures/pit.py` — `Pit` dataclass with all parsing/creation logic

Update `data_structures/__init__.py` to re-export everything so external imports
are unchanged.

**Files**:
- `data_structures/layer.py` (new)
- `data_structures/slab.py` (new)
- `data_structures/pit.py` (new)
- `data_structures/data_structures.py` (delete after migration)
- `data_structures/__init__.py` (update imports)

### 3.3 Consider enum-based method registration (optional / future)

**Problem**: Method names are bare strings everywhere. A typo like `"bergeld"` in
`definitions.py` silently creates a broken graph edge that only fails at runtime.

**Action** (evaluate feasibility, don't necessarily implement):
- Define a `MethodName` enum (or per-parameter enums) so misspellings are caught
  at import time.
- Alternatively, add a `graph.validate()` method that checks every method edge has
  a corresponding dispatcher registration, and call it in `__init__.py` or in tests.

The lighter-weight option (validation function + test) is probably better for this
codebase. The full enum approach would touch too many files for the benefit.

**Files**:
- `graph/structures.py` (add `validate()`)
- `tests/test_graph.py` (add validation test)

---

## Sequencing

| Phase | Effort | Risk | Prerequisite |
|-------|--------|------|-------------|
| 1.1 Numerical validation tests | Medium | Low | None |
| 1.2 Fix `include_method_uncertainty` | Small | Medium (changes output values) | 1.1 (tests catch regressions) |
| 1.3 Kim-Jamieson RG SE investigation | Small | Medium | Paper access |
| 1.4 Unbound variable fix | Trivial | None | None |
| 2.1 Slab parameter refactor | Medium | Low (pure refactor) | 1.1 (tests verify no regression) |
| 2.2 `__init__.py` for `layer_parameters` | Trivial | None | None |
| 2.3 Minor cleanup | Trivial | None | None |
| 3.1 Logging for NaN returns | Small | None | None |
| 3.2 Split `data_structures.py` | Medium | Low (import-only changes) | None |
| 3.3 Method name validation | Small | None | None |

Start with **1.4** and **2.2** (trivial, no risk), then **1.1** (tests), then the
rest of Phase 1, then Phases 2 and 3 in order.
