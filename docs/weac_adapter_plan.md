# WEAC Skier Criterion Adapter — Implementation Plan

## Background

[WEAC](https://github.com/2phi/weac) (Weak-layer fracture mechanics model for snow cover) is a
published Python library implementing beam-on-elastic-foundation mechanics for snowpack stability
assessment. SnowPyt-MechParams provides snow pit profiles as structured `Slab` objects with
uncertainty propagation. This document describes the plan to integrate WEAC as a stability
criterion in SnowPyt-MechParams via an adapter module that bridges the two libraries without
modifying either.

### Repository paths

```
/Users/marykate/Desktop/Snow/SnowPyt-MechParams/src/snowpyt_mechparams/   ← SnowPyt package root
/Users/marykate/Desktop/Snow/weac/src/weac/                               ← WEAC package root
```

### What is already implemented

`stability_models/weac/__init__.py` has been created and is complete — do not recreate it.
It contains:

```python
from snowpyt_mechparams.stability_models.weac.weac_result import WeacSkierResult
from snowpyt_mechparams.stability_models.weac.weac_criterion import calculate_weac_skier
__all__ = ["WeacSkierResult", "calculate_weac_skier"]
```

### Execution engine architecture (critical for implementing weak layer graph nodes)

SnowPyt uses a graph + execution engine to discover and run parameterization pathways. Adding
new parameters requires touching **five files** in a fixed pattern:

1. **`graph/structures.py`** — `NodeLevel` type alias and `Node.__post_init__` validator.
   Currently allows only `"layer"` and `"slab"`. Adding `"weak_layer"` requires updating both
   the `Literal` type and the validation check. Also add a `weak_layer_params` property to
   `Graph` (parallel to `layer_params` / `slab_params`).

2. **`graph/definitions.py`** — Add nodes with `level="weak_layer"` and method edges.
   Also export `WEAK_LAYER_PARAMS` frozenset (see Graph Additions section).

3. **`execution/dispatcher.py`** — Contains `ParameterLevel` enum (currently `LAYER` and
   `SLAB` only) and `MethodDispatcher._register_all_methods()`. Add:
   - `ParameterLevel.WEAK_LAYER = "weak_layer"` to the enum
   - Six `MethodSpec` entries (one per weak layer parameter) with
     `level=ParameterLevel.WEAK_LAYER`. Since `weissgraeber_rosendahl` returns constants,
     the lambda ignores its slab argument:
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
   - The dispatcher's `execute()` method already has an `else` branch that passes
     `inputs = {"slab": slab}` for non-LAYER levels — this works unchanged for WEAK_LAYER
     because the lambdas accept and ignore `slab`.

4. **`execution/executor.py`** — `PathwayExecutor.execute_parameterization()` currently
   triggers `_execute_slab_calculations()` only when `target_parameter in SLAB_PARAMS`.
   A new branch is needed for `WEAK_LAYER_PARAMS`. Key points:
   - Import `WEAK_LAYER_PARAMS` from `graph.definitions` alongside `SLAB_PARAMS`
   - Add `if target_parameter in WEAK_LAYER_PARAMS:` branch after the `SLAB_PARAMS` branch
   - Add `_execute_weak_layer_calculations(slab, target_parameter)` method that computes
     **all six** weak layer parameters in one pass (they share the same method and source,
     so computing all six is no more expensive than one), assembles a `WeakLayer(...)` object,
     and sets `result_slab.weac_layer = WeakLayer(...)`. Use `dataclasses.replace` if you
     need to update an existing `WeakLayer` (like `replace(slab.weac_layer, G_Ic=value)`).
   - Success determination for weak layer target: check that the trace for `target_parameter`
     succeeded (same pattern as slab params).

5. **`data_structures/weak_layer.py`** — New `WeakLayer` dataclass (see dedicated section).
   Also update `data_structures/__init__.py` to export `WeakLayer`.

### Known bug in existing `weak_layer_parameters` files

`sigma_c_plus.py` (line 140) and `sigma_c_minus.py` (line 215) use `rho_ice` (undefined
variable) instead of `RHO_ICE` (the constant imported at the top of each file from
`snowpyt_mechparams.constants`). The `weissgraeber_rosendahl` methods added as part of this
implementation return constant values and do not call the existing density-dependent code, so
this bug will not be triggered. However, if either file is run in any other context, a
`NameError` will occur. Fix the variable name in both files while editing them.

### Known bug in `stability_models/__init__.py`

The current import reads:
```python
from snowpyt_mechparams.models.static_load import calculate_static_load
```
The directory `models` does not exist. The correct import is:
```python
from snowpyt_mechparams.stability_models.static_load import calculate_static_load
```
Fix this when updating `stability_models/__init__.py` to add the WEAC exports.

### WEAC API call pattern

Key details confirmed from WEAC source for `weac_criterion.py`:

- **`incremental_ERR`** default unit is `"kJ/m^2"`. Must call with `unit="J/m^2"` to be
  consistent with WEAC's fracture energy defaults (which are in J/m²). This is where `G_I`
  and `G_II` come from — they are not fields of `CoupledCriterionResult`.

- **`CoupledCriterionResult`** fields (confirmed from source):
  `converged`, `critical_skier_weight`, `initial_critical_skier_weight`, `crack_length`,
  `g_delta`, `dist_ERR_envelope`, `max_dist_stress`, `min_dist_stress`

---

## Architecture Decision: Adapter Pattern

**Option chosen:** Adapter module — neither library is modified.

| Option | Verdict |
|---|---|
| 1. Duplicate WEAC code inside SnowPyt | Rejected — high maintenance burden, divergence risk |
| 2. Modify WEAC to accept SnowPyt data structures | Rejected — wrong dependency direction, UFloat incompatible with scipy.linalg |
| 3. Modify SnowPyt to match WEAC inputs (adapter) | **Selected** |
| 4. Contribute Protocol interface to WEAC | Deferred — medium-term collaboration with WEAC authors |

The adapter:
1. Strips `UFloat` to nominal floats at the boundary
2. Converts SnowPyt `Slab` → WEAC `ModelInput` (unit conversion + field mapping)
3. Runs WEAC's `SystemModel` + `CriteriaEvaluator`
4. Returns a `WeacSkierResult` dataclass

**Uncertainty note:** WEAC's eigensystem solver uses `scipy.linalg.eig`, which is incompatible
with `uncertainties.UFloat`. Uncertainty does not propagate through WEAC results. Nominal values
are used at the adapter boundary; the returned result contains plain floats.

---

## Scope

### Scenario supported: Skier (v1)

The skier scenario was chosen first because:
- It is WEAC's primary and most-validated use case
- It requires no PST geometry assumptions
- SnowPyt's `Slab` provides all required inputs (layers, weak layer, slope angle)

PST scenario integration is deferred to a future iteration, where `slab.pit.PST_results` can
supply cut lengths and system type (`pst-` / `-pst`) directly from field data.

---

## Files

### New files

```
data_structures/
└── weak_layer.py        ← WeakLayer dataclass (WEAC fracture/strength parameters)

stability_models/
└── weac/
    ├── __init__.py          ← subpackage — exposes WeacSkierResult, calculate_weac_skier
    ├── weac_result.py       ← WeacSkierResult dataclass (no WEAC dependency)
    └── weac_criterion.py    ← adapter: conversion helpers + calculate_weac_skier

weak_layer_parameters/
    ├── G_Ic.py              ← NEW: Mode I fracture toughness
    ├── G_IIc.py             ← NEW: Mode II fracture toughness
    └── tau_c.py             ← NEW: weak layer shear strength

tests/
└── test_weac_criterion.py   ← unit + integration tests
```

### Modified files

```
data_structures/
└── slab.py              ← add weac_layer: Optional[WeakLayer] = None

graph/
├── structures.py        ← extend NodeLevel to include "weak_layer"; add weak_layer_params property
└── definitions.py       ← add weak layer parameter nodes + weissgraeber_rosendahl edges

stability_models/
└── __init__.py          ← import from weac subpackage + fix broken static_load import

weak_layer_parameters/
    ├── Gc.py            ← implement weissgraeber_rosendahl method (currently a TODO stub)
    ├── sigma_c_minus.py ← add weissgraeber_rosendahl method
    └── sigma_c_plus.py  ← add weissgraeber_rosendahl method

pyproject.toml           ← update requires-python; add [weac] optional dependency group
```

---

## Dependency Management

Update `pyproject.toml`:

```toml
[project]
requires-python = ">=3.12"   # aligned with weac requirement

[project.optional-dependencies]
weac = ["weac>=3.1.4"]
```

Install with:

```bash
pip install snowpyt-mechparams[weac]
```

---

## New `WeakLayer` Dataclass

**File:** `data_structures/weak_layer.py`

A new dataclass that holds the WEAC-required fracture and strength parameters for the weak layer.
It is populated by SnowPyt's execution engine (via the graph) and stored as `slab.weac_layer`.
The adapter reads from it directly — it never calls `weak_layer_parameters` functions at call time.

```python
@dataclass
class WeakLayer:
    """
    Holds WEAC-required fracture and strength parameters for a weak layer.

    All fields are in the units expected by WEAC's WeakLayer constructor.
    Populated by the execution engine via weissgraeber_rosendahl methods.
    Any field left None will fall back to WEAC's internal default.

    Attributes
    ----------
    G_c : Optional[UncertainValue]
        Total fracture energy [J/m²]
    G_Ic : Optional[UncertainValue]
        Mode I (opening) fracture toughness [J/m²]
    G_IIc : Optional[UncertainValue]
        Mode II (sliding) fracture toughness [J/m²]
    sigma_c : Optional[UncertainValue]
        Tensile normal strength [kPa]
    tau_c : Optional[UncertainValue]
        Shear strength [kPa]
    sigma_comp : Optional[UncertainValue]
        Compressive strength [kPa]
    """
    G_c: Optional[UncertainValue] = None       # 1.0 J/m²  (WEAC default)
    G_Ic: Optional[UncertainValue] = None      # 0.56 J/m² (WEAC default)
    G_IIc: Optional[UncertainValue] = None     # 0.79 J/m² (WEAC default)
    sigma_c: Optional[UncertainValue] = None   # 6.16 kPa  (WEAC default)
    tau_c: Optional[UncertainValue] = None     # 5.09 kPa  (WEAC default)
    sigma_comp: Optional[UncertainValue] = None  # 2.6 kPa (WEAC default)
```

**`Slab` update:** Add `weac_layer: Optional[WeakLayer] = None` to the `Slab` dataclass
(after the existing `weak_layer` field), imported from `data_structures.weak_layer`.

---

## Graph Additions (`graph/structures.py` and `graph/definitions.py`)

### `graph/structures.py` changes

1. Extend `NodeLevel` to include `"weak_layer"`:
   ```python
   NodeLevel = Optional[Literal["layer", "slab", "weak_layer"]]
   ```
2. Update `Node.__post_init__` to accept `"weak_layer"` as valid.
3. Add a `weak_layer_params` property to `Graph` (parallel to `layer_params` / `slab_params`):
   ```python
   @property
   def weak_layer_params(self) -> FrozenSet[str]:
       return frozenset(n.parameter for n in self.nodes if n.level == "weak_layer")
   ```

### `graph/definitions.py` changes

Add six new parameter nodes with `level="weak_layer"` and register a `weissgraeber_rosendahl`
method edge for each. Since these methods return constant reference values (no density or grain
form input required), they are sourced from the `snow_pit` root node.

**New nodes (after the existing slab-level nodes):**

```python
# Weak-layer fracture / strength parameter nodes
G_c = build_graph.param("G_c", level="weak_layer")         # Total fracture energy
G_Ic = build_graph.param("G_Ic", level="weak_layer")        # Mode I fracture toughness
G_IIc = build_graph.param("G_IIc", level="weak_layer")      # Mode II fracture toughness
sigma_c = build_graph.param("sigma_c", level="weak_layer")  # Tensile normal strength
tau_c = build_graph.param("tau_c", level="weak_layer")      # Shear strength
sigma_comp = build_graph.param("sigma_comp", level="weak_layer")  # Compressive strength
```

**Method edges (weissgraeber_rosendahl — constant reference values):**

```python
build_graph.method_edge(snow_pit, G_c, "weissgraeber_rosendahl")
build_graph.method_edge(snow_pit, G_Ic, "weissgraeber_rosendahl")
build_graph.method_edge(snow_pit, G_IIc, "weissgraeber_rosendahl")
build_graph.method_edge(snow_pit, sigma_c, "weissgraeber_rosendahl")
build_graph.method_edge(snow_pit, tau_c, "weissgraeber_rosendahl")
build_graph.method_edge(snow_pit, sigma_comp, "weissgraeber_rosendahl")
```

**Classification set** — add to definitions.py after `LAYER_PARAMS` / `SLAB_PARAMS`:

```python
WEAK_LAYER_PARAMS: frozenset = graph.weak_layer_params
```

**`__all__`** — export the six new node variables and `WEAK_LAYER_PARAMS`.

---

## New and Modified `weak_layer_parameters` Files

All new files follow the structure of existing `layer_parameters/` files:
- A public `calculate_{param}(method, **kwargs) -> ufloat` dispatcher
- Private `_calculate_{param}_{method_name}(**kwargs) -> ufloat` implementations

The `weissgraeber_rosendahl` method in each file returns the corresponding WEAC reference value
from Weißgraeber & Rosendahl (2023), cited in the WEAC source. These are constant reference
values, not density-dependent parameterisations.

### New files

| File | Parameter | `weissgraeber_rosendahl` value | Unit |
|---|---|---|---|
| `G_Ic.py` | Mode I fracture toughness | 0.56 | J/m² |
| `G_IIc.py` | Mode II fracture toughness | 0.79 | J/m² |
| `tau_c.py` | Weak layer shear strength | 5.09 | kPa |

### Modified files — add `weissgraeber_rosendahl` method

| File | Parameter | `weissgraeber_rosendahl` value | Notes |
|---|---|---|---|
| `Gc.py` | Total fracture energy | 1.0 | J/m² — file exists but is a TODO stub; implement method |
| `sigma_c_minus.py` | Compressive strength | 2.6 | kPa — same value as existing `reiweger` method |
| `sigma_c_plus.py` | Tensile normal strength | 6.16 | kPa — constant; differs from existing `sigrist` (density-dependent) |

### Parameter mapping: `slab.weac_layer` → WEAC `WeakLayer`

The adapter reads fracture and strength parameters from `slab.weac_layer` (pre-computed by the
execution engine). It strips each `UFloat` to its nominal value. If a `WeakLayer` field is
`None`, WEAC's internal default applies (since the `weissgraeber_rosendahl` values ARE the WEAC
defaults, a `None` field and a computed value are numerically equivalent).

| `slab.weac_layer` field | WEAC `WeakLayer` field | WEAC default |
|---|---|---|
| `G_c` | `G_c` | 1.0 J/m² |
| `G_Ic` | `G_Ic` | 0.56 J/m² |
| `G_IIc` | `G_IIc` | 0.79 J/m² |
| `sigma_c` | `sigma_c` | 6.16 kPa |
| `tau_c` | `tau_c` | 5.09 kPa |
| `sigma_comp` | `sigma_comp` | 2.6 kPa |

The caller can override any individual field via `**weak_layer_overrides` on
`calculate_weac_skier`. These take precedence over `slab.weac_layer` values.

`kn` and `kt` are omitted from the constructor — WEAC derives them internally as `E_plane / h`
and `G / h` respectively. `collapse_height` is also omitted — WEAC derives it from layer
thickness via van Herwijnen (2016).

---

## Data Conversion Mapping

### Slab layers (`Layer` → `weac.components.Layer`)

| SnowPyt `Layer` field | WEAC `Layer` field | Conversion |
|---|---|---|
| `thickness` (cm, UFloat) | `h` (mm, float) | `nominal_value × 10` |
| `density_calculated` (kg/m³, UFloat) | `rho` (kg/m³, float) | `nominal_value` |
| `elastic_modulus` (MPa, UFloat) | `E` (MPa, float) | `nominal_value` — return `None` if not pre-computed |
| `shear_modulus` (MPa, UFloat) | `G` (MPa, float) | `nominal_value` — return `None` if not pre-computed |
| `poissons_ratio` (UFloat) | `nu` (float) | `nominal_value` — return `None` if not pre-computed |

> **Pre-computation required:** The adapter is a strict consumer of SnowPyt's calculated
> parameters. It never falls back to WEAC's internal parameter derivations for slab layers.
> `elastic_modulus`, `shear_modulus`, and `poissons_ratio` must be computed by SnowPyt's
> execution engine before calling `calculate_weac_skier`. If any of these are `None` on any
> slab layer, the function logs a warning identifying the missing field and layer, then
> returns `None`.

### Weak layer (`Layer` → `weac.components.WeakLayer`)

Same strict mapping as slab layers for `thickness`, `density_calculated`, `elastic_modulus`,
`shear_modulus`, and `poissons_ratio`.

Fracture and strength parameters are read from `slab.weac_layer` (pre-computed by the execution
engine). The caller can override any via `**weak_layer_overrides` (see Parameter mapping table
above).

### Scenario config (`Slab` → `weac.components.ScenarioConfig`)

| SnowPyt source | WEAC field | Notes |
|---|---|---|
| `slab.angle` (degrees, UFloat) | `phi` (degrees, float) | `nominal_value` |
| *(fixed)* | `system_type` | `"skier"` |

### Segments (skier scenario)

Two symmetric segments with the skier at their junction:

```python
[
    Segment(length=L, has_foundation=True, m=skier_mass),
    Segment(length=L, has_foundation=True, m=0),
]
```

---

## Segment Length

`L = slab.total_thickness × 10` (cm → mm).

**Why `slab.total_thickness` and not `slab.pit.layers` total:**
Snow pits are dug below the weak layer in practice (to characterise the full stratigraphy).
`slab.pit.layers` therefore includes the substratum layers below the weak layer, making the
full pit depth larger than the slab thickness. `slab.total_thickness` sums only the slab
layers (snow above the weak layer), which is the mechanically relevant dimension: it is the
beam WEAC models, not the full pit. The two values are not the same and conflating them would
overestimate segment length.

**Why this is physically motivated:**
The slab thickness H determines the beam's bending stiffness D and therefore the
characteristic beam length λ = (D / kn·cos²θ)^(1/4), typically 200–500 mm for seasonal
snowpacks. Using `L = H` ensures L ≥ 2λ for nearly all realistic slabs (H ≥ 40 cm), where
boundary effects on `g_delta` are < 5%.

**No fallback.** If any layer thickness is `None`, the per-layer validation step already
returns `None` before segment length is evaluated. There is no ambiguity to resolve.

Pass an explicit float to `segment_length` to override (e.g., `segment_length=5000.0`).

---

## Function Signatures

### `weac_result.py`

```python
@dataclass
class WeacSkierResult:
    g_delta: float                  # coupled criterion value — ≥ 1.0 = unstable
    converged: bool                 # whether WEAC's binary search converged
    G_I: float                      # Mode I ERR at critical point [J/m²]
    G_II: float                     # Mode II ERR at critical point [J/m²]
    G_total: float                  # G_I + G_II [J/m²]
    critical_skier_weight: float    # skier mass at g_delta = 1 [kg]
    crack_length: float             # crack length at critical point [mm]
    max_dist_stress: float          # max stress envelope value — ≥ 1.0 = stress-driven failure
    min_dist_stress: float          # min stress envelope value (safety margin)
    dist_ERR_envelope: float        # distance to ERR criterion envelope
    segment_length: float           # segment length used [mm] — informational
    skier_mass: float               # input skier mass [kg] — informational
```

### `weac_criterion.py`

```python
def calculate_weac_skier(
    slab: Slab,
    skier_mass: float = 80.0,
    segment_length: Optional[float] = None,
    **weak_layer_overrides,
) -> Optional[WeacSkierResult]:
    """
    segment_length : float, optional
        Length of each slab segment [mm]. If None, derived from slab.total_thickness.
        Pass an explicit value to override.
    **weak_layer_overrides
        Override specific weak layer fracture/strength parameters at call time.
        Values here take precedence over slab.weac_layer. Accepted keys match
        WEAC WeakLayer fields: G_c, G_Ic, G_IIc, sigma_c, tau_c, sigma_comp.
    """
```

---

## Edge Cases and Error Handling

| Condition | Behaviour |
|---|---|
| `slab.weak_layer is None` | Return `None` |
| `slab.weac_layer is None` | Return `None` |
| `slab.angle is None` | Return `None` |
| Any slab layer missing `thickness` or `density_calculated` | Return `None` |
| Any slab layer missing `elastic_modulus`, `shear_modulus`, or `poissons_ratio` | Log warning with layer index and field name; return `None` |
| Weak layer missing `thickness` or `density_calculated` | Return `None` |
| Weak layer missing `elastic_modulus`, `shear_modulus`, or `poissons_ratio` | Log warning; return `None` |
| WEAC not installed | Raise `ImportError` with install instructions |
| WEAC solver does not converge | Return result with `converged=False`, other fields still populated |

---

## Test Plan

### Unit tests (no WEAC required)

| Test | Verifies |
|---|---|
| `test_nominal_strips_ufloat` | `_nominal(ufloat(5.0, 0.5))` → `5.0` |
| `test_nominal_passthrough_float` | `_nominal(3.14)` → `3.14` |
| `test_nominal_none` | `_nominal(None)` → `None` |
| `test_segment_length_from_slab_thickness` | Slab with 2 × 50 cm layers → `L = 1000.0` mm |
| `test_segment_length_override` | Explicit `segment_length=5000.0` bypasses derivation |
| `test_layer_conversion_units` | SnowPyt 20 cm layer → WEAC `h = 200.0` mm |
| `test_layer_uses_density_calculated` | `density_calculated` used; `density_measured` ignored |
| `test_layer_missing_thickness_returns_none` | `thickness=None` → `None` |
| `test_layer_missing_density_returns_none` | `density_calculated=None` → `None` |
| `test_layer_missing_elastic_modulus_returns_none` | `elastic_modulus=None` → `None` |
| `test_layer_missing_shear_modulus_returns_none` | `shear_modulus=None` → `None` |
| `test_layer_missing_poissons_ratio_returns_none` | `poissons_ratio=None` → `None` |
| `test_no_weak_layer_returns_none` | `slab.weak_layer = None` → `None` |
| `test_no_weac_layer_returns_none` | `slab.weac_layer = None` → `None` |
| `test_no_angle_returns_none` | `slab.angle = None` → `None` |
| `test_import_error_message` | Monkeypatch `_WEAC_AVAILABLE = False` → `ImportError` with clear message |
| `test_weak_layer_override_takes_precedence` | `G_Ic=1.5` kwarg overrides `slab.weac_layer.G_Ic` |

### Integration tests (`@pytest.mark.slow`, requires `weac` installed)

| Test | Verifies |
|---|---|
| `test_skier_known_slab` | Slab matching WEAC demo values → `g_delta` within 1% of notebook result |
| `test_g_delta_increases_with_slope` | 40° slope has higher `g_delta` than 30° |
| `test_g_delta_increases_with_slab_depth` | Thicker slab → higher `g_delta` |
| `test_weak_layer_override_G_Ic` | `G_Ic=1.5` → lower `g_delta` than default |
| `test_result_fields_finite` | All result fields are finite floats |
| `test_converged_flag` | Well-conditioned slab → `converged=True` |

---

## Future Work

- **PST scenario:** Use `slab.pit.PST_results` to supply `system_type` (`pst-` / `-pst`) and
  `cut_length` from field test metadata. This makes WEAC directly comparable to observed
  propagation outcomes recorded in the pit.
- **Protocol contribution to WEAC:** Work with WEAC authors to add Python `Protocol` classes
  formalising the numerical interface (`rho`, `h`, `E`, `G`, `nu`). This would allow SnowPyt
  objects to satisfy the protocol via a thin wrapper, eliminating the need for explicit field
  mapping in the adapter.
- **Uncertainty:** Once the adapter is validated, consider a Monte Carlo wrapper that samples
  each `UFloat` input `N` times, runs `calculate_weac_skier` per sample, and returns
  `mean ± std` as an `UncertainValue`.
