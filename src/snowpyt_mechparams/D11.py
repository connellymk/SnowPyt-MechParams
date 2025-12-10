# Methods to calculate bending stiffness (D11) of a layered slab

from typing import Any

import numpy as np
from uncertainties import ufloat

from data_structures.data_structures import Slab


def calculate_D11(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate bending stiffness of a layered slab based on specified method
    and input parameters.

    The bending stiffness D11 represents the slab's resistance to bending
    moments. It is a fundamental mechanical property used in beam-on-elastic-
    foundation models for snow slab avalanche mechanics.

    Parameters
    ----------
    method : str
        Method to use for D11 calculation. Available methods:
        - 'weissgraeber_rosendahl': Uses Weißgraeber & Rosendahl (2023) 
          formulation based on classical laminate theory applied to layered
          snow slabs with plane-strain assumptions

    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated bending stiffness in N·mm with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_D11_weissgraeber_rosendahl(**kwargs)
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_D11_weissgraeber_rosendahl(slab: Slab) -> ufloat:
    """
    Calculate bending stiffness using Weißgraeber & Rosendahl (2023) formulation
    based on classical laminate theory.

    This method calculates the bending stiffness of a layered slab by
    integrating the plane-strain elastic modulus weighted by the square of
    the distance from the neutral axis over the slab thickness. The formulation
    applies classical laminate theory (from composite mechanics) to stratified
    snow covers, accounting for the position of each layer relative to the
    neutral axis.

    Parameters
    ----------
    slab : Slab
        Slab object containing ordered layers from top to bottom, where each
        layer has elastic_modulus (MPa), poissons_ratio (dimensionless), and
        thickness (cm) defined.

    Returns
    -------
    ufloat
        Bending stiffness D11 in N·mm with associated uncertainty.
        Returns ufloat(NaN, NaN) if any required layer properties are missing
        or invalid.

    Notes
    -----
    The bending stiffness is calculated using the weighted integration of
    individual layer stiffness properties (Equation 8c in Weißgraeber & 
    Rosendahl 2023):

    D11 = ∫_{-h/2}^{h/2} E(z)/(1-ν(z)²) * z² dz = (1/3) * Σ_{i=1}^{N} E_i/(1-ν_i²) * (z_{i+1}³ - z_i³)

    where:
    - E_i is the elastic (Young's) modulus of layer i [MPa]
    - ν_i is Poisson's ratio of layer i [dimensionless]
    - z_i, z_{i+1} are the vertical coordinates of the bottom and top of layer i [mm]
    - N is the number of layers in the slab
    - z = 0 is at the centroid (geometric center) of the slab
    - z increases upward (toward the surface)

    The term E/(1-ν²) represents the plane-strain elastic modulus. The z²
    weighting reflects the fact that material farther from the neutral axis
    contributes more to bending resistance.

    Theoretical Basis:
    This formula is derived from classical laminate theory as presented in
    composite mechanics textbooks (Jones 1998, Reddy 2003), applied to
    stratified snow covers by Weißgraeber & Rosendahl (2023). The integration
    is performed over the slab thickness with second-order weighting (z²),
    which captures the moment of inertia contribution of each layer.

    Coordinate System:
    - The origin (z = 0) is at the geometric centroid of the slab
    - For a slab with total thickness h, z ranges from -h/2 (bottom) to +h/2 (top)
    - Layers are ordered from top to bottom in the Slab object
    - Layer boundaries are calculated based on cumulative thickness from the top

    Unit Conversions:
    - Input elastic modulus: MPa = N/mm²
    - Input thickness: cm → mm (multiply by 10)
    - z-coordinates: mm
    - Output: N·mm

    Physical Interpretation:
    - D11 represents the bending moment per unit width required to produce
      unit curvature in the slab
    - Higher values indicate a stiffer slab that resists bending
    - Bending stiffness increases with the cube of the distance from the
      neutral axis, making layer position critical
    - Layering effects can be dramatic: a stiff layer far from the centroid
      contributes much more than the same layer near the centroid

    Limitations
    -----------
    - Assumes plane-strain conditions (no out-of-plane deformation)
    - Assumes perfect bonding between layers (no slip)
    - Assumes linear elastic behavior of each layer
    - Assumes homogeneous and isotropic properties within each layer
    - Assumes small deformations (linear beam theory)
    - Does not account for temperature effects on material properties
    - The neutral axis is assumed to be at the geometric centroid, which is
      exact only for symmetric layering or uniform properties

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
    if not slab.layers:
        return ufloat(np.nan, np.nan)

    # Calculate total slab thickness
    total_thickness = slab.total_thickness
    if total_thickness is None:
        return ufloat(np.nan, np.nan)

    # Convert to mm
    h_total = total_thickness * 10.0  # cm → mm

    # Initialize accumulator for D11
    D11_sum = 0.0

    # Calculate z-coordinates for each layer
    # z = 0 at centroid, z = h/2 at top surface, z = -h/2 at bottom
    z_top_surface = h_total / 2.0  # mm from centroid to top surface

    # Track cumulative depth from top surface
    depth_from_top = 0.0  # mm

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

        # Check for valid Poisson's ratio
        if hasattr(nu_i, 'nominal_value'):
            nu_val = nu_i.nominal_value
        else:
            nu_val = nu_i

        if nu_val >= 1.0 or nu_val < -1.0:
            return ufloat(np.nan, np.nan)

        # Calculate z-coordinates of layer boundaries (from centroid)
        # Top of this layer
        z_i_plus_1 = z_top_surface - depth_from_top
        # Bottom of this layer
        z_i = z_top_surface - (depth_from_top + h_i)

        # Update depth for next layer
        depth_from_top += h_i

        # Calculate plane-strain modulus term: E_i / (1 - ν_i²)
        plane_strain_modulus = E_i / (1.0 - nu_i**2)

        # Add contribution from this layer: (1/3) * [E_i / (1 - ν_i²)] * (z_{i+1}³ - z_i³)
        D11_sum += (1.0 / 3.0) * plane_strain_modulus * (z_i_plus_1**3 - z_i**3)

    return D11_sum
