"""
Result dataclass for the Roch stability criterion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from snowpyt_mechparams.models import UncertainValue


@dataclass(frozen=True)
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
    variant : {"natural", "skier"}
        Which form of the criterion was evaluated.
    skier_stress : UncertainValue, optional
        Additional skier shear stress τ_sk [N/m²]. ``None`` for the
        natural variant.
    """
    stability_index: UncertainValue
    shear_stress: UncertainValue
    tau_c: UncertainValue
    variant: Literal["natural", "skier"]
    skier_stress: Optional[UncertainValue] = None
