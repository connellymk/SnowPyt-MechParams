# Roch Stability Criterion

**Date:** 2026-03-13
**Feature:** `stability_models/roch/`
**Author:** Claude (claude-sonnet-4-6)

---

## Overview

Implement the Roch stability criterion as a `roch/` package inside `stability_models/`,
mirroring the `weac/` package structure. The criterion compares the gravitational shear stress
acting on the weak layer to its shear strength. Both the natural terrain variant and the
skier-loaded variant are supported; the caller selects by providing or omitting `skier_stress`.

---

## Formulas

**Natural terrain variant** (Roch, 1966):

```
τ   = Σᵢ (ρᵢ × hᵢ × g) × sin θ     [N/m²]
S_r = τ_c / τ
```

Slope is considered unstable when S_r < 1 (shear stress exceeds shear strength).

**Skier variant** (Föhn, 1987):

```
S_sk = (τ_c − τ) / τ_sk
```

where `τ_sk` is the additional shear stress applied by a skier at the weak layer [N/m²].
Unstable when S_sk < 1.

---

## Design Decisions

| Question | Decision |
|---|---|
| Return of `calculate_shear_stress` | Single `UncertainValue` (shear component only) |
| Density field | `layer.density_calculated` only (mirrors `weac_criterion.py`) |
| Shear strength input | `tau_c` passed as argument to `calculate_roch` |
| Variant selection | Pass `skier_stress=None` → natural; pass value → skier |
| UFloat propagation | Preserved — Roch is pure arithmetic, no external solver |
| File structure | `roch_result.py` + `roch_criterion.py` (mirrors `weac/` pattern) |

---

## Files to Create / Modify

### 1. Rewrite `stability_models/roch/shear_stress.py`

The existing file was copied from the deleted `static_load.py` and has several bugs:
- Uses `layer.density` (field does not exist; should be `density_calculated`)
- Function name `calculate_static_load` does not match the file
- Returns a 3-tuple instead of a single shear stress value
- Imports `numpy` unnecessarily

**New implementation:**

```python
# Shear stress of a snow slab from its gravitational load

import math

from snowpyt_mechparams.models import Slab, UncertainValue  # data_structures was renamed to models


def calculate_shear_stress(slab: Slab) -> UncertainValue:
    """
    Calculate the shear stress on the weak layer from the gravitational
    load of the snow slab.

    The shear stress is the component of the slab weight acting parallel
    to the slope: τ = Σᵢ (ρᵢ hᵢ g) × sin θ

    Parameters
    ----------
    slab : Slab
        Slab with layers whose ``density_calculated`` (kg/m³) and
        ``thickness`` (cm) are populated, and whose ``angle`` (degrees)
        is set.

    Returns
    -------
    UncertainValue
        Shear stress in N/m². Returns ``float('nan')`` if any layer is
        missing ``thickness`` or ``density_calculated``.
    """
    g = 9.81  # m/s²
    slope_rad = math.radians(slab.angle)
    total = 0.0
    for layer in slab.layers:
        if layer.thickness is None or layer.density_calculated is None:
            return float('nan')
        total += (layer.thickness / 100.0) * layer.density_calculated * g
    return total * math.sin(slope_rad)
```

### 2. Create `stability_models/roch/roch_result.py`

Pure dataclass — safe to import with no optional dependencies (mirrors `weac_result.py`).
UFloat values are preserved; no nominal stripping is required.

```python
# Result dataclass for the Roch stability criterion

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from snowpyt_mechparams.models import UncertainValue  # data_structures was renamed to models


@dataclass
class RochResult:
    """
    Result of a Roch stability criterion evaluation.

    Attributes
    ----------
    stability_index : UncertainValue
        S_r = τ_c / τ  (natural)  or  S_sk = (τ_c − τ) / τ_sk  (skier).
        Values < 1 indicate instability.
    shear_stress : UncertainValue
        Gravitational shear stress τ on the weak layer [N/m²].
    tau_c : UncertainValue
        Weak layer shear strength supplied by the caller [N/m²].
    variant : str
        ``"natural"`` or ``"skier"``.
    skier_stress : UncertainValue, optional
        Additional skier shear stress τ_sk [N/m²]. ``None`` for the
        natural variant.
    """
    stability_index: UncertainValue
    shear_stress: UncertainValue
    tau_c: UncertainValue
    variant: str
    skier_stress: Optional[UncertainValue] = None
```

### 3. Create `stability_models/roch/roch_criterion.py`

```python
# Roch stability criterion

from __future__ import annotations

import math
from typing import Optional

from snowpyt_mechparams.models import Slab, UncertainValue  # data_structures was renamed to models
from snowpyt_mechparams.stability_models.roch.roch_result import RochResult
from snowpyt_mechparams.stability_models.roch.shear_stress import calculate_shear_stress


def calculate_roch(
    slab: Slab,
    tau_c: UncertainValue,
    skier_stress: Optional[UncertainValue] = None,
) -> Optional[RochResult]:
    """
    Compute the Roch stability index for a snow slab.

    Parameters
    ----------
    slab : Slab
        Slab with ``angle`` set and all layers having ``thickness`` and
        ``density_calculated`` populated.
    tau_c : UncertainValue
        Shear strength of the weak layer [N/m²].
    skier_stress : UncertainValue, optional
        Additional shear stress from a skier τ_sk [N/m²].
        If ``None``, the natural terrain variant is used:
            S_r = τ_c / τ
        If provided, the skier variant (Föhn, 1987) is used:
            S_sk = (τ_c − τ) / τ_sk

    Returns
    -------
    Optional[RochResult]
        ``None`` if ``slab.angle`` is ``None`` or any layer is missing
        ``thickness`` or ``density_calculated``.
    """
    if slab.angle is None:
        return None

    tau = calculate_shear_stress(slab)
    if math.isnan(float(getattr(tau, 'nominal_value', tau))):
        return None

    if skier_stress is None:
        index = tau_c / tau
        variant = "natural"
    else:
        index = (tau_c - tau) / skier_stress
        variant = "skier"

    return RochResult(
        stability_index=index,
        shear_stress=tau,
        tau_c=tau_c,
        variant=variant,
        skier_stress=skier_stress,
    )
```

### 4. Create `stability_models/roch/__init__.py`

```python
"""
Roch stability criterion.

Provides the gravitational shear stress on the weak layer and the Roch
stability index for both natural terrain and skier-loaded variants.
"""

from snowpyt_mechparams.stability_models.roch.roch_result import RochResult
from snowpyt_mechparams.stability_models.roch.roch_criterion import calculate_roch
from snowpyt_mechparams.stability_models.roch.shear_stress import calculate_shear_stress

__all__ = [
    "RochResult",
    "calculate_roch",
    "calculate_shear_stress",
]
```

### 5. Update `stability_models/__init__.py`

Remove the broken import from the deleted `static_load.py` and add the roch exports:

```python
"""
Models for calculating mechanical loads and forces on snow slabs.
"""

from snowpyt_mechparams.stability_models.roch import (
    RochResult,
    calculate_roch,
    calculate_shear_stress,
)
from snowpyt_mechparams.stability_models.weac import (
    WeacSkierResult,
    calculate_weac_skier,
)

__all__ = [
    "RochResult",
    "calculate_roch",
    "calculate_shear_stress",
    "WeacSkierResult",
    "calculate_weac_skier",
]
```

---

## Critical Files

| File | Action |
|---|---|
| `stability_models/roch/shear_stress.py` | Rewrite |
| `stability_models/roch/roch_result.py` | Create |
| `stability_models/roch/roch_criterion.py` | Create |
| `stability_models/roch/__init__.py` | Create |
| `stability_models/__init__.py` | Update imports |

---

## Reference Patterns

- Density field: `layer.density_calculated` — see `weac_criterion.py:178`
- NaN sentinel: `float('nan')` — valid `UncertainValue` since `UncertainValue = Union[float, UFloat]`
- UFloat check: `getattr(v, 'nominal_value', v)` strips to float without importing `uncertainties`
- UFloat propagation: automatic through arithmetic; no stripping needed (unlike WEAC)
- Units: thickness cm → m (÷ 100), angle degrees → radians via `math.radians`
- Return `None` on missing inputs (mirrors `weac_criterion.py`)

---

## Out of Scope

- Graph / execution engine integration for `S_r` as a first-class graph node (separate PR)
- Skier stress calculation (τ_sk is the caller's responsibility; this criterion only computes S_sk given τ_sk)
- Uncertainty on the Roch threshold (the 1.0 cutoff is treated as exact)

---

## Verification

1. **Import check:**
   ```
   python -c "from snowpyt_mechparams.stability_models import RochResult, calculate_roch, calculate_shear_stress"
   ```

2. **Shear stress smoke test** — single layer, density_calculated=250 kg/m³, thickness=50 cm, angle=30°:
   ```python
   tau = calculate_shear_stress(slab)
   assert abs(float(tau) - 250 * 0.5 * 9.81 * math.sin(math.radians(30))) < 0.1
   # expect ≈ 613 N/m²
   ```

3. **Natural variant** — tau_c = 1000 N/m², tau ≈ 613 N/m²:
   ```python
   result = calculate_roch(slab, tau_c=1000.0)
   assert result.variant == "natural"
   assert abs(float(result.stability_index) - 1000.0 / 613.0) < 0.01
   ```

4. **Skier variant** — same slab, tau_sk = 100 N/m²:
   ```python
   result = calculate_roch(slab, tau_c=1000.0, skier_stress=100.0)
   assert result.variant == "skier"
   assert abs(float(result.stability_index) - (1000.0 - 613.0) / 100.0) < 0.01
   ```

5. **Missing data** — layer with `density_calculated=None` → `calculate_roch` returns `None`

6. **Uncertainty propagation** — UFloat density → `stability_index` is a UFloat with propagated uncertainty:
   ```python
   from uncertainties import ufloat
   layer.density_calculated = ufloat(250, 25)  # 10% relative uncertainty
   result = calculate_roch(slab, tau_c=ufloat(1000, 100))
   assert hasattr(result.stability_index, 'nominal_value')
   ```
