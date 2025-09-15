# Methods to calculate density of a layered slab if not known

import math
from typing import Any, Dict, Optional, cast
from uncertainties import ufloat


def calculate_density(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate density of a snow layer based on specified method and input parameters.

    Parameters
    ----------
    method : str
        Method to use for density calculation. Available methods:
        - 'geldsetzer': Uses Geldsetzer et al. formulas based on hand hardness
          and grain form
        - 'kim_hhi_gt': Uses Kim & Jamieson (2014) formulas based on hand hardness
          index and grain type
        - 'kim_hhi_gt_gs': Uses Kim & Jamieson (2014) Equation (5) formulas based 
          on hand hardness index, grain type, and grain size
    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated density in kg/m³ with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'geldsetzer':
        return _calculate_density_geldsetzer(**kwargs)
    elif method.lower() == 'kim_hhi_gt':
        return _calculate_density_kim_hhi_gt(**kwargs)
    elif method.lower() == 'kim_hhi_gt_gs':
        return _calculate_density_kim_hhi_gt_gs(**kwargs)
    else:
        available_methods = ['geldsetzer', 'kim_hhi_gt', 'kim_hhi_gt_gs']
        raise ValueError(f"Unknown method: {method}. Available methods: {available_methods}")


def _calculate_density_geldsetzer(hand_hardness: str, grain_form: str) -> ufloat:
    """
    Calculate density using Geldsetzer et al. empirical formulas.

    This method uses empirical relationships between hand hardness and grain form
    to estimate snow density based on the Geldsetzer et al. dataset.

    Parameters
    ----------
    hand_hardness : str
        Hand hardness measurement in string notation
        (e.g., 'F', '4F', '1F', 'P', 'K', with optional '+' or '-')
    grain_form : str
        Grain form classification. Supported values:
        - 'PP', 'PPgp', 'DF', 'RG', 'RGmx', 'FC', 'FCmx', 'DH'

    Returns
    -------
    ufloat
        Estimated density in kg/m³ with associated uncertainty

    Raises
    ------
    ValueError
        If hand_hardness or grain_form values are not supported

    Notes
    -----
    The Geldsetzer formulas apply different regression models based on grain type:
    - Linear regression (ρ = A + B*h): Used for most grain types including PP, PPgp, 
      DF, RGmx, FC, FCmx, and DH
    - Non-linear regression (ρ = A + B*h^x): Applied specifically to rounded grain 
      types (RG) which do not conform well to linear relationships

    Standard errors from Table 3 are used as uncertainties for density estimates.

    References
    ----------
    Geldsetzer, T., & Jamieson, J. B. (2000). Estimating dry snow density from
    grain form and hand hardness. Proceedings of the International Snow Science
    Workshop, Big Sky, Montana, USA, 1-6 October 2000, 121-127.
    """
    # Validate that hand_hardness is a string
    if not isinstance(hand_hardness, str):
        raise ValueError(f"Hand hardness must be a string, got {type(hand_hardness)}")

    # Validate grain form
    valid_grain_forms = ['PP', 'PPgp', 'DF', 'RG', 'RGmx', 'FC', 'FCmx', 'DH']
    if grain_form not in valid_grain_forms:
        raise ValueError(
            f"Invalid grain form '{grain_form}'. Valid options: {valid_grain_forms}"
        )

    # Map hand hardness string to numeric hand hardness index (hhi)
    hardness_mapping = {
        'F-': 0.67, 'F': 1.0, 'F+': 1.33,
        '4F-': 1.67, '4F': 2.0, '4F+': 2.33,
        '1F-': 2.67, '1F': 3.0, '1F+': 3.33,
        'P-': 3.67, 'P': 4.0, 'P+': 4.33,
        'K-': 4.67, 'K': 5.0, 'K+': 5.33
    }

    if hand_hardness not in hardness_mapping:
        raise ValueError(f"Hand hardness '{hand_hardness}' not supported. "
                        f"Valid options: {list(hardness_mapping.keys())}")

    hhi = hardness_mapping[hand_hardness]

    # Table 3: Linear regressions of density on hardness index h by groups of grain types
    # From Geldsetzer and Jamieson (2000)
    # Parameters for rho = A + B*h (linear) or rho = A + B*h^x (non-linear for RG types)
    # NOTE: Parameters for RG types are from discussion of equation 5
    regression_parameters = {
        'PP': {'A': 45.0, 'B': 36.0, 'SE': 27.0, 'formula': 'linear'},
        'PPgp': {'A': 83.0, 'B': 37.0, 'SE': 42.0, 'formula': 'linear'},
        'DF': {'A': 65.0, 'B': 36.0, 'SE': 30.0, 'formula': 'linear'},
        'RG': {'A': 154.0, 'B': 1.51, 'SE': 46.0, 'formula': 'nonlinear'},
        #NOTE: SE for nonlinear regression is not provided, SE above is from linear regression
        'RGmx': {'A': 91.0, 'B': 42.0, 'SE': 32.0, 'formula': 'linear'},
        'FC': {'A': 112.0, 'B': 46.0, 'SE': 43.0, 'formula': 'linear'},
        'FCmx': {'A': 56.0, 'B': 64.0, 'SE': 43.0, 'formula': 'linear'},
        'DH': {'A': 185.0, 'B': 25.0, 'SE': 41.0, 'formula': 'linear'}
    }

    # Get regression parameters for the grain form
    params = regression_parameters[grain_form]
    a = cast(float, params['A'])
    b = cast(float, params['B'])
    se = cast(float, params['SE'])

    # Calculate density using appropriate formula
    if params['formula'] == 'linear':
        # Linear regression: rho = A + B*h (Equation 4)
        rho = a + b * hhi
    elif params['formula'] == 'nonlinear':
        # Non-linear regression for rounded grains: rho = A + B*h^3.15 (Equation 5)
        x = 3.15
        rho = a + b * (hhi ** x)
    else:
        raise ValueError(f"Unknown formula type for grain form '{grain_form}'")

    return ufloat(rho, se)


def _calculate_density_kim_hhi_gt(hand_hardness: float, grain_form: str) -> ufloat:
    """
    Calculate density using Kim & Jamieson (2014) empirical formulas based on 
    hand hardness index and grain type.

    This method uses empirical relationships from Kim & Jamieson (2014) to estimate
    snow density based on hand hardness index (numeric) and grain form.

    Parameters
    ----------
    hand_hardness : float
        Hand hardness index (e.g., F=1.0, 4F=2.0, 1F=3.0, P=4.0, K=5.0)
    grain_form : str
        Grain form classification. Supported values:
        - 'PP': Precipitation particles
        - 'PPgp': Precipitation particles, graupel
        - 'DF': Decomposing and fragmented particles
        - 'RGxf': Rounded grains, mixed forms (fine)
        - 'RG': Rounded grains
        - 'FC': Faceted crystals
        - 'FCxr': Faceted crystals, mixed forms (coarse)
        - 'DH': Depth hoar
        - 'MFcr': Melt forms, crusts

    Returns
    -------
    ufloat
        Estimated density in kg/m³ with associated uncertainty

    Raises
    ------
    ValueError
        If hand_hardness is not numeric or grain_form is not supported

    Notes
    -----
    The Kim & Jamieson (2014) formulas provide density estimates with associated 
    uncertainties and R² values indicating model fit quality.

    References
    ----------
    Kim, D. and Jamieson, J.B., 2014. Estimating the Density of Dry Snow Layers 
    From Hardness, and Hardness From Density, International Snow Science Workshop 
    2014 Proceedings, Banff, Canada, 2014 pp.540-547.
    """
    # Validate that hand_hardness is numeric
    if not isinstance(hand_hardness, (int, float)):
        raise ValueError(f"Hand hardness must be numeric, got {type(hand_hardness)}")

    # Validate grain form
    valid_grain_forms = ['PP', 'PPgp', 'DF', 'RGxf', 'RG', 'FC', 'FCxr', 'DH', 'MFcr']
    if grain_form not in valid_grain_forms:
        raise ValueError(
            f"Invalid grain form '{grain_form}'. Valid options: {valid_grain_forms}"
        )

    # Calculate density using Kim & Jamieson (2014) formulas
    if grain_form == 'PP':
        rho, unc_rho = 41.3 + 40.3 * hand_hardness, 27.0
    elif grain_form == 'PPgp':
        rho, unc_rho = 61.8 + 46.4 * hand_hardness, 43.0
    elif grain_form == 'DF':
        rho, unc_rho = 62.5 + 37.4 * hand_hardness, 31.0
    elif grain_form == 'RGxf':
        rho, unc_rho = 85.0 + 46.3 * hand_hardness, 40.0
    elif grain_form == 'FC':
        rho, unc_rho = 103.0 + 50.6 * hand_hardness, 47.0
    elif grain_form == 'FCxr':
        rho, unc_rho = 68.8 + 58.6 * hand_hardness, 46.0
    elif grain_form == 'DH':
        rho, unc_rho = 214.0 + 19.0 * hand_hardness, 48.0
    elif grain_form == 'MFcr':
        rho, unc_rho = 235.0 + 15.1 * hand_hardness, 58.0
    elif grain_form == 'RG':
        # Using exponential formula: rho = 91.8 * exp(0.270 * hhi)
        rho, unc_rho = 91.8 * math.exp(0.270 * hand_hardness), 0.2
    else:
        raise ValueError(f"Grain form '{grain_form}' not supported")

    return ufloat(rho, unc_rho)


def _calculate_density_kim_hhi_gt_gs(hand_hardness: float, grain_form: str, grain_size: float) -> ufloat:
    """
    Calculate density using Kim & Jamieson (2014) empirical formulas based on 
    hand hardness index, grain type, and grain size.

    This method uses empirical relationships from Kim & Jamieson (2014) Equation (5)
    to estimate snow density: ρ = A*h + B*gs + C

    Parameters
    ----------
    hand_hardness : float
        Hand hardness index (e.g., F=1.0, 4F=2.0, 1F=3.0, P=4.0, K=5.0)
    grain_form : str
        Grain form classification. Supported values:
        - 'Facet': Faceted crystals
        - 'FCxr': Faceted crystals, mixed forms (coarse)
        - 'PP': Precipitation particles
        - 'PPgp': Precipitation particles, graupel
        - 'DF': Decomposing and fragmented particles
        - 'MF': Melt forms
    grain_size : float
        Grain size in mm

    Returns
    -------
    ufloat
        Estimated density in kg/m³ with associated uncertainty

    Raises
    ------
    ValueError
        If hand_hardness or grain_size are not numeric or grain_form is not supported

    Notes
    -----
    The Kim & Jamieson (2014) Equation (5) formulas provide density estimates 
    with associated uncertainties and R² values indicating model fit quality.

    References
    ----------
    Kim, D. and Jamieson, J.B., 2014. Estimating the Density of Dry Snow Layers 
    From Hardness, and Hardness From Density, International Snow Science Workshop 
    2014 Proceedings, Banff, Canada, 2014 pp.540-547.
    """
    # Validate that hand_hardness is numeric
    if not isinstance(hand_hardness, (int, float)):
        raise ValueError(f"Hand hardness must be numeric, got {type(hand_hardness)}")

    # Validate that grain_size is numeric
    if not isinstance(grain_size, (int, float)):
        raise ValueError(f"Grain size must be numeric, got {type(grain_size)}")

    # Validate grain form
    valid_grain_forms = ['Facet', 'FCxr', 'PP', 'PPgp', 'DF', 'MF']
    if grain_form not in valid_grain_forms:
        raise ValueError(
            f"Invalid grain form '{grain_form}'. Valid options: {valid_grain_forms}"
        )

    # Calculate density using Kim & Jamieson (2014) Equation (5) formulas
    if grain_form == 'Facet':
        rho, unc_rho = 51.9 * hand_hardness + 19.7 * grain_size + 82.8, 46
    elif grain_form == 'FCxr':
        rho, unc_rho = 60.4 * hand_hardness + 27.7 * grain_size + 36.7, 45
    elif grain_form == 'PP':
        rho, unc_rho = 40.0 * hand_hardness - 7.33 * grain_size + 52.8, 25
    elif grain_form == 'PPgp':
        rho, unc_rho = 38.8 * hand_hardness + 18.8 * grain_size + 35.7, 33
    elif grain_form == 'DF':
        rho, unc_rho = 37.9 * hand_hardness - 8.87 * grain_size + 71.4, 31
    elif grain_form == 'MF':
        rho, unc_rho = 34.9 * hand_hardness + 11.2 * grain_size + 124.5, 63
    else:
        raise ValueError(f"Grain form '{grain_form}' not supported")

    return ufloat(rho, unc_rho)
