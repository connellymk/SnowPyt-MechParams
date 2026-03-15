"""
Roch (1966) gravitational and skier stability criteria for snow slabs.

Two variants are implemented:

* **Natural** — S_r = τ_c / τ  (Roch, 1966)
* **Skier** — S_sk = (τ_c − τ) / τ_sk  (Föhn, 1987)

References
----------
Roch, A. (1966): Les déclenchements d'avalanches.  IASH Publ. 69, 182–195.
Föhn, J. M. L. (1987): The stability index and various triggering mechanisms.
    IAHS Publ. 162, 195–214.
"""

from __future__ import annotations

import math
from typing import Literal, Optional

from snowpyt_mechparams.models import Slab, UncertainValue
from snowpyt_mechparams.stability_criteria._utils import _nominal
from snowpyt_mechparams.stability_criteria.roch.roch_result import RochResult
from snowpyt_mechparams.stability_criteria.roch.shear_stress import calculate_shear_stress


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

            S_r = τ_c / τ  (Roch, 1966)

        If provided, the skier variant is used (Föhn, 1987):

            S_sk = (τ_c − τ) / τ_sk

    Returns
    -------
    Optional[RochResult]
        ``None`` if ``slab.angle`` is ``None``, any layer is missing
        ``thickness`` or ``density_calculated``, shear stress τ is NaN,
        τ is negative (counter-slope),
        τ is zero for the natural variant (flat terrain, S_r undefined),
        or (skier variant) ``skier_stress`` is zero or NaN.
    """
    if slab.angle is None:
        return None

    tau = calculate_shear_stress(slab)
    tau_val = _nominal(tau)
    if tau_val is None or math.isnan(tau_val) or tau_val < 0:
        return None

    if skier_stress is None:
        # Natural variant: S_r = τ_c / τ.  Undefined on flat terrain (τ = 0).
        if tau_val == 0:
            return None
        index = tau_c / tau
        variant: Literal["natural", "skier"] = "natural"
    else:
        # Skier variant: S_sk = (τ_c − τ) / τ_sk.
        # τ = 0 (flat terrain) is valid here; τ_sk = 0 is not.
        skier_val = _nominal(skier_stress)
        if skier_val is None or math.isnan(skier_val) or skier_val == 0:
            return None
        index = (tau_c - tau) / skier_stress
        variant = "skier"

    return RochResult(
        stability_index=index,
        shear_stress=tau,
        tau_c=tau_c,
        variant=variant,
        skier_stress=skier_stress,
    )
