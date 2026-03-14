# WEAC Skier Criterion Integration — Progress Log

**Project:** SnowPyt-MechParams
**Feature:** WEAC coupled skier stability criterion
**Plan document:** `docs/2026-03-11-weac-skier-criterion-adapter.plan.md`
**Started:** 2026-03-11 (previous session)
**Last updated:** 2026-03-12

---

## Summary

This document tracks the implementation of the WEAC (Weak Layer Anticrack Nucleation
Criterion) skier stability criterion adapter for SnowPyt-MechParams.  The integration
adds a full pipeline from snow pit observations → weak-layer fracture parameters →
WEAC stability criterion, hooked into the existing graph-based parameterization engine.

---

## Phase 1 — Bug Fixes  ✅ COMPLETE

**Goal:** Fix three pre-existing bugs discovered during code review.

### Files Modified

| File | Change |
|------|--------|
| `stability_models/__init__.py` | Fixed broken import: `models.static_load` → `stability_models.static_load` |
| `weak_layer_parameters/sigma_c_plus.py` | Fixed `rho_ice` → `RHO_ICE` (line 140) |
| `weak_layer_parameters/sigma_c_minus.py` | Fixed `rho_ice` → `RHO_ICE` (line 215) |

### Decisions

- Both sigma files had identical bugs — same constant was referenced by incorrect lower-case name.
- The `stability_models/__init__.py` import path bug would have caused `ImportError` on any
  use of `calculate_static_load`, masking all downstream tests.

---

## Phase 2 — WeakLayer Data Structure  ✅ COMPLETE

**Goal:** Add a SnowPyt-side `WeakLayer` dataclass to hold fracture/strength parameters
computed by the engine, separate from the WEAC `WeakLayer` Pydantic model.

### Files Modified / Created

| File | Change |
|------|--------|
| `data_structures/weak_layer.py` | **Created** — new `WeakLayer` dataclass |
| `data_structures/__init__.py` | Added `WeakLayer` import and export |
| `data_structures/slab.py` | Added `weac_layer: Optional[WeakLayer]` field |

### WeakLayer dataclass

```python
@dataclass
class WeakLayer:
    G_c:        Optional[UncertainValue] = None   # J/m²  (WEAC default 1.0)
    G_Ic:       Optional[UncertainValue] = None   # J/m²  (WEAC default 0.56)
    G_IIc:      Optional[UncertainValue] = None   # J/m²  (WEAC default 0.79)
    sigma_c:    Optional[UncertainValue] = None   # kPa   (WEAC default 6.16)
    tau_c:      Optional[UncertainValue] = None   # kPa   (WEAC default 5.09)
    sigma_comp: Optional[UncertainValue] = None   # kPa   (WEAC default 2.6)
```

### Decisions

- Kept distinct from `weac.components.WeakLayer` (Pydantic, plain floats) to preserve
  `UncertainValue` (ufloat) semantics up to the WEAC adapter boundary.
- `WeakLayer` is a plain Python dataclass, not frozen, so the executor can populate
  fields incrementally as the pathway runs.

---

## Phase 3 — Weak-Layer Parameter Modules  ✅ COMPLETE

**Goal:** Implement the six weak-layer fracture/strength calculation functions using
the Weißgraeber & Rosendahl (2023) reference constants.

### Files Modified / Created

| File | Change |
|------|--------|
| `weak_layer_parameters/Gc.py` | Implemented stub: `calculate_Gc` + `weissgraeber_rosendahl` method → `ufloat(1.0, 0.0)` J/m² |
| `weak_layer_parameters/G_Ic.py` | **Created** — `calculate_G_Ic` → `ufloat(0.56, 0.0)` J/m² |
| `weak_layer_parameters/G_IIc.py` | **Created** — `calculate_G_IIc` → `ufloat(0.79, 0.0)` J/m² |
| `weak_layer_parameters/tau_c.py` | **Created** — `calculate_tau_c` → `ufloat(5.09, 0.0)` J/m² |
| `weak_layer_parameters/sigma_c_plus.py` | Added `weissgraeber_rosendahl` method → `ufloat(6.16, 0.0)` kPa |
| `weak_layer_parameters/sigma_c_minus.py` | Added `weissgraeber_rosendahl` method → `ufloat(2.6, 0.0)` kPa |
| `weak_layer_parameters/__init__.py` | Added exports for all six functions |

### Reference Constants (Weißgraeber & Rosendahl 2023)

| Parameter | Value | Unit | WEAC built-in default |
|-----------|-------|------|----------------------|
| G_c | 1.0 | J/m² | ✓ matches |
| G_Ic | 0.56 | J/m² | ✓ matches |
| G_IIc | 0.79 | J/m² | ✓ matches |
| sigma_c | 6.16 | kPa | ✓ matches |
| tau_c | 5.09 | kPa | ✓ matches |
| sigma_comp | 2.6 | kPa | ✓ matches |

### Decisions

- All six values are exact matches to WEAC's built-in defaults, providing a
  self-consistent baseline.  Users can override via `slab.weac_layer` direct
  assignment or `**weak_layer_overrides` in `calculate_weac_skier()`.
- All return `ufloat(value, 0.0)` — zero uncertainty since these are point
  estimates from the literature (no published uncertainty bounds).
- `sigma_c` (tensile) maps to `sigma_c_plus`; `sigma_comp` (compressive) maps
  to `sigma_c_minus`.

---

## Phase 4 — Graph Extension  ✅ COMPLETE

**Goal:** Extend the parameter dependency graph with weak-layer and stability nodes.

### Files Modified

| File | Change |
|------|--------|
| `graph/structures.py` | Extended `NodeLevel` type; added `weak_layer_params` and `stability_params` properties to `Graph` |
| `graph/definitions.py` | Added 6 weak-layer nodes, `g_delta` stability node, `merge_weac_inputs` merge node, 16 new edges, `WEAK_LAYER_PARAMS` and `STABILITY_PARAMS` frozensets |

### New Graph Topology

```
snow_pit ──weissgraeber_rosendahl──► G_c ──────────────────────────────┐
snow_pit ──weissgraeber_rosendahl──► G_Ic ─────────────────────────────┤
snow_pit ──weissgraeber_rosendahl──► G_IIc ────────────────────────────┤
snow_pit ──weissgraeber_rosendahl──► sigma_c ──────────────────────────┤
snow_pit ──weissgraeber_rosendahl──► tau_c ─────────────────────────────► merge_weac_inputs ──weac_skier──► g_delta
snow_pit ──weissgraeber_rosendahl──► sigma_comp ───────────────────────┤
density ──────────────────────────────────────────────────────────────┤
elastic_modulus ───────────────────────────────────────────────────────┤
poissons_ratio ────────────────────────────────────────────────────────┤
shear_modulus ─────────────────────────────────────────────────────────┘
```

### New Exported Symbols

- `WEAK_LAYER_PARAMS: FrozenSet[str]` — `{"G_c", "G_Ic", "G_IIc", "sigma_c", "tau_c", "sigma_comp"}`
- `STABILITY_PARAMS: FrozenSet[str]` — `{"g_delta"}`

### Decisions

- `merge_weac_inputs` aggregates all 10 prerequisites (4 slab mechanical + 6 weak-layer
  fracture/strength).  This single merge node drives `find_parameterizations` to enumerate
  all combinations of layer-param methods with the single weak-layer constant method.
- `NodeLevel` extended from `Optional[Literal["layer", "slab"]]` to include
  `"weak_layer"` and `"stability_model"`.
- `WEAK_LAYER_PARAMS` and `STABILITY_PARAMS` frozensets allow the executor to
  quickly classify targets without walking the graph.

---

## Phase 5 — WEAC Adapter  ✅ COMPLETE

**Goal:** Create the SnowPyt → WEAC boundary adapter that converts `Slab` inputs
into WEAC API calls and returns a structured `WeacSkierResult`.

### Files Created / Modified

| File | Change |
|------|--------|
| `stability_models/weac/weac_result.py` | **Created** — `WeacSkierResult` dataclass |
| `stability_models/weac/weac_criterion.py` | **Created** — `calculate_weac_skier()` adapter |
| `stability_models/__init__.py` | Added `WeacSkierResult` and `calculate_weac_skier` exports |

### `WeacSkierResult` fields

```python
@dataclass
class WeacSkierResult:
    g_delta:              float   # dimensionless — primary stability metric
    converged:            bool
    G_I:                  float   # J/m² — mode-I ERR at critical point
    G_II:                 float   # J/m² — mode-II ERR at critical point
    G_total:              float   # J/m² — total ERR at critical point
    critical_skier_weight: float  # N
    crack_length:         float   # mm
    max_dist_stress:      float   # kPa
    min_dist_stress:      float   # kPa
    dist_ERR_envelope:    float   # J/m²
    segment_length:       float   # mm
    skier_mass:           float   # kg
```

### Key adapter logic

```python
# CRITICAL: method name is evaluate_coupled_criterion, NOT coupled_criterion
evaluator = CriteriaEvaluator(CriteriaConfig())
result = evaluator.evaluate_coupled_criterion(system)

# G_I/G_II extraction: incremental_ERR returns [G_total, G_I, G_II, 0]
analyzer = Analyzer(result.final_system)
arr = analyzer.incremental_ERR(unit="J/m^2")
G_total = float(arr[0])
G_I     = float(arr[1])
G_II    = float(arr[2])
```

### Decisions

- **Lazy WEAC import**: `_WEAC_AVAILABLE` flag set at module load; `ImportError` with install
  instructions raised only at call time.  The module is importable even without weac installed.
- **UFloat stripping**: `_nominal(v)` helper converts all `UncertainValue` inputs to plain
  `float` at the adapter boundary.  WEAC's eigensystem solver (scipy.linalg.eig) is incompatible
  with `uncertainties.UFloat`.
- **Unit conversion**: SnowPyt uses cm for thickness; WEAC uses mm.  `×10` applied to all
  layer and weak-layer thicknesses.
- **Segment layout**: Two segments of equal length L (default: `slab.total_thickness × 10 mm`).
  First segment carries the skier mass; second carries zero (unloaded).
- **Weak-layer density fallback**: Tries `density_measured` first, then `density_calculated`.

---

## Phase 6 — pyproject.toml Update  ✅ COMPLETE

### Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Added `[project.optional-dependencies] weac = ["weac>=3.1.4"]` |
| `pyproject.toml` | Added `"weac.*"` to mypy `ignore_missing_imports` overrides |

### Install commands

```bash
# Core only (no WEAC)
pip install snowpyt-mechparams

# With WEAC stability criterion
pip install "snowpyt-mechparams[weac]"
```

---

## Phase 7 — Dispatcher & Executor Extension  ✅ COMPLETE

**Goal:** Wire the new weak-layer and stability methods into the execution engine.

### Files Modified

| File | Change |
|------|--------|
| `execution/dispatcher.py` | Added `WEAK_LAYER` + `STABILITY` enum values; imported 6 weak-layer functions + `calculate_weac_skier`; registered 7 new `MethodSpec` entries; updated `execute()` return type to `Optional[Any]` |
| `execution/executor.py` | Imported `WEAK_LAYER_PARAMS`, `STABILITY_PARAMS`, `WeakLayer`; added WEAK_LAYER and STABILITY execution blocks; added `_execute_weak_layer_calculations()` and `_execute_stability_calculations()` methods |
| `data_structures/slab.py` | Added `weac_result: Optional["WeacSkierResult"] = None` field |

### New ParameterLevel values

```python
class ParameterLevel(Enum):
    LAYER     = "layer"
    SLAB      = "slab"
    WEAK_LAYER  = "weak_layer"      # NEW
    STABILITY   = "stability_model" # NEW
```

### Execution flow for `target_parameter = "g_delta"`

```
execute_parameterization()
  1. Per-layer loop → compute density, E, ν, G for each slab layer
  2. WEAK_LAYER block → compute G_c, G_Ic, G_IIc, sigma_c, tau_c, sigma_comp
                        → populate slab.weac_layer
  3. STABILITY block  → call calculate_weac_skier(slab)
                        → store WeacSkierResult on slab.weac_result
                        → trace records g_delta float
```

### Decisions

- **WEAK_LAYER functions accept `slab` arg** for API consistency with SLAB methods, even
  though they don't use it (constant reference values).
- **`execute()` return type** widened from `Optional[UncertainValue]` to `Optional[Any]`
  because stability methods return `WeacSkierResult`, not a scalar.
- **`WeacSkierResult` stored on slab** as `slab.weac_result` so callers can access all
  fields (G_I, G_II, crack_length, etc.) from the `PathwayResult.slab`.
- **`ComputationTrace.output`** for stability contains `g_delta` float (the primary scalar
  metric) rather than the full `WeacSkierResult` object — keeps traces human-readable.
- **Circular import prevention**: `slab.py` imports `WeacSkierResult` under `TYPE_CHECKING`
  guard only, avoiding the `data_structures → stability_models → data_structures` cycle.
- **`slab.weac_layer` lazy init**: If `weac_layer` is None when weak-layer calcs run,
  a new `WeakLayer()` is created automatically.  This allows the engine to populate it
  incrementally without requiring the caller to pre-initialise it.

---

## Phase 8 — Tests  ✅ COMPLETE

**Goal:** Write unit and integration tests covering the new WEAC criterion adapter and
engine extensions.

### Files Created

| File | Contents |
|------|----------|
| `tests/test_weac_criterion.py` | 28 test items: `_nominal` helper, input validation, dataclass structure, integration tests |
| `tests/test_weak_layer_engine.py` | 28 test items: `ParameterLevel` enum, dispatcher registration, executor weak-layer/stability flow, full pipeline |

### Test Results

```
39 passed, 17 skipped (weac not installed), 0 new failures
```

All skipped tests are guarded by `requires_weac = pytest.mark.skipif(not _WEAC_AVAILABLE, ...)`.

### Test Coverage

| Test Class | Tests | Notes |
|------------|-------|-------|
| `TestNominalHelper` | 6 | None, UFloat, float, int, zero, negative |
| `TestCalculateWeacSkierValidation` | 7 | angle=None, no weak_layer, missing density/thickness/E/G |
| `TestWeacSkierResultStructure` | 2 | construction, g_delta threshold property |
| `TestCalculateWeacSkierIntegration` | 13 (skip) | Full WEAC calls: return type, g_delta finite, G_I+G_II≈G_total, overrides |
| `TestParameterLevel` | 3 | WEAK_LAYER + STABILITY enum values exist |
| `TestDispatcherWeakLayerMethods` | 7 | All 6 WEAK_LAYER + 1 STABILITY MethodSpec registered |
| `TestDispatcherExecuteWeakLayer` | 8 | Return values match reference constants |
| `TestExecutorWeakLayerCalculations` | 6 | Lazy weac_layer creation, all 6 params populated |
| `TestFullPipelineStability` | 4 (skip) | find_parameterizations → execute → g_delta in trace |

### Pre-existing Failures (not caused by this work)

`tests/test_elastic_modulus_methods.py::TestWautierNumerical` — 2 failures, values ~10× off.
Confirmed via `git stash` test run: failures existed before any changes.

---

## Phase 8a — Bug Fix: Validation Order in weac_criterion.py  ✅ COMPLETE

**Discovered during:** Phase 8 first test run (7 failures in `TestCalculateWeacSkierValidation`)

### Problem

`calculate_weac_skier()` raised `ImportError` before checking for missing inputs:

```python
# BEFORE (broken order):
if not _WEAC_AVAILABLE:
    raise ImportError("The 'weac' package is required...")

# 1. Validate required inputs
phi = _nominal(slab.angle)
if phi is None:
    return None
```

With weac not installed, all validation-path tests received `ImportError` instead of `None`.

### Fix

Moved the availability guard to section `1b` — after all input validation:

```python
# AFTER (correct order):
# 1. Validate required inputs
phi = _nominal(slab.angle)
if phi is None:
    return None
# ... all other validation ...
weac_layers.append(WeacLayer(rho=rho, h=h_mm, E=E, G=G, nu=nu))

# 1b. WEAC availability check (deferred until after input validation)
if not _WEAC_AVAILABLE:
    raise ImportError("The 'weac' package is required...")
```

### Behaviour After Fix

| Inputs | weac installed? | Result |
|--------|----------------|--------|
| Missing / invalid | Either | `return None` |
| Valid | Yes | `WeacSkierResult` |
| Valid | No | `ImportError` with install instructions |

### File Modified

| File | Change |
|------|--------|
| `stability_models/weac/weac_criterion.py` | Moved `if not _WEAC_AVAILABLE` block from function top to section 1b |

---

## Phase 9 — Example Notebook  ✅ COMPLETE

**Goal:** Create a runnable Jupyter notebook demonstrating the full WEAC pipeline.

### File Created

| File | Description |
|------|-------------|
| `examples/weac_skier_all_pathways.ipynb` | 9-section notebook with synthetic and real-data examples |

### Notebook Sections

1. **Setup & Imports** — install instructions, `_WEAC_AVAILABLE` guard
2. **Graph Inspection** — `WEAK_LAYER_PARAMS`, `STABILITY_PARAMS`, node counts
3. **Build a Synthetic Slab** — 3-layer slab with weak layer
4. **Run `calculate_weac_skier` Directly** — single direct API call
5. **Inspect `WeacSkierResult`** — all 12 fields, g_delta interpretation
6. **Find All Pathways to g_delta** — `find_parameterizations(pit, "g_delta")`
7. **Run the Execution Engine** — `PathwayExecutor`, trace table output
8. **Real Dataset: ECTP Slabs** — load from CSV, batch processing
9. **g_delta Distribution by Pathway** — histogram / violin plot

All cells have `execution_count: null`; intended to be run by user with `weac` installed.

---

## Final Summary

All planned implementation phases completed successfully.

| Phase | Description | Status | Files Changed/Created |
|-------|-------------|--------|-----------------------|
| 1 | Bug fixes | ✅ | 3 modified |
| 2 | WeakLayer data structure | ✅ | 3 modified/created |
| 3 | Weak-layer parameter modules | ✅ | 7 modified/created |
| 4 | Graph extension | ✅ | 2 modified |
| 5 | WEAC adapter | ✅ | 3 created, 1 modified |
| 6 | pyproject.toml | ✅ | 1 modified |
| 7 | Dispatcher & executor | ✅ | 3 modified |
| 8 | Tests | ✅ | 2 created |
| 8a | Validation-order bug fix | ✅ | 1 modified |
| 9 | Example notebook | ✅ | 1 created |

**Test results:** 39 passed, 17 skipped (weac not installed), 0 new failures

**New public API surface:**
- `snowpyt_mechparams.stability_models.WeacSkierResult`
- `snowpyt_mechparams.stability_models.calculate_weac_skier`
- `snowpyt_mechparams.data_structures.WeakLayer`
- `Slab.weac_layer`, `Slab.weac_result` fields
- `WEAK_LAYER_PARAMS`, `STABILITY_PARAMS` frozensets
- `ParameterLevel.WEAK_LAYER`, `ParameterLevel.STABILITY` enum values

---

## Architecture Summary

```
SnowPyt Slab
    │
    ├── slab.layers[]         (Layer objects with density, E, ν, G)
    ├── slab.weak_layer       (measured Layer: rho, h for WEAC WeakLayer)
    ├── slab.weac_layer       (WeakLayer dataclass: G_c, G_Ic, … — from engine)
    └── slab.weac_result      (WeacSkierResult — from calculate_weac_skier)

graph
    └── g_delta node (stability_model)
            ← merge_weac_inputs (merge)
                    ← density, elastic_modulus, poissons_ratio, shear_modulus
                    ← G_c, G_Ic, G_IIc, sigma_c, tau_c, sigma_comp

execution engine
    PathwayExecutor.execute_parameterization(pathway, slab, "g_delta")
        1. Per-layer: density/E/ν/G via layer methods
        2. _execute_weak_layer_calculations → slab.weac_layer
        3. _execute_stability_calculations  → slab.weac_result
```
