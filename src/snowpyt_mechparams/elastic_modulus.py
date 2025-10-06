# Methods to calculate elastic modulus of a slab layer

# Bergfeld et al. (2023)  ###
# Köchle and Schneebeli (2014)
# Wautier et al. (2015) ###

from math import exp
import numpy as np
from typing import Any

from uncertainties import ufloat

def calculate_elastic_modulus(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate elastic modulus of a slab layer based on specified method and input parameters.

    Parameters
    ----------
    method : str
        Method to use for elastic modulus calculation. Available methods:
        - 'bergfeld': Uses Bergfeld et al. (2023) formula based on density
        - 'kochle': Uses Köchle and Schneebeli (2014) formula based on density
        - 'wautier': Uses Wautier et al. (2015) formula based on density
    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated elastic modulus in GPa with associated uncertainty

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

        available_methods = ['gerling', 'bergfeld', 'srivastava', 'koechle', 'wautier']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )

def _calculate_elastic_modulus_bergfeld(density: ufloat, grain_form: str) -> ufloat:
    """
    Calculate elastic modulus using Bergfeld et al. (2023) formula.
    
    This method uses the empirical relationship developed by Bergfeld et al. (2023)
    based on extensive laboratory and field measurements. The form of the parametrization is based on 
    the Gerling et al. (2017) paper.
    
    Parameters
    ----------
    density : ufloat
        Snow density in kg/m³ with associated uncertainty
        
    Returns
    -------
    ufloat
        Elastic modulus in GPa with associated uncertainty
        
    Notes
    -----
    The Bergfeld formula uses an exponential relationship:
    E = A * exp(B * ρ)
    where E is elastic modulus in GPa and ρ is snow density in kg/m³

    Limitations
    -----------
    -Only valid for rounded grain types (RG)


    References
    ----------
    Bergfeld, B., van Herwijnen, A., Reuter, B., Bobillier, G., Dual, J., & 
    Schweizer, J. (2023). Dynamic anticrack propagation in snow. Nature 
    communications, 14(1), 293.
    """

    rho = density # kg/m³, input
    rho_ice = 917.0  # kg/m³

    # Constants from Bergfeld et al. (2023)
    C0 = 6.5e3  # MPa, fixed from Gerling (2017) eqn (6) ??
    C1 = 4.4 # From appendix B of Bergfeld et al. (2023), NOTE: How to include +/- as uncertainty?

    
    # Calculate elastic modulus in GPa if grain form is RG
    if grain_form == 'RG':
        E = C0 * (rho / rho_ice) ** C1
    else:
        E = ufloat(np.nan, np.nan)
    
    return E

def _calculate_elastic_modulus_kochle(density: ufloat) -> ufloat:
    """
    Calculate elastic modulus using Köchle and Schneebeli (2014) formula.
    
    This method uses the relationship developed by Köchle and Schneebeli (2014)
    based on microtomography and finite element analysis.
    
    Parameters
    ----------
    density : ufloat
        Snow density in kg/m³ with associated uncertainty
        
    Returns
    -------
    ufloat
        Elastic modulus in GPa with associated uncertainty
        
    Notes
    -----
    The Köchle-Schneebeli formula uses a power law relationship:
    E = A * (ρ/ρ_ice)^n
    where E is elastic modulus in GPa, ρ is snow density, and ρ_ice is ice density
    
    References
    ----------
    Köchle, B., & Schneebeli, M. (2014). Three‐dimensional microstructure and 
    numerical calculation of elastic properties of alpine snow with a focus 
    on weak layers. Journal of Glaciology, 60(222), 705-713.
    """
    # Constants from Köchle and Schneebeli (2014)
    # E = 4.5 * (ρ/ρ_ice)^1.9 (in GPa)
    A = 4.5  # GPa
    n = 1.9
    rho_ice = 917.0  # kg/m³
    
    # Calculate relative density
    relative_density = density / rho_ice
    
    # Calculate elastic modulus in GPa
    E = A * (relative_density ** n)
    
    return E

def _calculate_elastic_modulus_wautier(density: ufloat) -> ufloat:
    # NOTE: Add eleastic modulus of ice as input, with default from Kermani paper
    """
    Calculate elastic modulus using Wautier et al. (2015) formula.
    
    This method uses the numerical homogenization approach (eqn 5)developed by Wautier 
    et al. (2015) to relate snow microstructure to macroscopic elastic properties.
    
    Parameters
    ----------
    density : ufloat
        Snow density in kg/m³ with associated uncertainty
        
    Returns
    -------
    ufloat
        Elastic modulus in GPa with associated uncertainty
        
    Notes
    -----
    The Wautier formula uses a power law relationship derived from 
    three-dimensional numerical homogenization:
    E = A * (ρ/ρ_ice)^n
    where E is elastic modulus in GPa, ρ is snow density, and ρ_ice is ice density
    
    References
    ----------
    Wautier, A., Geindreau, C., & Flin, F. (2015). Linking snow microstructure 
    to its macroscopic elastic stiffness tensor: A numerical homogenization 
    method and its application to 3‐D images from X‐ray tomography. 
    Geophysical Research Letters, 42(19), 8031-8041.
    """
    # Constants from Wautier et al. (2015)
    E_ice = ufloat(1.06, 0.19) # GPa from Kermani paper NOTE: ADD CITATION and review
    # BEnding strength and effetive modulus of atmospheric ice
    A = 0.78  # GPa
    n = 2.34
    rho_ice = 917.0  # kg/m³
    
    # Calculate relative density
    relative_density = density / rho_ice
    
    # Calculate elastic modulus in GPa
    E = E_ice * A * (relative_density ** n) # R^2 is 0.97, convert to uncertainty
    
    return E