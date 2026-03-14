# Shear stress of a snow slab from its gravitational load

import math

from uncertainties import umath

from snowpyt_mechparams.data_structures import Slab, UncertainValue


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
    slope_rad = slab.angle * math.pi / 180  # UFloat-compatible radians
    total = 0.0
    for layer in slab.layers:
        if layer.thickness is None or layer.density_calculated is None:
            return float('nan')
        total += (layer.thickness / 100.0) * layer.density_calculated * g
    return total * umath.sin(slope_rad)
