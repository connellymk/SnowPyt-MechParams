# Methods to calculate extensional stiffness (A11) of a layered slab

from typing import Any

import numpy as np
from uncertainties import ufloat

from data_structures.data_structures import Slab


def calculate_A11(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate extensional stiffness of a layered slab based on specified method
    and input parameters.

    The extensional stiffness A11 represents the slab's resistance to in-plane
    normal forces (tension or compression). It is a fundamental mechanical property
    used in beam-on-elastic-foundation models for snow slab avalanche mechanics.

    Parameters
    ----------
    method : str
        Method to use for A11 calculation. Available methods:
        - 'weissgraeber_rosendahl': Uses Weißgraeber & Rosendahl (2023) 
          formulation based on classical laminate theory applied to layered
          snow slabs with plane-strain assumptions

    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated extensional stiffness in N/mm with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_A11_weissgraeber_rosendahl(**kwargs)
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_A11_weissgraeber_rosendahl(slab: Slab) -> ufloat:
    """
    Calculate extensional stiffness using Weißgraeber & Rosendahl (2023)
    formulation based on classical laminate theory.

    This method calculates the extensional stiffness of a layered slab by
    integrating the plane-strain elastic modulus over the slab thickness.
    The formulation applies classical laminate theory (from composite mechanics)
    to stratified snow covers, accounting for the mechanical properties of
    individual layers.

    Parameters
    ----------
    slab : Slab
        Slab object containing ordered layers from top to bottom, where each
        layer has elastic_modulus (MPa), poissons_ratio (dimensionless), and
        thickness (cm) defined.

    Returns
    -------
    ufloat
        Extensional stiffness A11 in N/mm with associated uncertainty.
        Returns ufloat(NaN, NaN) if any required layer properties are missing
        or invalid.

    Notes
    -----
    The extensional stiffness is calculated using the weighted integration of
    individual layer stiffness properties (Equation 8a in Weißgraeber & 
    Rosendahl 2023):

    A11 = ∫_{-h/2}^{h/2} E(z)/(1-ν(z)²) dz = Σ_{i=1}^{N} E_i/(1-ν_i²) * h_i

    where:
    - E_i is the elastic (Young's) modulus of layer i [MPa]
    - ν_i is Poisson's ratio of layer i [dimensionless]
    - h_i is the thickness of layer i [mm]
    - N is the number of layers in the slab

    The term E/(1-ν²) represents the plane-strain elastic modulus, which
    accounts for the constraint that the slab cannot deform in the
    out-of-plane direction (plane-strain condition).

    Theoretical Basis:
    This formula is derived from classical laminate theory as presented in
    composite mechanics textbooks (Jones 1998, Reddy 2003), applied to
    stratified snow covers by Weißgraeber & Rosendahl (2023). The integration
    is performed over the slab thickness with zeroth-order weighting (constant
    over each layer).

    Unit Conversions:
    - Input elastic modulus: MPa = N/mm²
    - Input thickness: cm → mm (multiply by 10)
    - Output: N/mm

    Physical Interpretation:
    - A11 represents the force per unit width required to produce unit
      in-plane strain in the slab
    - Higher values indicate a stiffer slab that resists in-plane deformation
    - Layering effects are captured through the summation over all layers
    - Each layer contributes proportionally to its stiffness and thickness

    Limitations
    -----------
    - Assumes plane-strain conditions (no out-of-plane deformation)
    - Assumes perfect bonding between layers (no slip)
    - Assumes linear elastic behavior of each layer
    - Assumes homogeneous and isotropic properties within each layer
    - Does not account for temperature effects on material properties
    - Valid for small deformations only

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for 
    layered snow slabs. The Cryosphere, 17(4), 1475-1496.
    https://doi.org/10.5194/tc-17-1475-2023

    Jones, R. M. (1998). Mechanics of composite materials (2nd ed.). CRC Press.
    https://doi.org/10.1201/9781498711067

    Reddy, J. N. (2003). Mechanics of Laminated Composite Plates and Shells: 
    Theory and Analysis (2nd ed.). CRC Press.
    https://doi.org/10.1201/b12409
    """
    # Validate slab input
    if not isinstance(slab, Slab):
        return ufloat(np.nan, np.nan)

    if not slab.layers or len(slab.layers) == 0:
        return ufloat(np.nan, np.nan)

    # Initialize accumulator for A11
    A11_sum = 0.0

    # Sum contributions from each layer
    for i, layer in enumerate(slab.layers):
        # Check that all required properties are present
        if layer.elastic_modulus is None:
            return ufloat(np.nan, np.nan)
        if layer.poissons_ratio is None:
            return ufloat(np.nan, np.nan)
        if layer.thickness is None:
            return ufloat(np.nan, np.nan)

        # Extract layer properties
        E_i = layer.elastic_modulus  # MPa = N/mm²
        nu_i = layer.poissons_ratio  # dimensionless
        h_i = layer.thickness * 10.0  # cm → mm

        # Check for valid Poisson's ratio (must be < 1 to avoid division issues)
        if hasattr(nu_i, 'nominal_value'):
            nu_val = nu_i.nominal_value
        else:
            nu_val = nu_i

        if nu_val >= 1.0 or nu_val < -1.0:
            return ufloat(np.nan, np.nan)

        # Calculate plane-strain modulus term: E_i / (1 - ν_i²)
        plane_strain_modulus = E_i / (1.0 - nu_i**2)

        # Add contribution from this layer: [E_i / (1 - ν_i²)] * h_i
        A11_sum += plane_strain_modulus * h_i

    return A11_sum
