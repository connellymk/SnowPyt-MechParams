"""
Weak layer parameters module for calculating mechanical properties of weak layers.

This module provides methods to calculate various mechanical parameters
specific to weak layers in snow, including:
- Compressive strength (σ_c-)
- Tensile normal strength (σ_c+)
- Fracture toughness (Gc)

These parameters are critical for avalanche stability assessment and
weak layer failure analysis.
"""

from snowpyt_mechparams.weak_layer_parameters.sigma_c_minus import calculate_sigma_c_minus
from snowpyt_mechparams.weak_layer_parameters.sigma_c_plus import calculate_sigma_c_plus

__all__ = [
    "calculate_sigma_c_minus",
    "calculate_sigma_c_plus",
]

