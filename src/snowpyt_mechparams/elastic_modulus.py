# Methods to calculate elastic modulus of a slab layer

# Bergfeld et al. (2023)  ###
# Köchle and Schneebeli (2014)
# Wautier et al. (2015) ###

import numpy as np
from typing import Any

from uncertainties import ufloat
from uncertainties import umath

def calculate_elastic_modulus(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate elastic modulus of a slab layer based on specified method and
    input parameters.

    Parameters
    ----------
    method : str
        Method to use for elastic modulus calculation. Available methods:
        - 'bergfeld': Uses Bergfeld et al. (2023) formula based on density
        - 'kochle': Uses Köchle and Schneebeli (2014) formula based on density
        - 'wautier': Uses Wautier et al. (2015) formula based on density and
          the elastic modulus of ice
    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated elastic modulus in MPa with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'bergfeld':
        return _calculate_elastic_modulus_bergfeld(**kwargs)
    elif method.lower() == 'kochle':
        return _calculate_elastic_modulus_kochle(**kwargs)
    elif method.lower() == 'wautier':
        return _calculate_elastic_modulus_wautier(**kwargs)
    else:

        available_methods = ['bergfeld', 'kochle', 'wautier']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )

def _calculate_elastic_modulus_bergfeld(density: ufloat,grain_form: str) -> ufloat:
    """
    Calculate elastic modulus using Bergfeld et al. (2023) formula.
    
    This method uses the power-law parameterization suggested by Gerling et al.
    (2017) to estimate the effective elastic modulus of individual snow layers
    based on density, optimized using mechanical models fit to Propagation Saw
    Test (PST) data. As described in Bergfeld et al. (2023).
    
    Parameters
    ----------
    density : ufloat
        Snow density in kg/m³ with associated uncertainty
    grain_form : str
        Grain form classification. Supported values:
        - 'PP', 'RG', 'DF'
        
    Returns
    -------
    ufloat
        Elastic modulus in MPa with associated uncertainty
        
    Notes
    -----
    The Bergfeld et al. (2023) study used a power-law relationship based on
    Gerling et al. (2017) (Eq. 4 in Bergfeld et al. (2023), expanded from Eq. 6
    in Gerling et al. (2017)):
    
    E = C0 * (ρ / ρ_ice) ** C1
    
    where E is elastic modulus, ρ is snow density in kg/m³, and ρ_ice = 917
    kg/m³. C0 is fixed at 6.5 MPa (Eq. 6, Gerling et al. (2017)). C1 is the
    fitted exponent (mean: 4.4, standard deviation: 0.18) (Appendix B, Bergfeld
    et al. (2023))

    - The fitted exponent C1=4.4 was derived from optimizing displacement fields
      of layered slabs during flat-field Propagation Saw Tests (PSTs).
    - The slab layers used in the optimization consisted of mixed grain types
      (fresh snow (+), decomposing particles (/), and rounded grains (•))

    Limitations
    -----------
    - The estimated parameter C1 (mean 4.4 ± 0.18) was determined as a specific
      free fitting parameter optimized using a Layered-Slab (LS) mechanical model
      against displacement fields measured during flat-field Propagation Saw
      Tests (PSTs). It may not be appropriate for other tests or models.
    - The resulting elastic modulus (Ei) should be interpreted as a
      flexural-like elastic modulus, as the optimization process in flat-field
      PSTs is dominated by vertical displacements induced by slab bending.
    - The modulus is strain-rate dependent. Since the fitting phase (sawing)
      occurs at strain rates at least 2 orders of magnitude lower than those
      during actual crack propagation, this method will likely underestimate the
      true elastic modulus needed for dynamic fracture events.
    - The density range of the mean slab densities observed during fitting was
      approximately 110 to 363 kg m⁻³.
    - The parameterization inherently assumes isotropic behavior, but a layered
      snow slab does not meet the necessary condition to be represented by a
      single effective elastic modulus. This parameterization is only
      appropriate for individual layers within a snow slab, not the entire slab
      or the weak layer.

    References
    ----------
    Bergfeld, B., van Herwijnen, A., Reuter, B., Bobillier, G., Dual, J., &
    Schweizer, J. (2023). Dynamic anticrack propagation in snow. Nature
    communications, 14(1), 293.
    """

    rho_snow = density # kg/m³, input
    rho_ice = 917.0  # kg/m³
    
    # Check grain form validity (only PP, RG, DF are supported)
    main_grain_shape = grain_form[:2]
    if main_grain_shape not in ['PP', 'RG', 'DF']:
        return ufloat(np.nan, np.nan)
    
    # Check density is within the valid range of the fit (110-363 kg/m³)
    if rho_snow.nominal_value < 110 or rho_snow.nominal_value > 363:
        return ufloat(np.nan, np.nan)
    
    # C0 is 6.5e3 MPa, (Eq. 6, Gerling et al. (2017), Eq. 4, Bergfeld et al. (2023)).
    C0 = 6.5e3  # MPa
    
    # C1 is the fitted exponent: mean 4.4, with a standard deviation of ± 0.18 (Appendix B, Bergfeld et al. (2023)).
    C1 = ufloat(4.4, 0.18) 
    
    # Calculate elastic modulus (E) in MPa based solely on density
    E_snow = C0 * (rho_snow / rho_ice) ** C1
    
    return E_snow

def _calculate_elastic_modulus_kochle(density: ufloat,grain_form: str) -> ufloat:
    """
    Calculate Young's modulus (E) using the exponential relationships fitted by
    Köchle and Schneebeli (2014).
    
    This method uses empirical fits based on Young's modulus values derived from
    X-ray microcomputer tomography (m-CT) and subsequent finite-element (FE)
    simulations of snow microstructure.
    
    Parameters
    ----------
    density : ufloat
        Snow density (ρ) in kg/m³ with associated uncertainty
    grain_form : str
        Grain form classification. Supported values:
        - 'RG', 'FC', 'DH', 'MF'
        
    Returns
    -------
    ufloat
        Young's modulus (E) in MPa with associated uncertainty
        
    Notes
    -----
    The relationship between the logarithmically transformed Young's modulus (E)
    in MPa and density (ρ) in kg/m³ is represented by two separate exponential
    fits, depending on the density range:
    
    1. Low Density (150 ≤ ρ < 250 kg/m³):
       E = 0.0061 * exp(0.0396 * ρ)  (R² = 0.68)
    
    2. High Density (250 ≤ ρ ≤ 450 kg/m³):
       E = 6.0457 * exp(0.011 * ρ) [2] (R² = 0.92)
       
    The calculated result (E_MPa) is divided by 1000 to return E in GPa.

    Limitations
    -----------
    - The correlation is based on calculated mechanical properties derived from
      FE simulations of m-CT snow geometry, not direct field or laboratory
      measurements.
    - The calculation relies on the assumption of isotropic, linear-elastic
      behavior of the underlying ice material (E_ice = 10 GPa, Poisson's ratio
      ν_ice = 0.3).
    - Calculated E values typically run higher than experimental results, which
      is attributed to viscous effects captured in low-strain-rate experimental
      methods but excluded in this linear-elastic FE approach.
    - The equations are fitted for specific density ranges: 150–250 kg/m³ (low
      density fit, lower R²) and 250–450 kg/m³ (high density fit, higher R²).
      Results outside this range (100–500 kg/m³ overall sample range) are
      extrapolated or unsupported.
    - The underlying FE calculations were based on cubic subvolumes with a
      minimum side length of 7 mm (Representative Volume Element, RVE) to
      capture elastic properties. Properties of layers thinner than 7 mm were
      not calculated [9].
    - Although the input samples contained weak layers, the calculated E value
      alone is not a sufficient indicator of weak snow; stiffness (E) should be
      assessed relative to adjacent layers ("the 'sandwich'").

    References
    ----------
    Köchle, B., & Schneebeli, M. (2014). Three-dimensional microstructure and
    numerical calculation of elastic properties of alpine snow with a focus on
    weak layers. Journal of Glaciology, 60(220), 304-315.
    """

    main_grain_shape = grain_form[:2]
    if main_grain_shape not in ['RG', 'RC', 'DH', 'MF']:
        return ufloat(np.nan, np.nan)

    rho_snow = density # kg/m³

    # Check for valid density range and apply appropriate formula (Equations 11 and 12 from source)
    if 150 <= rho_snow.nominal_value < 250:
        # Low Density Fit (R² = 0.68)
        # E = 0.0061 * exp(0.0396 * ρ)
        C_A = 0.0061
        C_B = 0.0396
        E_snow = C_A * umath.exp(C_B * rho_snow)
        
    elif 250 <= rho_snow.nominal_value <= 450:
        # High Density Fit (R² = 0.92)
        # E = 6.0457 * exp(0.011 * ρ)
        C_A = 6.0457
        C_B = 0.011
        E_snow = C_A * umath.exp(C_B * rho_snow)
    else:
        # Densities outside 150-450 kg/m³ return NaN
        E_snow = ufloat(np.nan, np.nan)
    
    return E_snow

def _calculate_elastic_modulus_wautier(density: ufloat, grain_form: str, E_ice: ufloat = ufloat(1060, 170)) -> ufloat:
    """
    Calculate the normalized average Young's modulus (E) using the power-law
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
    E_ice : ufloat, optional
        Young's modulus of ice in MPa with associated uncertainty.
        Default is 1060 ± 170 MPa (1.06 ± 0.17 GPa)
        
    Returns
    -------
    ufloat
        Average Young's modulus (E_snow) in MPa with associated uncertainty
        
    Notes
    -----
    The relationship found to correlate well (R² = 0.97) between normalized
    average Young's modulus (E_snow) and relative density is a power law (Eq. 5):
    
    E_snow / E_ice = A * (ρ_snow / ρ_ice)^n
    
    Where:
    A = 0.78 
    n = 2.34
    
    The default E_ice value (1.06 ± 0.17 GPa) is the effective modulus of
    atmospheric ice accumulated and tested at -10°C, reported by Kermani et al.
    (2008).

    Suggested values for E_ice based on source context:
    - Wautier et al. (2015) notes that E_ice is generally known to range from
      0.2 GPa to 9.5 GPa.
    - Kermani et al. (2008) references other studies on freshwater ice effective
      modulus that obtained values such as 1.6 ± 0.4 GPa and ranges between
      0.7 GPa and 10.5 GPa.
    
    Constants Used for Calculation:
    ρ_ice = 917.0 kg m⁻³

    Limitations
    -----------
    - The correlation is based on calculated mechanical properties derived from
      Finite Element (FE) simulations assuming the ice skeleton is a
      homogeneous, isotropic elastic material with a Poisson's ratio (ν_ice)
      of 0.3.
    - The fitting parameter (E_snow) represents the normalized *average*
      Young's modulus. The fit does not capture the orthotropic (anisotropic)
      behavior often observed in snow, which can lead to significant deviation
      from directional moduli.
    - The fit applies for relative density (ρ_snow / ρ_ice) in the range [0.1;
      0.6], corresponding approximately to densities from 103 to 544 kg m⁻³.

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

    main_grain_shape = grain_form[:2]
    if main_grain_shape not in ['DF', 'RG', 'FC', 'DH', 'MF']:
        return ufloat(np.nan, np.nan)

    rho_snow = density  # kg/m³, input
    
    # Constants for Ice
    rho_ice = 917.0  # kg/m³ 

    # Check for nominal density in range of fit
    if rho_snow.nominal_value < 103 or rho_snow.nominal_value > 544:
        E_snow = ufloat(np.nan, np.nan)
    else:
        # Wautier et al. (2015) power law coefficients (Eq. 5)
        A = ufloat(0.78, 0.0) 
        n = ufloat(2.34, 0.0) 

        # Calculate normalized Young's Modulus (E_snow / E_ice)
        # E_snow = E_ice * A * (ρ_snow / ρ_ice)^n
        E_snow = E_ice * A * ((rho_snow / rho_ice) ** n)
    
    return E_snow