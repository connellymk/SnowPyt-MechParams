# Roch stability criterion

from __future__ import annotations

import math
from typing import Optional

from snowpyt_mechparams.data_structures import Slab, UncertainValue
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
        ``None`` if ``slab.angle`` is ``None``, any layer is missing
        ``thickness`` or ``density_calculated``, shear stress τ is zero,
        or (skier variant) ``skier_stress`` is zero.
    """
    if slab.angle is None:
        return None

    tau = calculate_shear_stress(slab)
    tau_val = float(getattr(tau, 'nominal_value', tau))
    if math.isnan(tau_val) or tau_val == 0:
        return None

    if skier_stress is None:
        index = tau_c / tau
        variant = "natural"
    else:
        skier_val = float(getattr(skier_stress, 'nominal_value', skier_stress))
        if math.isnan(skier_val) or skier_val == 0:
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
