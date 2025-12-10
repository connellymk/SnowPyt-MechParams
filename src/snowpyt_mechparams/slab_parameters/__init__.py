"""
Slab parameters module for calculating mechanical properties of snow slabs.

This module provides methods to calculate various mechanical parameters
for snow slabs, including:
- Density
- Elastic modulus
- Shear modulus
- Poisson's ratio
- Plate theory parameters (A11, A55, B11, D11)
"""

from snowpyt_mechparams.slab_parameters.shear_modulus import calculate_shear_modulus

__all__ = [
    "calculate_shear_modulus",
]
