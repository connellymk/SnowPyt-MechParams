# Methods to calculate Poisson's ratio (ν) of a slab layer

# Köchle and Schneebeli (2014)
# Srivastava et al. (2016)
# Wautier et al. (2015)

import logging
import numpy as np
from typing import Any

from uncertainties import ufloat

logger = logging.getLogger(__name__)

def calculate_poissons_ratio(method: str, include_method_uncertainty: bool = True, **kwargs: Any) -> ufloat:
    """
    Calculate Poisson's ratio of a slab layer based on specified method and
    input parameters.

    Parameters
    ----------
    method : str
        Method to use for Poisson's ratio calculation. Available methods:
        - 'kochle': Uses Köchle and Schneebeli (2014) formula
        - 'srivastava': Uses Srivastava et al. (2016) formula
    include_method_uncertainty : bool, optional
        Whether to include the uncertainty inherent to the empirical method
        (e.g. grain-type standard deviations from FE simulations). Default is
        True. If False, the nominal value is unchanged but no method
        uncertainty is added; input uncertainties still propagate normally.
    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated Poisson's ratio (dimensionless) with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'kochle':
        return _calculate_poissons_ratio_kochle(include_method_uncertainty=include_method_uncertainty, **kwargs)
    elif method.lower() == 'srivastava':
        return _calculate_poissons_ratio_srivastava(include_method_uncertainty=include_method_uncertainty, **kwargs)
    else:
        available_methods = ['kochle', 'srivastava']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )

def _calculate_poissons_ratio_kochle(grain_form: str, include_method_uncertainty: bool = True) -> ufloat:
    """
    Calculate Poisson's ratio using Köchle and Schneebeli (2014) grain-type-
    specific mean values.
    
    This method uses mean Poisson's ratio values derived from X-ray
    microcomputer tomography (m-CT) and subsequent finite-element (FE)
    simulations of snow microstructure. Unlike Young's modulus, Poisson's ratio
    shows less density dependence and is characterized primarily by grain type.
    
    Parameters
    ----------
    grain_form : str
        Grain form classification. Supported values:
        - ['RG', 'FC', 'DH']
        
    Returns
    -------
    ufloat
        Poisson's ratio (dimensionless) with associated uncertainty
        
    Notes
    -----
    The Poisson's ratio values are grain-type-specific mean values calculated
    from FE simulations of 3-D snow microstructure obtained through m-CT
    imaging. The values represent:
    
    - Rounded Grains (RG): ν = 0.171 ± 0.026 (n = 17)
    - Faceted Crystals (FC): ν = 0.130 ± 0.040 (n = 19)
    - Depth Hoar (DH): ν = 0.087 ± 0.063 (n = 6)
    
    The reported uncertainties represent the standard deviation of the
    calculated values for each grain type. These values were calculated using
    the same methodology as Young's modulus, based on numerical homogenization
    of the elastic stiffness tensor.
    
    Limitations
    -----------
    - The values are based on calculated mechanical properties derived from FE
      simulations of m-CT snow geometry, not direct field or laboratory
      measurements.
    - The calculation relies on the assumption of isotropic, linear-elastic
      behavior of the underlying ice material (E_ice = 10 GPa, Poisson's ratio
      ν_ice = 0.3).
    - The values represent mean properties for each grain type and do not
      account for density variations within each grain type category.
    - The underlying FE calculations were based on cubic subvolumes with a
      minimum side length of 7 mm (Representative Volume Element, RVE) to
      capture elastic properties. Properties of layers thinner than 7 mm were
      not calculated.
    - The relatively large standard deviations (especially for DH) indicate
      significant variability within each grain type category, reflecting the
      natural heterogeneity of snow microstructure.
    - Although MF grain types were included in the study, and the results are shown in fig. 4,
      the authors did not provide the mean Poisson's ratio values for this grain type.
    
    References
    ----------
    Köchle, B., & Schneebeli, M. (2014). Three-dimensional microstructure and
    numerical calculation of elastic properties of alpine snow with a focus on
    weak layers. Journal of Glaciology, 60(220), 304-315.
    """
    
    main_grain_shape = grain_form[:2]
    if main_grain_shape not in ['RG', 'FC', 'DH']:
        logger.debug("kochle: unsupported grain_form=%r (main_grain_shape=%r)", grain_form, main_grain_shape)
        return ufloat(np.nan, np.nan)
    
    _u = lambda val, std: ufloat(val, std if include_method_uncertainty else 0.0)
    if main_grain_shape == 'RG':
        nu_snow = _u(0.171, 0.026)
    elif main_grain_shape == 'FC':
        nu_snow = _u(0.130, 0.040)
    elif main_grain_shape == 'DH':
        nu_snow = _u(0.087, 0.063)

    return nu_snow

def _calculate_poissons_ratio_srivastava(density: ufloat, grain_form: str, include_method_uncertainty: bool = True) -> ufloat:
    """
    Calculate Poisson's ratio using Srivastava et al. (2016) grain-type-specific
    mean values.
    
    This method uses effective isotropic Poisson's ratio values derived from
    micromechanical modeling of snow microstructure using X-ray micro-computed
    tomography (μCT) and finite element analysis.
    
    Parameters
    ----------
    density : ufloat
        Snow density (ρ) in kg/m³ with associated uncertainty
    grain_form : str
        Grain form classification. Supported values:
        - ['RG', 'PP', 'DF', 'FC', 'DH']
        
    Returns
    -------
    ufloat
        Poisson's ratio (dimensionless) with associated uncertainty
        
    Notes
    -----
    The effective isotropic Poisson's ratio showed no clear trend with density
    in the Srivastava et al. (2016) study. The values represent grain-type-
    specific means:
    
    - Rounded Grains (RG): ν = 0.191 ± 0.008 (density range: 200-580 kg/m³)
    - Precipitation Particles and Decomposing/Fragmented (PP, DF): ν = 0.132 ± 0.053
    - Faceted Crystals and Depth Hoar (FC, DH): ν = 0.17 ± 0.02
    
    The values were computed over subvolumes of size 150³ voxels and were
    consistent with those obtained over entire image volumes for density > 200 kg/m³.
    
    Limitations
    -----------
    - The method is based on numerical simulations of snow microstructure, not
      direct mechanical measurements.
    - The largest scatter was found for PP and DF particles, indicating high
      variability within these grain types.
    - Values are lower than dynamic measurements of Poisson's ratio for
      density > 400 kg/m³ (Smith, 1969), but comparable to Köchle and
      Schneebeli (2014) values.
    - Although density is not used in the calculation (no clear density dependence
      was found), the method is only valid for densities > 200 kg/m³.
    - The RG parameterization was validated over the density range 200-580 kg/m³.
    
    References
    ----------
    Srivastava, P. K., Mahajan, P., Satyawali, P. K., & Kumar, V. (2016).
    Observation of temperature gradient metamorphism in snow by X-ray computed
    microtomography: measurement of microstructure parameters and simulation of
    linear elastic properties. Annals of Glaciology, 57(71), 73-84.
    doi:10.3189/2016AoG71A562
    """
    
    # Extract nominal density value for validation
    density_nominal = density.nominal_value
    
    # Check if density is within valid range (> 200 kg/m³)
    if density_nominal <= 200.0:
        logger.debug("srivastava: density %.1f kg/m³ outside valid range (must be > 200 kg/m³)", density_nominal)
        return ufloat(np.nan, np.nan)
    
    main_grain_shape = grain_form[:2]
    
    # Check if grain form is valid
    if main_grain_shape not in ['RG', 'PP', 'DF', 'FC', 'DH']:
        logger.debug("srivastava: unsupported grain_form=%r (main_grain_shape=%r)", grain_form, main_grain_shape)
        return ufloat(np.nan, np.nan)
    
    # Assign Poisson's ratio based on grain form
    # Note: density value is not used in the calculation as the study found 
    # no clear density dependence, but density must be within valid ranges
    _u = lambda val, std: ufloat(val, std if include_method_uncertainty else 0.0)
    if main_grain_shape == 'RG':
        # Rounded grains: constant value over density range 200-580 kg/m³
        # Check upper limit for RG
        if density_nominal > 580.0:
            logger.debug("srivastava: density %.1f kg/m³ outside valid range for RG (must be <= 580 kg/m³)", density_nominal)
            return ufloat(np.nan, np.nan)
        nu_snow = _u(0.191, 0.008)
    elif main_grain_shape in ['PP', 'DF']:
        # Precipitation particles and decomposing/fragmented: largest scatter
        nu_snow = _u(0.132, 0.053)
    elif main_grain_shape in ['FC', 'DH']:
        # Faceted crystals and depth hoar: intermediate scatter
        nu_snow = _u(0.17, 0.02)

    return nu_snow