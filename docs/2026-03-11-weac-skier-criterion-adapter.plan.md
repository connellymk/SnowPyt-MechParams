# WEAC Skier Criterion Adapter & Pathway Example Notebook

**Date:** 2026-03-11
**Feature Group:** stability_models / examples
**Author:** Claude (claude-sonnet-4-6)

---

## Overview

Integrate WEAC's skier stability criterion into SnowPyt-MechParams via an adapter module that
converts `Slab` objects to WEAC inputs without modifying either library. `g_delta` is added as
a first-class graph node at a new `"stability_model"` level, so `find_parameterizations` can
naturally discover all calculation pathways to it. The deliverable is a companion example
notebook (`weac_skier_all_pathways.ipynb`) that mirrors `all_D11_pathways.ipynb` — running
every pathway the graph can produce through the WEAC skier criterion and visualising `g_delta`
distributions and slab coverage per pathway.

---

## Pre-implementation Decision: Pydantic Refactor of Data Structures

**Question:** Should `data_structures/` (`Layer`, `Slab`, `Pit`) be migrated from dataclasses
to Pydantic `BaseModel` before building the WEAC adapter?

**Recommendation: No. Defer the Pydantic migration.**

The core blocker is `uncertainties.UFloat`. SnowPyt's entire value proposition is uncertainty
propagation; every calculated field stores a `UFloat`. Pydantic would require:

1. **Custom validators for `UFloat`** — Pydantic has no built-in concept of `UFloat`. An
   `Annotated` wrapper or `custom_type_validator` would be needed for every field that can
   hold one. This is significant boilerplate with no scientific benefit.

2. **All `dataclasses.replace()` calls become `model.model_copy(update={})`** — the executor
   uses `replace(layer)` and `replace(slab, layers=result_layers)` throughout `executor.py`.
   Every call site would need updating.

3. **Mutation pattern must change** — `_set_layer_parameter` writes `layer.density_calculated =
   value` directly. With Pydantic this requires `ConfigDict(frozen=False)` (losing immutability
   guarantees) or switching to `model_copy` everywhere.

4. **Properties become `@computed_field`** — `Layer.depth_bottom`, `hand_hardness_index`,
   `main_grain_form` all use `@property`. Pydantic v2 requires `@computed_field`, changing the
   decorator and adding imports.

5. **No existing Pydantic usage in SnowPyt** — WEAC uses Pydantic for its own plain-`float`
   input validation. SnowPyt is a fundamentally different library (mutable, UFloat-typed). The
   migration is large, orthogonal to the WEAC adapter goal, and carries real regression risk.

**What the Pydantic refactor would gain:** construction-time validation (e.g., `thickness > 0`)
and JSON schema generation. These benefits can be achieved incrementally with `__post_init__`
validators in the existing dataclass structure without a full migration.

**Decision recorded:** Keep dataclasses. Track the Pydantic migration as separate technical debt.

---

## Scope

**In Scope:**

**Bugs (blockers):**
- `stability_models/__init__.py`: broken `models.static_load` import path
- `sigma_c_plus.py`, `sigma_c_minus.py`: undefined `rho_ice` name

**Data structures:**
- New `data_structures/weak_layer.py` — SnowPyt `WeakLayer` dataclass (6 fracture/strength fields)
- `data_structures/slab.py` — add `weac_layer: Optional[WeakLayer] = None` field

**Weak layer parameter modules (6 files):**
- Implement stub `weak_layer_parameters/Gc.py`; create `G_Ic.py`, `G_IIc.py`, `tau_c.py`
- Add `weissgraeber_rosendahl` method to `sigma_c_plus.py` and `sigma_c_minus.py`

**Graph — two new levels (seven-file extension):**
- `graph/structures.py`: add `"weak_layer"` and `"stability_model"` to `NodeLevel`; add
  `weak_layer_params` and `stability_params` properties to `Graph`
- `graph/definitions.py`: add 6 `weak_layer` nodes, `g_delta` stability node,
  `merge_weac_inputs` merge node, 7 method edges, `WEAK_LAYER_PARAMS` and `STABILITY_PARAMS`

**Execution engine:**
- `execution/dispatcher.py`: add `ParameterLevel.WEAK_LAYER` and `ParameterLevel.STABILITY`;
  register 6 weak-layer `MethodSpec` entries + 1 `("g_delta", "weac_skier")` entry
- `execution/executor.py`: add `WEAK_LAYER_PARAMS` branch, `STABILITY_PARAMS` branch,
  `_execute_weak_layer_calculations`, `_execute_stability_calculations`

**WEAC adapter:**
- `stability_models/weac/weac_result.py` — `WeacSkierResult` dataclass
- `stability_models/weac/weac_criterion.py` — `calculate_weac_skier` adapter function
- `stability_models/__init__.py` — add WEAC exports (also fixes import bug)

**Dependency management:**
- `pyproject.toml`: `requires-python = ">=3.12"`, `[project.optional-dependencies] weac`

**Tests:**
- `tests/test_weac_criterion.py` (17 unit + 7 integration)
- `tests/test_weak_layer_engine.py` (4 graph/engine tests)

**Example notebook:**
- `examples/weac_skier_all_pathways.ipynb`

**Out of Scope:**
- Pydantic migration of data structures (deferred, see above)
- PST scenario (requires `slab.pit.PST_results` integration)
- Monte Carlo uncertainty propagation through WEAC
- Any modification to the WEAC library itself

---

## Related Documentation

- [`docs/weac_adapter_plan.md`](weac_adapter_plan.md) — authoritative design spec (read this first)
- [`docs/execution_engine.md`](execution_engine.md) — execution engine architecture
- [`docs/parameter_graph.md`](parameter_graph.md) — graph node/edge conventions
- [`examples/all_D11_pathways.ipynb`](../examples/all_D11_pathways.ipynb) — structural template

---

## Python Package Changes

### Data Structures

**New file: `data_structures/weak_layer.py`**

SnowPyt's `WeakLayer` dataclass holding the six fracture/strength parameters WEAC needs.
All fields default to `None`; the adapter uses WEAC's own defaults for any `None` field.
Distinct from `weac.components.WeakLayer` (a Pydantic `BaseModel` with many more fields).

```python
@dataclass
class WeakLayer:
    G_c: Optional[UncertainValue] = None       # 1.0   J/m²  (WEAC default)
    G_Ic: Optional[UncertainValue] = None      # 0.56  J/m²
    G_IIc: Optional[UncertainValue] = None     # 0.79  J/m²
    sigma_c: Optional[UncertainValue] = None   # 6.16  kPa
    tau_c: Optional[UncertainValue] = None     # 5.09  kPa
    sigma_comp: Optional[UncertainValue] = None  # 2.6 kPa
```

**Modified: `data_structures/__init__.py`** — add `WeakLayer` to exports.

**Modified: `data_structures/slab.py`** — add `weac_layer: Optional[WeakLayer] = None`
after the existing `weak_layer` field.

### Weak Layer Parameter Modules

Three new files, three modified files. All follow the existing `calculate_{param}(method,
**kwargs)` dispatcher pattern. The `weissgraeber_rosendahl` method returns a constant
`ufloat` (zero uncertainty) — the Weißgraeber & Rosendahl (2023) reference values that
are also WEAC's built-in defaults.

| File | Status | Parameter | `weissgraeber_rosendahl` value |
|---|---|---|---|
| `weak_layer_parameters/Gc.py` | Implement stub | Total fracture energy | `ufloat(1.0, 0.0)` J/m² |
| `weak_layer_parameters/G_Ic.py` | **New** | Mode I fracture toughness | `ufloat(0.56, 0.0)` J/m² |
| `weak_layer_parameters/G_IIc.py` | **New** | Mode II fracture toughness | `ufloat(0.79, 0.0)` J/m² |
| `weak_layer_parameters/tau_c.py` | **New** | Shear strength | `ufloat(5.09, 0.0)` kPa |
| `weak_layer_parameters/sigma_c_plus.py` | Add method + fix bug | Tensile normal strength | `ufloat(6.16, 0.0)` kPa |
| `weak_layer_parameters/sigma_c_minus.py` | Add method + fix bug | Compressive strength | `ufloat(2.6, 0.0)` kPa |

**Bug fixes:** `sigma_c_plus.py:140` and `sigma_c_minus.py:215` reference undefined `rho_ice`;
rename to `RHO_ICE` (the constant already imported at the top of each file).

### Graph & Execution Engine

The extension follows the existing five-file pattern but adds **two new node levels** in a
single pass: `"weak_layer"` (6 fracture/strength nodes) and `"stability_model"` (`g_delta`).
The executor handles these levels in order after layer-level calculations complete.

#### `graph/structures.py`

```python
# Extend NodeLevel to include both new levels:
NodeLevel = Optional[Literal["layer", "slab", "weak_layer", "stability_model"]]
```

- Update `Node.__post_init__` validator to accept both new level strings
- Add two new properties to `Graph`:
  ```python
  @property
  def weak_layer_params(self) -> FrozenSet[str]:
      return frozenset(n.parameter for n in self.nodes if n.level == "weak_layer")

  @property
  def stability_params(self) -> FrozenSet[str]:
      return frozenset(n.parameter for n in self.nodes if n.level == "stability_model")
  ```

#### `graph/definitions.py`

**Weak layer nodes** (level=`"weak_layer"`):
```python
G_c     = build_graph.param("G_c",      level="weak_layer")
G_Ic    = build_graph.param("G_Ic",     level="weak_layer")
G_IIc   = build_graph.param("G_IIc",    level="weak_layer")
sigma_c  = build_graph.param("sigma_c",  level="weak_layer")
tau_c    = build_graph.param("tau_c",    level="weak_layer")
sigma_comp = build_graph.param("sigma_comp", level="weak_layer")
```
Each has a single method edge from `snow_pit` via `"weissgraeber_rosendahl"`.

**Stability node** (level=`"stability_model"`):
```python
g_delta = build_graph.param("g_delta", level="stability_model")
```

**Merge node** — aggregates all WEAC prerequisites:
```python
merge_weac_inputs = build_graph.merge("merge_weac_inputs")
```
Incoming edges from: `density`, `elastic_modulus`, `poissons_ratio`, `shear_modulus`,
`G_c`, `G_Ic`, `G_IIc`, `sigma_c`, `tau_c`, `sigma_comp`.

```python
# Slab layer mechanical params → merge_weac_inputs
build_graph.flow(density,          merge_weac_inputs)
build_graph.flow(elastic_modulus,  merge_weac_inputs)
build_graph.flow(poissons_ratio,   merge_weac_inputs)
build_graph.flow(shear_modulus,    merge_weac_inputs)
# Weak layer fracture params → merge_weac_inputs
build_graph.flow(G_c,       merge_weac_inputs)
build_graph.flow(G_Ic,      merge_weac_inputs)
build_graph.flow(G_IIc,     merge_weac_inputs)
build_graph.flow(sigma_c,   merge_weac_inputs)
build_graph.flow(tau_c,     merge_weac_inputs)
build_graph.flow(sigma_comp, merge_weac_inputs)
# merge_weac_inputs → g_delta via weac_skier
build_graph.method_edge(merge_weac_inputs, g_delta, "weac_skier")
```

**Exports:**
```python
WEAK_LAYER_PARAMS: frozenset = graph.weak_layer_params
STABILITY_PARAMS:  frozenset = graph.stability_params
```

**Pathway count:** `find_parameterizations(graph, graph.get_node("g_delta"))` discovers all
combinations of methods for `density × elastic_modulus × poissons_ratio × shear_modulus`.
With current methods: 4 × 4 × 2 × 1 = 32. Weak-layer fracture params have only one method
each and contribute no branching. As new methods are added, the count updates automatically.

#### `execution/dispatcher.py`

```python
class ParameterLevel(Enum):
    LAYER = "layer"
    SLAB = "slab"
    WEAK_LAYER = "weak_layer"    # new
    STABILITY = "stability_model" # new
```

**6 weak-layer MethodSpec entries** — constant-value functions (lambda ignores slab arg):
```python
MethodSpec(
    parameter="G_Ic",
    method_name="weissgraeber_rosendahl",
    level=ParameterLevel.WEAK_LAYER,
    function=lambda slab: calculate_G_Ic("weissgraeber_rosendahl"),
    required_inputs=["slab"],
    optional_inputs={}
)
```

**1 stability MethodSpec** — calls the WEAC adapter:
```python
MethodSpec(
    parameter="g_delta",
    method_name="weac_skier",
    level=ParameterLevel.STABILITY,
    function=lambda slab: _dispatch_weac_skier(slab),  # wrapper with lazy import
    required_inputs=["slab"],
    optional_inputs={}
)
```
`_dispatch_weac_skier` is a module-level helper in `dispatcher.py` that lazily imports
`calculate_weac_skier` from `stability_models.weac` and raises `ImportError` with install
instructions if `weac` is not installed.

The existing `else` branch in `dispatcher.execute()` already passes `inputs = {"slab": slab}`
for all non-LAYER levels — no change to `execute()` itself.

#### `execution/executor.py`

Import `WEAK_LAYER_PARAMS` and `STABILITY_PARAMS` alongside `SLAB_PARAMS`.

**Execution order in `execute_parameterization`:**
```python
# After layer-level loop:
if target_parameter in SLAB_PARAMS:
    ...  # existing
elif target_parameter in WEAK_LAYER_PARAMS:
    wl_traces = self._execute_weak_layer_calculations(result_slab, target_parameter)
    computation_trace.extend(wl_traces)
elif target_parameter in STABILITY_PARAMS:
    stab_traces = self._execute_stability_calculations(result_slab, target_parameter)
    computation_trace.extend(stab_traces)
```

**`_execute_weak_layer_calculations(slab, target_parameter)`:**
- Computes all six weak-layer parameters in one pass via `dispatcher.execute`
- Assembles `WeakLayer(G_c=…, G_Ic=…, …)` SnowPyt dataclass
- Sets `result_slab.weac_layer = WeakLayer(…)`
- Returns 6 `ComputationTrace` entries (one per field)
- The `target_parameter` argument is used only for the success determination trace

**`_execute_stability_calculations(slab, target_parameter)`:**
- First calls `_execute_weak_layer_calculations(slab, ...)` to populate `slab.weac_layer`
  (these traces are included in the returned list)
- Then calls `dispatcher.execute("g_delta", "weac_skier", slab=slab)`
- Returns: weak-layer traces + g_delta trace
- The g_delta trace carries `output = WeacSkierResult` (the full result object);
  `output.g_delta` is the scalar the notebook extracts

**Success determination** — add parallel to SLAB_PARAMS block:
```python
elif target_parameter in STABILITY_PARAMS:
    success = any(
        t.success and t.parameter == target_parameter
        for t in computation_trace
    )
```

### Stability Models (WEAC Adapter)

**`stability_models/__init__.py`** — two changes:
1. Fix broken import: `from snowpyt_mechparams.models.static_load` →
   `from snowpyt_mechparams.stability_models.static_load`
2. Add:
   ```python
   from snowpyt_mechparams.stability_models.weac import WeacSkierResult, calculate_weac_skier
   ```

**`stability_models/weac/__init__.py`** — already complete, do not recreate.

**New: `stability_models/weac/weac_result.py`** — pure dataclass, no WEAC import required:
```python
@dataclass
class WeacSkierResult:
    g_delta: float
    converged: bool
    G_I: float                   # Mode I ERR at critical point [J/m²]
    G_II: float                  # Mode II ERR at critical point [J/m²]
    G_total: float               # G_I + G_II [J/m²]
    critical_skier_weight: float # [kg]
    crack_length: float          # [mm]
    max_dist_stress: float
    min_dist_stress: float
    dist_ERR_envelope: float
    segment_length: float        # informational [mm]
    skier_mass: float            # informational [kg]
```

**New: `stability_models/weac/weac_criterion.py`** — the adapter:
```python
def calculate_weac_skier(
    slab: Slab,
    skier_mass: float = 80.0,
    segment_length: Optional[float] = None,
    **weak_layer_overrides,
) -> Optional[WeacSkierResult]:
```

Key implementation details:
- Guard: return `None` for any missing required field on slab layers or `slab.weak_layer`
- `_nominal(v)` helper strips `UFloat` → `float`; passes through `float`; returns `None` for `None`
- Slab layers → `weac.components.Layer(rho=…, h=…, E=…, G=…, nu=…)` — strict, uses only
  SnowPyt-computed values; no fallback to WEAC's internal E/G derivation
- `slab.weak_layer` supplies `rho` and `h` for the WEAC `WeakLayer`; WEAC derives its own
  `E`, `G`, `kn`, `kt` internally from those
- Fracture/strength params read from `slab.weac_layer`; `**weak_layer_overrides` take precedence
- `L = slab.total_thickness × 10` (cm → mm) unless `segment_length` is provided explicitly
- Two segments: `[Segment(L, has_foundation=True, m=skier_mass), Segment(L, …, m=0)]`
- WEAC call sequence: `ModelInput(…)` → `SystemModel(model_input)` → `CriteriaEvaluator(…)`
  → `result = evaluator.coupled_criterion(…)`

**G_I / G_II extraction — confirmed from source:**

`Analyzer.incremental_ERR(unit="J/m^2")` at `weac/analysis/analyzer.py:647` returns:
```python
np.array([Ginc1 + Ginc2, Ginc1, Ginc2, 0]).flatten() * convert[unit]
#  index:       0              1       2    3
#  meaning:  G_total          G_I    G_II  (placeholder zero)
```
`G_I = arr[1]`, `G_II = arr[2]`, `G_total = arr[0]`.

`CoupledCriterionResult` does not carry G_I / G_II directly. After calling
`evaluator.coupled_criterion(…)`, extract them by:
```python
analyzer = Analyzer(result.final_system)
arr = analyzer.incremental_ERR(unit="J/m^2")
G_I, G_II, G_total = arr[1], arr[2], arr[0]
```
`result.final_system` is already configured at the critical crack length and critical skier
weight, so re-calling `incremental_ERR` reproduces the convergence-point ERR values.

### Dependency Management

```toml
[project]
requires-python = ">=3.12"

[project.optional-dependencies]
weac = ["weac>=3.1.4"]
```

---

## Example Notebook

**New file: `examples/weac_skier_all_pathways.ipynb`**

Mirrors `all_D11_pathways.ipynb` in structure and visual style.
Target parameter: `g_delta` (WEAC coupled criterion, ≥ 1.0 = unstable).

### Design decisions (all resolved)

| Question | Decision |
|---|---|
| Pathway enumeration | `find_parameterizations(graph, graph.get_node("g_delta"))` |
| Weak layer definition | `weak_layer_def="ECTP_failure_layer"` |
| Slab filter | All required parameters must be present (not just weak_layer ≠ None) |
| Skier mass | Fixed: `80.0 kg` |
| Slab count cap | No cap — add a small-sample test cell before the full-run cell |
| G_I / G_II indexing | Confirmed: `incremental_ERR()[0]` = G_total, `[1]` = G_I, `[2]` = G_II |
| Weak-layer mechanical params | WEAC derives E/G internally from `rho` and `h`; SnowPyt does not pre-compute them |

### Notebook Structure

```
Section 1 — Load Snow Pit Data
    parse_caaml_directory + Pit.from_snow_pit
    (identical to all_D11_pathways.ipynb)

Section 2 — Find All WEAC Calculation Pathways
    pathways = find_parameterizations(graph, graph.get_node("g_delta"))
    The graph traversal backward from g_delta → merge_weac_inputs discovers all method
    combinations for density × elastic_modulus × poissons_ratio × shear_modulus.
    Weak-layer fracture params (G_c, G_Ic, …) have exactly one method each and add no branching.
    Print count and list all pathways with their method fingerprints.

Section 3 — Create ECTP Slabs
    ectp_slabs = [
        slab for pit in pits
        for slab in pit.create_slabs(weak_layer_def="ECTP_failure_layer")
        if slab.weak_layer is not None
    ]
    Note: further filtering (only slabs with all required params) happens naturally at
    execution time — pathways that fail to compute any required field return success=False.

Section 4 — Small-Sample Test Run  [*** run this before Section 5 ***]
    N = 50
    test_slabs = random.sample(ectp_slabs, N)
    Run the full pipeline (Sections 5's loop) on test_slabs only.
    Confirm: g_delta traces are present and finite, no import errors, converged fraction > 0.

Section 5 — Execute All Pathways (full dataset)
    engine = ExecutionEngine(graph)
    config = ExecutionConfig(include_method_uncertainty=False)
    For each slab × pathway:
      result = engine.execute_parameterization(slab, pathway, target="g_delta", config=config)
      # The engine internally:
      #   1. Computes layer mechanical params (density, E, ν, G) on slab layers
      #   2. Computes weak layer fracture params (G_c, G_Ic, …), populates slab.weac_layer
      #   3. Calls calculate_weac_skier(result_slab) via dispatcher
      # Extract from result's computation_trace:
      g_delta_trace = next(t for t in result.computation_trace if t.parameter == "g_delta")
      weac_result: WeacSkierResult = g_delta_trace.output  # if success
    Record per-pathway: g_delta, converged, G_I, G_II, critical_skier_weight, crack_length,
    attrition counts at each step (density → E → ν → G → weak_layer → g_delta)

Section 6 — Coverage Table
    Per-pathway: slabs / total_slabs, % success, avg g_delta, % converged,
    avg critical_skier_weight, avg crack_length.
    Sorted by slab coverage descending.

Section 7 — Sankey Diagram (best-coverage pathway)
    Attrition chain: all slabs → density → E-mod → ν → G → weak_layer_params → g_delta
    Same node/colour scheme as all_D11_pathways.ipynb.
    Add "WEAC not converged" node if any non-converged solutions.

Section 8 — g_delta Distribution by Pathway
    Horizontal violin plots.
    x-axis: g_delta, linear scale (~0–5).
    Vertical dashed line at g_delta = 1.0 (instability threshold).
    Colour by density method (same DENSITY_COLORS dict as D11 notebook).
    Ordered top-to-bottom by slab coverage.

Section 9 — Convergence & Physical Outputs
    Bar chart: fraction converged per pathway.
    Scatter: g_delta vs critical_skier_weight, coloured by converged flag.
    Scatter: G_I vs G_II at critical point (ERR mode decomposition).
```

---

## Implementation Steps

1. **Fix pre-existing bugs** (blockers — do first)
   - `stability_models/__init__.py`: `models.static_load` → `stability_models.static_load`
   - `sigma_c_plus.py:140`: `rho_ice` → `RHO_ICE`
   - `sigma_c_minus.py:215`: `rho_ice` → `RHO_ICE`
   - Files: 3

2. **Create `data_structures/weak_layer.py`** and update `__init__.py`
   - New SnowPyt `WeakLayer` dataclass (6 optional UFloat fields)
   - Files: 2

3. **Update `data_structures/slab.py`**
   - Add `weac_layer: Optional[WeakLayer] = None` field
   - Files: 1 | Depends on: Step 2

4. **Implement weak layer parameter modules**
   - Implement `Gc.py` stub; create `G_Ic.py`, `G_IIc.py`, `tau_c.py`
   - Add `weissgraeber_rosendahl` to `sigma_c_plus.py` and `sigma_c_minus.py`
   - Files: 6 | Note: bug fixes in those sigma files done in Step 1

5. **Extend `graph/structures.py`**
   - Add `"weak_layer"` and `"stability_model"` to `NodeLevel` and validator
   - Add `weak_layer_params` and `stability_params` properties to `Graph`
   - Files: 1

6. **Extend `graph/definitions.py`**
   - Add 6 `weak_layer` nodes + method edges
   - Add `g_delta` stability node, `merge_weac_inputs` merge node, all flow edges, method edge
   - Export `WEAK_LAYER_PARAMS` and `STABILITY_PARAMS` frozensets; update `__all__`
   - Files: 1 | Depends on: Step 5

7. **Extend `execution/dispatcher.py`**
   - Add `ParameterLevel.WEAK_LAYER` and `ParameterLevel.STABILITY`
   - Register 6 weak-layer `MethodSpec` entries
   - Register `("g_delta", "weac_skier")` `MethodSpec` with `_dispatch_weac_skier` helper
   - Files: 1 | Depends on: Steps 4, 6, 9 (for `_dispatch_weac_skier` import target)

8. **Extend `execution/executor.py`**
   - Import `WEAK_LAYER_PARAMS`, `STABILITY_PARAMS`
   - Add `WEAK_LAYER_PARAMS` and `STABILITY_PARAMS` branches in `execute_parameterization`
   - Add success determination for both new levels
   - Implement `_execute_weak_layer_calculations` and `_execute_stability_calculations`
   - Files: 1 | Depends on: Steps 2, 3, 7

9. **Create WEAC adapter stability model files**
   - `stability_models/weac/weac_result.py` — `WeacSkierResult` dataclass
   - `stability_models/weac/weac_criterion.py` — `_nominal`, helpers, `calculate_weac_skier`
   - Update `stability_models/__init__.py` (static_load bug already fixed in Step 1)
   - Files: 3 | Depends on: Steps 2, 3

10. **Update `pyproject.toml`**
    - `requires-python = ">=3.12"`, add `weac` optional dependency group
    - Files: 1

11. **Write tests**
    - `tests/test_weac_criterion.py`: 17 unit + 7 integration tests
    - `tests/test_weak_layer_engine.py`: 4 graph/engine tests + 2 g_delta graph tests
    - Files: 2 | Depends on: Steps 8, 9

12. **Build example notebook**
    - `examples/weac_skier_all_pathways.ipynb`: Sections 1–9
    - Files: 1 | Depends on: Steps 8, 9, 11

**Note on Step 7 / Step 9 ordering:** The `_dispatch_weac_skier` helper in `dispatcher.py`
lazily imports `calculate_weac_skier` at call time, not at module load time. Steps 7 and 9
can therefore be developed in parallel — the dispatcher just needs the import path to be correct,
not the module to exist yet during development.

---

## Parallel Work Streams

### Stream 1: Bug Fixes (start immediately)
- **Steps:** 1
- **Files:** `stability_models/__init__.py`, `sigma_c_plus.py`, `sigma_c_minus.py`

### Stream 2: Data Structures (start immediately)
- **Steps:** 2 → 3 (sequential within stream)
- **Files:** `data_structures/weak_layer.py`, `data_structures/__init__.py`, `data_structures/slab.py`

### Stream 3: Weak Layer Parameter Modules (start after Stream 1)
- **Steps:** 4
- **Files:** `weak_layer_parameters/{Gc,G_Ic,G_IIc,tau_c,sigma_c_plus,sigma_c_minus}.py`
- Stream 1 should land first to avoid conflict on sigma_c files

### Stream 4: Graph & Engine Wiring (after Streams 2 and 3)
- **Steps:** 5 → 6 → 7 → 8 (sequential within stream)
- **Files:** `graph/structures.py`, `graph/definitions.py`, `execution/dispatcher.py`, `execution/executor.py`

### Stream 5: WEAC Adapter (after Streams 1 and 2; parallel to Stream 4)
- **Steps:** 9 → 10 (sequential within stream)
- **Files:** `stability_models/weac/weac_result.py`, `stability_models/weac/weac_criterion.py`,
  `stability_models/__init__.py`, `pyproject.toml`
- No file overlap with Stream 4

### Stream 6: Tests and Notebook (after Streams 4 and 5)
- **Steps:** 11 → 12 (sequential within stream)
- **Files:** `tests/test_weac_criterion.py`, `tests/test_weak_layer_engine.py`,
  `examples/weac_skier_all_pathways.ipynb`

---

## Incremental Delivery (Multi-PR Strategy)

### PR 1: Bug fixes + data structures
- **Delivers:** Silent failures fixed; `WeakLayer` dataclass and `slab.weac_layer` field added.
  Zero behaviour change for existing callers.
- **Steps:** 1, 2, 3 | **Files:** ~6

### PR 2: Weak layer parameter modules + graph extension
- **Delivers:** Six computable weak-layer parameters via `weissgraeber_rosendahl`. Graph knows
  `"weak_layer"` and `"stability_model"` levels, `g_delta` node exists, pathways discoverable.
- **Steps:** 4, 5, 6 | **Files:** ~9 | **Depends on:** PR 1

### PR 3: Execution engine extension
- **Delivers:** `engine.execute_all(slab, "G_Ic")` populates `slab.weac_layer`.
  `engine.execute_all(slab, "g_delta")` runs the full WEAC pipeline end-to-end.
- **Steps:** 7, 8 | **Files:** 2 | **Depends on:** PR 2 + PR 4 (for `_dispatch_weac_skier`)

### PR 4: WEAC adapter + dependency management
- **Delivers:** `calculate_weac_skier(slab)` is callable;
  `pip install snowpyt-mechparams[weac]` works.
- **Steps:** 9, 10 | **Files:** 4 | **Depends on:** PR 1

### PR 5: Tests + example notebook
- **Delivers:** Full test coverage; `weac_skier_all_pathways.ipynb` runs end-to-end on the
  real dataset and produces all visualisations.
- **Steps:** 11, 12 | **Files:** 3 | **Depends on:** PRs 3 and 4

---

## Testing Strategy

**Unit tests (no WEAC install required)** — `tests/test_weac_criterion.py`:

| Test | Verifies |
|---|---|
| `test_nominal_strips_ufloat` | `_nominal(ufloat(5.0, 0.5))` → `5.0` |
| `test_nominal_passthrough_float` | `_nominal(3.14)` → `3.14` |
| `test_nominal_none` | `_nominal(None)` → `None` |
| `test_segment_length_from_slab_thickness` | 2 × 50 cm layers → `L = 1000.0` mm |
| `test_segment_length_override` | `segment_length=5000.0` bypasses derivation |
| `test_layer_conversion_units` | 20 cm layer → WEAC `h = 200.0` mm |
| `test_layer_uses_density_calculated` | `density_calculated` used; `density_measured` ignored |
| `test_layer_missing_thickness_returns_none` | `thickness=None` → `None` |
| `test_layer_missing_density_returns_none` | `density_calculated=None` → `None` |
| `test_layer_missing_elastic_modulus_returns_none` | `elastic_modulus=None` → `None` |
| `test_layer_missing_shear_modulus_returns_none` | `shear_modulus=None` → `None` |
| `test_layer_missing_poissons_ratio_returns_none` | `poissons_ratio=None` → `None` |
| `test_no_weak_layer_returns_none` | `slab.weak_layer = None` → `None` |
| `test_no_weac_layer_returns_none` | `slab.weac_layer = None` → `None` |
| `test_no_angle_returns_none` | `slab.angle = None` → `None` |
| `test_import_error_message` | Monkeypatch `_WEAC_AVAILABLE = False` → `ImportError` with instructions |
| `test_weak_layer_override_takes_precedence` | `G_Ic=1.5` kwarg overrides `slab.weac_layer.G_Ic` |

**Integration tests** (`@pytest.mark.slow`, requires `weac` installed):

| Test | Verifies |
|---|---|
| `test_skier_known_slab` | Demo-matching slab → `g_delta` within 1% of WEAC notebook reference |
| `test_g_delta_increases_with_slope` | 40° → higher `g_delta` than 30° |
| `test_g_delta_increases_with_slab_depth` | Thicker slab → higher `g_delta` |
| `test_weak_layer_override_G_Ic` | `G_Ic=1.5` → lower `g_delta` than default |
| `test_result_fields_finite` | All `WeacSkierResult` fields are finite floats |
| `test_converged_flag` | Well-conditioned slab → `converged=True` |
| `test_G_I_G_II_indexing` | `incremental_ERR()[1]` = G_I, `[2]` = G_II, `[0]` = G_total |

**Graph / engine tests** — `tests/test_weak_layer_engine.py`:

| Test | Verifies |
|---|---|
| `test_graph_weak_layer_nodes` | Graph has 6 nodes with `level="weak_layer"` |
| `test_WEAK_LAYER_PARAMS_frozenset` | `WEAK_LAYER_PARAMS` contains all 6 parameter names |
| `test_weak_layer_params_registered` | Dispatcher has all 6 `(param, "weissgraeber_rosendahl")` specs |
| `test_execute_G_Ic_populates_weac_layer` | Engine call sets `slab.weac_layer.G_Ic` |
| `test_graph_g_delta_node` | Graph has `g_delta` node with `level="stability_model"` |
| `test_STABILITY_PARAMS_frozenset` | `STABILITY_PARAMS == {"g_delta"}` |

---

## To-dos

### Bug Fixes
- [ ] Fix `stability_models/__init__.py`: `from snowpyt_mechparams.models.static_load` → `from snowpyt_mechparams.stability_models.static_load`
- [ ] Fix `sigma_c_plus.py:140`: `rho_ice` → `RHO_ICE`
- [ ] Fix `sigma_c_minus.py:215`: `rho_ice` → `RHO_ICE`

### Data Structures
- [ ] Create `data_structures/weak_layer.py` with SnowPyt `WeakLayer` dataclass (6 optional UFloat fields)
- [ ] Update `data_structures/__init__.py` to export `WeakLayer`
- [ ] Add `weac_layer: Optional[WeakLayer] = None` to `data_structures/slab.py`

### Weak Layer Parameter Modules
- [ ] Implement `weak_layer_parameters/Gc.py`: `calculate_Gc` dispatcher + `_calculate_Gc_weissgraeber_rosendahl` returning `ufloat(1.0, 0.0)` J/m²
- [ ] Create `weak_layer_parameters/G_Ic.py`: same pattern, `ufloat(0.56, 0.0)` J/m²
- [ ] Create `weak_layer_parameters/G_IIc.py`: same pattern, `ufloat(0.79, 0.0)` J/m²
- [ ] Create `weak_layer_parameters/tau_c.py`: same pattern, `ufloat(5.09, 0.0)` kPa
- [ ] Add `weissgraeber_rosendahl` method to `sigma_c_plus.py`: `ufloat(6.16, 0.0)` kPa
- [ ] Add `weissgraeber_rosendahl` method to `sigma_c_minus.py`: `ufloat(2.6, 0.0)` kPa

### Graph
- [ ] Add `"weak_layer"` and `"stability_model"` to `NodeLevel` Literal in `graph/structures.py`
- [ ] Update `Node.__post_init__` validator to accept both new levels
- [ ] Add `weak_layer_params` property to `Graph` in `graph/structures.py`
- [ ] Add `stability_params` property to `Graph` in `graph/structures.py`
- [ ] Add 6 `weak_layer` parameter nodes to `graph/definitions.py`
- [ ] Add 6 method edges (`snow_pit` → weak layer param, `"weissgraeber_rosendahl"`) to `graph/definitions.py`
- [ ] Add `g_delta` parameter node (level=`"stability_model"`) to `graph/definitions.py`
- [ ] Add `merge_weac_inputs` merge node to `graph/definitions.py`
- [ ] Add flow edges from all 10 prerequisite params into `merge_weac_inputs`
- [ ] Add method edge `merge_weac_inputs` → `g_delta` via `"weac_skier"`
- [ ] Export `WEAK_LAYER_PARAMS` frozenset from `graph/definitions.py`
- [ ] Export `STABILITY_PARAMS` frozenset from `graph/definitions.py`
- [ ] Update `__all__` in `graph/definitions.py`

### Execution Engine
- [ ] Add `ParameterLevel.WEAK_LAYER` and `ParameterLevel.STABILITY` to enum in `execution/dispatcher.py`
- [ ] Register 6 `MethodSpec` entries for weak layer parameters in `execution/dispatcher.py`
- [ ] Add `_dispatch_weac_skier` lazy-import helper in `execution/dispatcher.py`
- [ ] Register `("g_delta", "weac_skier")` `MethodSpec` using `_dispatch_weac_skier`
- [ ] Import `WEAK_LAYER_PARAMS`, `STABILITY_PARAMS` in `execution/executor.py`
- [ ] Add `WEAK_LAYER_PARAMS` branch + success determination in `execute_parameterization`
- [ ] Add `STABILITY_PARAMS` branch + success determination in `execute_parameterization`
- [ ] Implement `_execute_weak_layer_calculations(slab, target_parameter)` in `execution/executor.py`
- [ ] Implement `_execute_stability_calculations(slab, target_parameter)` in `execution/executor.py`

### Stability Models (WEAC Adapter)
- [ ] Create `stability_models/weac/weac_result.py` with `WeacSkierResult` dataclass
- [ ] Create `stability_models/weac/weac_criterion.py` with `_nominal`, unit conversion, `calculate_weac_skier`
- [ ] Implement G_I/G_II extraction: `Analyzer(result.final_system).incremental_ERR(unit="J/m^2")` → `[1]`, `[2]`
- [ ] Update `stability_models/__init__.py` to add WEAC exports

### Dependency Management
- [ ] Update `pyproject.toml`: `requires-python = ">=3.12"`, add `[project.optional-dependencies] weac = ["weac>=3.1.4"]`

### Tests
- [ ] Create `tests/test_weac_criterion.py`: 17 unit tests + 7 integration tests
- [ ] Create `tests/test_weak_layer_engine.py`: 6 graph/engine tests

### Example Notebook
- [ ] Create `examples/weac_skier_all_pathways.ipynb` — Section 1: Load snow pit data
- [ ] Section 2: `find_parameterizations(graph, graph.get_node("g_delta"))`
- [ ] Section 3: Create ECTP slabs (`weak_layer_def="ECTP_failure_layer"`)
- [ ] Section 4: Small-sample test run (N=50 slabs, smoke test full pipeline)
- [ ] Section 5: Execute all pathways on full dataset
- [ ] Section 6: Coverage table (pathways × slabs, avg g_delta, % converged)
- [ ] Section 7: Sankey diagram for best-coverage pathway
- [ ] Section 8: g_delta violin plots by pathway
- [ ] Section 9: Convergence analysis + G_I vs G_II scatter
