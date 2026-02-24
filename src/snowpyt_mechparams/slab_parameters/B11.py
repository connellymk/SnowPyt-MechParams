# Methods to calculate bending-extension coupling stiffness (B11) of a layered slab

from typing import Any

from uncertainties import ufloat

from snowpyt_mechparams.data_structures import Slab
from snowpyt_mechparams.slab_parameters._common import integrate_plane_strain_over_layers


def calculate_B11(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate bending-extension coupling stiffness of a layered slab based on
    specified method and input parameters.

    The bending-extension coupling stiffness B11 represents the coupling between
    in-plane forces and bending moments in asymmetrically layered slabs. It is
    analogous to the bending-extension coupling in bimetal bars. For symmetric
    layering, B11 = 0.

    Parameters
    ----------
    method : str
        Method to use for B11 calculation. Available methods:
        - 'weissgraeber_rosendahl': Uses Weißgraeber & Rosendahl (2023)
          formulation based on classical laminate theory applied to layered
          snow slabs with plane-strain assumptions

    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated bending-extension coupling stiffness in N with associated
        uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_B11_weissgraeber_rosendahl(**kwargs)
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_B11_weissgraeber_rosendahl(slab: Slab) -> ufloat:
    """
    Calculate bending-extension coupling stiffness using Weißgraeber & Rosendahl
    (2023) formulation based on classical laminate theory.

    This method calculates the bending-extension coupling stiffness of a
    layered slab by integrating the plane-strain elastic modulus weighted by
    the distance from the neutral axis over the slab thickness. The formulation
    applies classical laminate theory (from composite mechanics) to stratified
    snow covers, capturing the coupling effects that arise from asymmetric
    layering.

    Parameters
    ----------
    slab : Slab
        Slab object containing ordered layers from top to bottom, where each
        layer has elastic_modulus (MPa), poissons_ratio (dimensionless), and
        thickness (cm) defined.

    Returns
    -------
    ufloat
        Bending-extension coupling stiffness B11 in N with associated uncertainty.
        Returns ufloat(NaN, NaN) if any required layer properties are missing
        or invalid.

    Notes
    -----
    The bending-extension coupling stiffness is calculated using the weighted
    integration of individual layer stiffness properties (Equation 8b in
    Weißgraeber & Rosendahl 2023):

    B11 = ∫_{-h/2}^{h/2} E(z)/(1-ν(z)²) * z dz = (1/2) * Σ_{i=1}^{N} E_i/(1-ν_i²) * (z_{i+1}² - z_i²)

    where:
    - E_i is the elastic (Young's) modulus of layer i [MPa]
    - ν_i is Poisson's ratio of layer i [dimensionless]
    - z_i, z_{i+1} are the vertical coordinates of the bottom and top of layer i [mm]
    - N is the number of layers in the slab
    - z = 0 is at the centroid (geometric center) of the slab
    - z increases upward (toward the surface)

    The term E/(1-ν²) represents the plane-strain elastic modulus. The linear
    z weighting creates coupling between extension and bending.

    Theoretical Basis:
    This formula is derived from classical laminate theory as presented in
    composite mechanics textbooks (Jones 1998, Reddy 2003), applied to
    stratified snow covers by Weißgraeber & Rosendahl (2023). The integration
    is performed over the slab thickness with first-order weighting (z),
    which captures the first moment of area contribution of each layer.

    Physical Interpretation:
    - B11 represents the coupling between in-plane normal forces and bending
      moments in the constitutive equations
    - B11 = 0 for symmetric layering (e.g., homogeneous slab or symmetric
      sandwich structure)
    - B11 ≠ 0 for asymmetric layering (e.g., hard layer on top, soft layer
      on bottom)
    - Positive B11: stiffer layers are above the centroid
    - Negative B11: stiffer layers are below the centroid
    - An applied in-plane force will induce bending (and vice versa) when B11 ≠ 0
    - This coupling is analogous to thermal bending in bimetal strips

    Coordinate System:
    - The origin (z = 0) is at the geometric centroid of the slab
    - For a slab with total thickness h, z ranges from -h/2 (bottom) to +h/2 (top)
    - Layers are ordered from top to bottom in the Slab object
    - Layer boundaries are calculated based on cumulative thickness from the top

    Unit Conversions:
    - Input elastic modulus: MPa = N/mm²
    - Input thickness: cm → mm (multiply by 10)
    - z-coordinates: mm
    - Output: N (note: different from A11 and D11)

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

    Example
    -------
    For a two-layer slab with a stiff layer on top and soft layer on bottom:
    - The stiff layer (above centroid, z > 0) contributes positive terms
    - The soft layer (below centroid, z < 0) contributes smaller negative terms
    - Net result: B11 > 0
    - Physical meaning: tension causes upward bending, compression causes
      downward bending

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
    def _accumulate_B11(plane_strain_modulus, z_top, z_bottom):
        # B11: first-order weighting — (1/2) * Ē * (z_top² - z_bottom²)
        return 0.5 * plane_strain_modulus * (z_top ** 2 - z_bottom ** 2)

    return integrate_plane_strain_over_layers(slab, _accumulate_B11)
