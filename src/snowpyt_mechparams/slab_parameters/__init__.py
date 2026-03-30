"""
Slab parameters module for calculating mechanical properties of snow slabs.

This module provides methods to calculate plate theory parameters for snow slabs:
- A11: Extensional stiffness
- A55: Shear stiffness (with shear correction factor κ)
- B11: Bending-extension coupling stiffness
- D11: Bending stiffness

Note: Layer-level parameters (density, elastic modulus, shear modulus, Poisson's ratio)
are in the layer_parameters module.
"""

from snowpyt_mechparams.slab_parameters.extensional_stiffness import calculate_A11
from snowpyt_mechparams.slab_parameters.shear_stiffness import calculate_A55
from snowpyt_mechparams.slab_parameters.bending_extension_coupling import calculate_B11
from snowpyt_mechparams.slab_parameters.bending_stiffness import calculate_D11

__all__ = [
    "calculate_A11",
    "calculate_A55",
    "calculate_B11",
    "calculate_D11",
]
