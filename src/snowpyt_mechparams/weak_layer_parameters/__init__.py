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
weak layer failure analysis.  For G_c, G_Ic, G_IIc, τ_c, and σ_c+, the
``'weissgraeber_rosendahl'`` method returns the reference constants from
Weißgraeber & Rosendahl (2023), which are also WEAC's built-in defaults.
For σ_c-, the ``'reiweger'`` method returns the Reiweger et al. (2015) value
cited by Weißgraeber & Rosendahl (2023).
"""

from snowpyt_mechparams.weak_layer_parameters.fracture_energy import calculate_G_c
from snowpyt_mechparams.weak_layer_parameters.mode_i_fracture_toughness import calculate_G_Ic
from snowpyt_mechparams.weak_layer_parameters.mode_ii_fracture_toughness import calculate_G_IIc
from snowpyt_mechparams.weak_layer_parameters.tau_c import calculate_tau_c
from snowpyt_mechparams.weak_layer_parameters.sigma_c_minus import calculate_sigma_c_minus
from snowpyt_mechparams.weak_layer_parameters.sigma_c_plus import calculate_sigma_c_plus

__all__ = [
    "calculate_G_c",
    "calculate_G_Ic",
    "calculate_G_IIc",
    "calculate_tau_c",
    "calculate_sigma_c_minus",
    "calculate_sigma_c_plus",
]

