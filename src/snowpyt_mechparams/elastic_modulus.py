# Methods to calculate elastic modulus of a slab layer

# Gerling et al. (2017)
# Bergfeld et al. (2023)
# Srivastava et al. (2016)
# Köchle and Schneebeli (2014)
# Wautier et al. (2015)

from math import exp
from typing import Any

from uncertainties import ufloat

def calculate_elastic_modulus(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate elastic modulus of a slab layer based on specified method and input parameters.

    Parameters
    ----------
    method : str
        Method to use for elastic modulus calculation. Available methods:
        - 'gerling': Uses Gerling et al. (2017) formula based on density
        - 'bergfeld': Uses Bergfeld et al. (2023) formula based on density
        - 'srivastava': Uses Srivastava et al. (2016) formula based on density
        - 'koechle': Uses Köchle and Schneebeli (2014) formula based on density
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
    if method.lower() == 'gerling':
        return _calculate_elastic_modulus_gerling(**kwargs)
    elif method.lower() == 'bergfeld':
        return _calculate_elastic_modulus_bergfeld(**kwargs)
    elif method.lower() == 'srivastava':
        return _calculate_elastic_modulus_srivastava(**kwargs)
    elif method.lower() == 'koechle':
        return _calculate_elastic_modulus_koechle(**kwargs)
    elif method.lower() == 'wautier':
        return _calculate_elastic_modulus_wautier(**kwargs)
    else:

        available_methods = ['gerling', 'bergfeld', 'srivastava', 'koechle', 'wautier']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )

def _calculate_elastic_modulus_gerling(density: ufloat) -> ufloat:
    """
    Calculate elastic modulus using Gerling et al. (2017) formula.
    
    This method uses the empirical relationship between snow density and elastic modulus
    developed by Gerling et al. (2017) from field measurements.
    
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
    The Gerling formula uses a power law relationship:
    E = A * (ρ/ρ_ice)^n
    where E is elastic modulus in GPa, ρ is snow density, and ρ_ice is ice density
    
    References
    ----------
    Gerling, B., Löwe, H., & van Herwijnen, A. (2017). Measuring the elastic 
    modulus of snow. Geophysical Research Letters, 44(21), 11088-11096.
    """
    # Constants from Gerling et al. (2017)
    # E = 68.8 * (ρ/ρ_ice)^2.02 (in GPa)
    A = 68.8  # GPa
    n = 2.02
    rho_ice = 917.0  # kg/m³
    
    # Calculate relative density
    relative_density = density / rho_ice
    
    # Calculate elastic modulus in GPa
    E = A * (relative_density ** n)
    
    return E

def _calculate_elastic_modulus_bergfeld(density: ufloat) -> ufloat:
    """
    Calculate elastic modulus using Bergfeld et al. (2023) formula.
    
    This method uses the empirical relationship developed by Bergfeld et al. (2023)
    based on extensive laboratory and field measurements.
    
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
    
    References
    ----------
    Bergfeld, B., van Herwijnen, A., Reuter, B., Bobillier, G., Dual, J., & 
    Schweizer, J. (2023). Dynamic anticrack propagation in snow. Nature 
    communications, 14(1), 293.
    """
    # Constants from Bergfeld et al. (2023)
    # E = 0.0024 * exp(0.0138 * ρ) (in GPa)
    A = 0.0024  # GPa
    B = 0.0138  # 1/(kg/m³)
    
    # Calculate elastic modulus in GPa
    E = A * exp(B * density.nominal_value)
    
    # Propagate uncertainty using simple approximation
    # dE/dρ = A * B * exp(B * ρ) = B * E
    E_uncertainty = B * E * density.std_dev
    
    return ufloat(E, E_uncertainty)

def _calculate_elastic_modulus_srivastava(density: ufloat) -> ufloat:
    """
    Calculate elastic modulus using Srivastava et al. (2016) formula.
    
    This method uses the relationship developed by Srivastava et al. (2016) based
    on microstructural analysis and mechanical testing.
    
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
    The Srivastava formula uses a cubic relationship:
    E = A * (ρ/ρ_ice)^3
    where E is elastic modulus in GPa, ρ is snow density, and ρ_ice is ice density
    
    References
    ----------
    Srivastava, P. K., Chandel, C., Mahajan, P., & Pankaj, P. (2016). 
    Prediction of anisotropic elastic properties of snow from its 
    microstructure. Cold Regions Science and Technology, 125, 85-100.
    """
    # Constants from Srivastava et al. (2016)
    # E = 9.0 * (ρ/ρ_ice)^3 (in GPa)
    A = 9.0  # GPa
    n = 3.0
    rho_ice = 917.0  # kg/m³
    
    # Calculate relative density
    relative_density = density / rho_ice
    
    # Calculate elastic modulus in GPa
    E = A * (relative_density ** n)
    
    return E

def _calculate_elastic_modulus_koechle(density: ufloat) -> ufloat:
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
    """
    Calculate elastic modulus using Wautier et al. (2015) formula.
    
    This method uses the numerical homogenization approach developed by Wautier 
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
    # E = 10.2 * (ρ/ρ_ice)^2.94 (in GPa)
    A = 10.2  # GPa
    n = 2.94
    rho_ice = 917.0  # kg/m³
    
    # Calculate relative density
    relative_density = density / rho_ice
    
    # Calculate elastic modulus in GPa
    E = A * (relative_density ** n)
    
    return E