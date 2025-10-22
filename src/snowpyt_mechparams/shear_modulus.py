# Methods to calculate shear modulus of a slab layer

# Wautier et al. (2015)

import numpy as np
from typing import Any

from uncertainties import ufloat

def calculate_shear_modulus(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate shear modulus of a slab layer based on specified method and
    input parameters.

    Parameters
    ----------
    method : str
        Method to use for shear modulus calculation. Available methods:
        - 'wautier': Uses Wautier et al. (2015) power-law formula based on 
          density and the shear modulus of ice
    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated shear modulus in MPa with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'wautier':
        return _calculate_shear_modulus_wautier(**kwargs)
    elif method.lower() == 'from_elastic_modulus_and_poissons_ratio':
        return _calculate_shear_modulus_wautier_from_elastic_modulus_and_poissons_ratio(**kwargs)
    else:
        available_methods = ['wautier', 'from_elastic_modulus_and_poissons_ratio']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )

def _calculate_shear_modulus_wautier(density: ufloat, grain_form: str, G_ice: ufloat = ufloat(407.7, 65.4)) -> ufloat:
    """
    Calculate the normalized average shear modulus (G) using the power-law
    relationship fitted by Wautier et al. (2015).
    
    This relationship is derived from numerical homogenization calculations of the
    elastic stiffness tensor over 3-D X-ray microtomography images of snow.
    
    Parameters
    ----------
    density : ufloat
        Snow density (ρ_snow) in kg/m³ with associated uncertainty
    grain_form : str
        Grain form classification. Supported values:
        - 'DF', 'RG', 'FC', 'DH', 'MF'
    G_ice : ufloat, optional
        Shear modulus of ice in MPa with associated uncertainty.
        Default is 407.7 ± 65.4 MPa (0.41 ± 0.07 GPa), calculated from the
        elastic modulus of ice E_ice = 1060 ± 170 MPa (1.06 ± 0.17 GPa) and
        Poisson's ratio ν_ice = 0.3 using G = E / (2 * (1 + ν)).
        
    Returns
    -------
    ufloat
        Average shear modulus (G_snow) in MPa with associated uncertainty
        
    Notes
    -----
    The relationship found to correlate well (R² = 0.97) between normalized
    average shear modulus (G_snow) and relative density is a power law (Eq. 5):
    
    G_snow / G_ice = A * (ρ_snow / ρ_ice)^n
    
    Where:
    A = 0.92
    n = 2.51
    
    The default G_ice value (0.41 ± 0.07 GPa) is derived from the relationship
    G = E / (2 * (1 + ν)) using E_ice = 1.06 ± 0.17 GPa (the effective modulus
    of atmospheric ice accumulated and tested at -10°C, reported by Kermani et al.
    (2008)) and ν_ice = 0.3 (standard Poisson's ratio for ice).
    
    Constants Used for Calculation:
    ρ_ice = 917.0 kg m⁻³

    Limitations
    -----------
    - The correlation is based on calculated mechanical properties derived from
      Finite Element (FE) simulations assuming the ice skeleton is a
      homogeneous, isotropic elastic material with a Poisson's ratio (ν_ice)
      of 0.3.
    - The fitting parameter (G_snow) represents the normalized *average*
      shear modulus. The fit does not capture the orthotropic (anisotropic)
      behavior often observed in snow, which can lead to significant deviation
      from directional moduli.
    - The fit applies for relative density (ρ_snow / ρ_ice) in the range [0.1;
      0.6], corresponding approximately to densities from 103 to 544 kg m⁻³.
    - The shear modulus calculation assumes isotropic elastic behavior, which
      may not be appropriate for highly anisotropic snow layers.
    - The calculation relies on the assumption that snow behaves as a linear
      elastic material, which may not be valid at all strain rates or stress
      levels.

    References
    ----------
    Wautier, A., Geindreau, C., and Flin, F. (2015). Linking snow microstructure
    to its macroscopic elastic stiffness tensor: A numerical homogenization
    method and its application to 3-D images from X-ray tomography.
    Geophysical Research Letters, 42, 8031–8041.
    
    Kermani, M., Farzaneh, M., and Gagnon, R. (2008). Bending strength and
    effective modulus of atmospheric ice. Cold Regions Science and Technology,
    53(2), 162–169.
    """
    
    # Validate grain form
    main_grain_shape = grain_form[:2]
    if main_grain_shape not in ['DF', 'RG', 'FC', 'DH', 'MF']:
        return ufloat(np.nan, np.nan)
    
    rho_snow = density  # kg/m³, input
    
    # Constants for Ice
    rho_ice = 917.0  # kg/m³ 

    # Check for nominal density in range of fit
    if rho_snow.nominal_value < 103 or rho_snow.nominal_value > 544:
        G_snow = ufloat(np.nan, np.nan)
    else:
        # Wautier et al. (2015) power law coefficients (Eq. 5)
        A = ufloat(0.92, 0.0) 
        n = ufloat(2.51, 0.0) 

        # Calculate shear modulus (G_snow / G_ice = A * (ρ_snow / ρ_ice)^n)
        # G_snow = G_ice * A * (ρ_snow / ρ_ice)^n
        G_snow = G_ice * (A * ((rho_snow / rho_ice) ** n))
    
    return G_snow

def _calculate_shear_modulus_wautier_from_elastic_modulus_and_poissons_ratio(elastic_modulus: ufloat, poissons_ratio: ufloat) -> ufloat:
    """
    Calculate the shear modulus (G) using the elastic modulus and Poisson's ratio.
    
    This method uses the standard elastic relationship for isotropic materials:
    G = E / (2 * (1 + ν))
    
    Parameters
    ----------
    elastic_modulus : ufloat
        Elastic modulus (E) in MPa with associated uncertainty
    poissons_ratio : ufloat
        Poisson's ratio (ν) with associated uncertainty
        
    Returns
    -------
    ufloat
        Shear modulus (G) in MPa with associated uncertainty
    """
    
    # Calculate shear modulus: G = E / (2 * (1 + ν))
    G_snow = elastic_modulus / (2.0 * (1.0 + poissons_ratio))
    
    return G_snow

