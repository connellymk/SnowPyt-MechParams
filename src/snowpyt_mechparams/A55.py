# Methods to calculate shear stiffness (A55) of a layered slab

from typing import Any

import numpy as np
from uncertainties import ufloat

from data_structures.data_structures import Slab


def calculate_A55(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate shear stiffness of a layered slab based on specified method
    and input parameters.

    The shear stiffness A55 (multiplied by shear correction factor κ) represents
    the slab's resistance to transverse shear forces. It is a fundamental
    mechanical property used in first-order shear deformation beam theory for
    snow slab avalanche mechanics.

    Parameters
    ----------
    method : str
        Method to use for A55 calculation. Available methods:
        - 'weissgraeber_rosendahl': Uses Weißgraeber & Rosendahl (2023) 
          formulation based on classical laminate theory with first-order
          shear deformation theory (Timoshenko beam assumptions)

    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated shear stiffness κ*A55 in N/mm with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_A55_weissgraeber_rosendahl(**kwargs)
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_A55_weissgraeber_rosendahl(slab: Slab) -> ufloat:
    """
    Calculate shear stiffness using Weißgraeber & Rosendahl (2023) formulation
    based on classical laminate theory with first-order shear deformation.

    This method calculates the shear stiffness of a layered slab by integrating
    the shear modulus over the slab thickness and applying a shear correction
    factor. The formulation applies first-order shear deformation theory
    (Timoshenko beam theory) from composite mechanics to stratified snow covers.

    Parameters
    ----------
    slab : Slab
        Slab object containing ordered layers from top to bottom, where each
        layer has elastic_modulus (MPa), poissons_ratio (dimensionless), and
        thickness (cm) defined.

    Returns
    -------
    ufloat
        Shear stiffness κ*A55 in N/mm with associated uncertainty.
        Returns ufloat(NaN, NaN) if any required layer properties are missing
        or invalid.

    Notes
    -----
    The shear stiffness is calculated using the weighted integration of
    individual layer shear moduli (Equation 8d in Weißgraeber & Rosendahl 2023):

    A55 = ∫_{-h/2}^{h/2} G(z) dz = Σ_{i=1}^{N} G_i * h_i

    where:
    - G_i is the shear modulus of layer i [MPa]
    - h_i is the thickness of layer i [mm]
    - N is the number of layers in the slab

    The shear modulus G_i should be provided directly in the Layer object.

    Shear Correction Factor:
    The shear correction factor κ = 5/6 is applied to account for the
    non-uniform shear stress distribution through the beam thickness. This
    factor is appropriate for rectangular cross-sections and provides a good
    approximation for layered slabs (Klarmann & Schweizerhof 1993).

    The final output is κ*A55, which appears in the constitutive equations
    for the shear force V(x) in the beam model.

    Theoretical Basis:
    This formula is derived from classical laminate theory with first-order
    shear deformation (Reddy 2003), applied to stratified snow covers by
    Weißgraeber & Rosendahl (2023). The integration is performed over the
    slab thickness with zeroth-order weighting.

    Unit Conversions:
    - Input elastic modulus: MPa = N/mm²
    - Input thickness: cm → mm (multiply by 10)
    - Output: N/mm

    Physical Interpretation:
    - κ*A55 represents the shear force per unit width required to produce
      unit shear strain in the slab
    - Higher values indicate a stiffer slab that resists transverse shear
      deformation
    - Shear stiffness is particularly important for thick slabs where shear
      deformation cannot be neglected (Timoshenko beam theory)
    - The shear correction factor accounts for the parabolic distribution of
      shear stress through the thickness

    Limitations
    -----------
    - Assumes isotropic elasticity (G = E/(2(1+ν)))
    - Assumes perfect bonding between layers (no slip)
    - Assumes linear elastic behavior of each layer
    - Assumes homogeneous properties within each layer
    - Shear correction factor κ = 5/6 is exact for homogeneous rectangular
      beams but approximate for layered beams
    - Does not account for temperature effects on material properties
    - Valid for small deformations only

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for 
    layered snow slabs. The Cryosphere, 17(4), 1475-1496.
    https://doi.org/10.5194/tc-17-1475-2023

    Klarmann, R., & Schweizerhof, K. (1993). A priori improvement of shear
    correction factors for the analysis of layered anisotropic shell structures.
    Archive of Applied Mechanics, 63, 73-85.
    https://doi.org/10.1007/BF00788914

    Reddy, J. N. (2003). Mechanics of Laminated Composite Plates and Shells: 
    Theory and Analysis (2nd ed.). CRC Press.
    https://doi.org/10.1201/b12409

    Timoshenko, S. P. (1921). On the correction for shear of the differential
    equation for transverse vibrations of prismatic bars. The London, Edinburgh,
    and Dublin Philosophical Magazine and Journal of Science, 41(245), 744-746.
    """
    # Validate slab input
    if not slab.layers:
        return ufloat(np.nan, np.nan)

    # Shear correction factor for rectangular cross-section
    kappa = 5.0 / 6.0

    # Initialize accumulator for A55
    A55_sum = 0.0

    # Sum contributions from each layer
    for i, layer in enumerate(slab.layers):
        # Check that required properties are present
        # Shear modulus is required (Equation 8d uses G_i directly)
        if layer.shear_modulus is None:
            return ufloat(np.nan, np.nan)
        if layer.thickness is None:
            return ufloat(np.nan, np.nan)

        # Extract layer properties
        G_i = layer.shear_modulus  # MPa = N/mm², shear modulus
        h_i = layer.thickness * 10.0  # cm → mm

        # Add contribution from this layer: G_i * h_i (Equation 8d)
        A55_sum += G_i * h_i

    # Apply shear correction factor
    return kappa * A55_sum
