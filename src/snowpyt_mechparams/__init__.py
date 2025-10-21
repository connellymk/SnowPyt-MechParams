"""
SnowPyt-MechParams: Collaborative Python library for estimating mechanical
parameters from snow pit measurements.

This library provides methods to estimate various mechanical properties of snow
from standard snowpit observations including density, grain size, hardness, and
temperature measurements. Developed through collaboration between multiple
academic researchers and institutions in the snow science community.
"""

from .data_structures import Layer, Slab
from .shear_modulus import calculate_shear_modulus

__version__ = "0.1.0"
__author__ = "Mary Connelly and SnowPyt-MechParams Contributors"
__email__ = "connellymarykate@gmail.com"
__maintainer__ = "SnowPyt-MechParams Contributors"

# Expose common data structures and calculation functions at package level
__all__ = ["Layer", "Slab", "calculate_shear_modulus"]
