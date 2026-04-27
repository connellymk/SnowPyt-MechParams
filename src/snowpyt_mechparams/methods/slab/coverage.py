"""Slab-weight coverage methods used by graph execution."""

from __future__ import annotations

import math
from typing import Optional

from uncertainties import umath

from snowpyt_mechparams.constants import g
from snowpyt_mechparams.models import Slab, UncertainValue


def calculate_slab_weight(slab: Slab) -> Optional[UncertainValue]:
    """Return slab weight per unit area from computed layer densities."""
    total = None
    for layer in slab.layers:
        density = layer.density_calculated
        if density is None or layer.thickness is None:
            return None
        layer_weight = density * (layer.thickness / 100.0) * g
        total = layer_weight if total is None else total + layer_weight
    return total


def calculate_slab_weight_shear(slab: Slab) -> Optional[UncertainValue]:
    """Project slab weight onto the slope-parallel direction."""
    slab_weight = getattr(slab, "slab_weight", None)
    if slab_weight is None or slab.angle is None:
        return None
    return slab_weight * umath.sin(slab.angle * math.pi / 180.0)


def calculate_slab_weight_shear_with_elasticity(slab: Slab) -> Optional[UncertainValue]:
    """Return W_s only when all elastic layer inputs are present."""
    if not all(layer.elastic_modulus is not None for layer in slab.layers):
        return None
    if not all(layer.poissons_ratio is not None for layer in slab.layers):
        return None
    return getattr(slab, "slab_weight_shear", None)
