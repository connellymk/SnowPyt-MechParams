"""
Weak layer parameters module for calculating mechanical properties of weak layers.

This module provides methods to calculate various mechanical parameters
specific to weak layers in snow, including:
- Total fracture energy (Gc)
- Mode-I fracture toughness (G_Ic)
- Mode-II fracture toughness (G_IIc)
- Shear strength (τ_c)
- Compressive strength (σ_c-)
- Tensile normal strength (σ_c+)

These parameters are critical for avalanche stability assessment and
weak layer failure analysis.  The ``'weissgraeber_rosendahl'`` method returns
the reference constants from Weißgraeber & Rosendahl (2023), which are also
WEAC's built-in defaults.
"""

from snowpyt_mechparams.weak_layer_parameters.Gc import calculate_Gc
from snowpyt_mechparams.weak_layer_parameters.G_Ic import calculate_G_Ic
from snowpyt_mechparams.weak_layer_parameters.G_IIc import calculate_G_IIc
from snowpyt_mechparams.weak_layer_parameters.tau_c import calculate_tau_c
from snowpyt_mechparams.weak_layer_parameters.sigma_c_minus import calculate_sigma_c_minus
from snowpyt_mechparams.weak_layer_parameters.sigma_c_plus import calculate_sigma_c_plus

__all__ = [
    "calculate_Gc",
    "calculate_G_Ic",
    "calculate_G_IIc",
    "calculate_tau_c",
    "calculate_sigma_c_minus",
    "calculate_sigma_c_plus",
]

