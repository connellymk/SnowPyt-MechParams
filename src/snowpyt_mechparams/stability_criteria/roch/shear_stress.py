"""
Gravitational shear stress on the weak layer from a snow slab.

Reference
---------
Roch, A. (1966): Les déclenchements d'avalanches.  IASH Publ. 69, 182–195.
"""

import math

from uncertainties import umath

from snowpyt_mechparams.models import Slab, UncertainValue


def calculate_shear_stress(slab: Slab) -> UncertainValue:
    """
    Calculate the shear stress on the weak layer from the gravitational
    load of the snow slab.

    The shear stress is the component of the slab weight acting parallel
    to the slope (Roch, 1966):

        τ = Σᵢ (ρᵢ hᵢ g) × sin θ

    Parameters
    ----------
    slab : Slab
        Slab with layers whose ``density_calculated`` (kg/m³) and
        ``thickness`` (cm) are populated, and whose ``angle`` (degrees)
        is set.

    Returns
    -------
    UncertainValue
        Shear stress in N/m².  Returns ``math.nan`` (as a plain ``float``)
        if any layer is missing ``thickness`` or ``density_calculated``;
        the caller should check ``math.isnan(float(result))`` before use.
    """
    g = 9.81  # m/s²
    slope_rad = slab.angle * math.pi / 180  # UFloat-compatible radians
    total = 0.0
    for layer in slab.layers:
        if layer.thickness is None or layer.density_calculated is None:
            return float('nan')
        total += (layer.thickness / 100.0) * layer.density_calculated * g
    return total * umath.sin(slope_rad)
