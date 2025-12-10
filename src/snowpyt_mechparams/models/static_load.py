# Methods to calculate the weight per units area (pressure) of a layered slab

import math
from typing import Tuple

from snowpyt_mechparams.data_structures import Slab


def calculate_static_load(slab: Slab) -> Tuple[float, float, float]:
    """
    Calculate the weight per unit area (pressure) of a layered snow slab and
    the shear and normal force components on a slope.

    Parameters
    ----------
    slab: Slab
        A Slab object containing layers (each with thickness in cm and density in kg/m³)
        and the slope angle in degrees

    Returns
    -------
    float
        The gravitational load per unit area (N/m²) of the layered slab
    float
        The shear force component per unit area (N/m²) of the layered slab
    float
        The normal force component per unit area (N/m²) of the layered slab

    Notes
    -----
    The calculations account for:
    - Layer thickness in centimeters converted to meters
    - Layer density in kg/m³
    - Gravitational acceleration (9.81 m/s²)
    - Slope angle in degrees converted to radians
    - Force components resolved along and perpendicular to the slope
    """

    # Gravitational acceleration (m/s²)
    g = 9.81

    # Convert slope angle from degrees to radians
    slope_angle_rad = math.radians(slab.angle)

    gravitational_load = 0.0  # N/m²
    shear_load = 0.0          # N/m²
    normal_load = 0.0         # N/m²

    for layer in slab.layers:
        # Convert thickness from cm to m
        thickness_m = layer.thickness / 100.0

        # Calculate weight per unit area for this layer (N/m²)
        # Weight = thickness (m) * density (kg/m³) * g (m/s²) = N/m²
        layer_weight = thickness_m * layer.density * g

        # Total gravitational load (vertical component)
        gravitational_load += layer_weight

        # Shear component (parallel to slope)
        shear_load += layer_weight * math.sin(slope_angle_rad)

        # Normal component (perpendicular to slope)
        normal_load += layer_weight * math.cos(slope_angle_rad)

    return gravitational_load, shear_load, normal_load
