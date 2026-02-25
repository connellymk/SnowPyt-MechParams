# Methods to calculate density of a layered slab if not known

import logging
import math
from math import sqrt
from typing import Any

import numpy as np
from uncertainties import ufloat

from snowpyt_mechparams.data_structures import UncertainValue

logger = logging.getLogger(__name__)


def calculate_density(method: str, include_method_uncertainty: bool = True, **kwargs: Any) -> ufloat:
    """
    Calculate density of a snow layer based on specified method and input parameters.

    Parameters
    ----------
    method : str
        Method to use for density calculation. Available methods:
        - 'geldsetzer': Uses Geldsetzer et al. formulas based on hand hardness
          and grain form
        - 'kim_jamieson_table2': Uses Kim & Jamieson (2014) Table 2 formulas based
          on hand hardness and grain form (extended from Geldsetzer)
        - 'kim_jamieson_table5': Uses Kim & Jamieson (2014) Table 5 formulas based
          on hand hardness, grain type, and grain size
    include_method_uncertainty : bool, optional
        Whether to include the uncertainty inherent to the empirical method
        (e.g. regression standard error). Default is True. If False, the
        nominal value is unchanged but no method uncertainty is added;
        input uncertainties still propagate normally.
    **kwargs
        Method-specific parameters. All methods accept:
        - ``hand_hardness_index`` : UncertainValue
            Hand hardness index as a ufloat (HHI with measurement uncertainty
            already applied). Obtain via ``Layer.hand_hardness_index``.
        'kim_jamieson_table5' additionally requires:
        - ``grain_size`` : UncertainValue
            Grain size in mm as a ufloat with measurement uncertainty already
            applied. Obtain via ``Layer.grain_size_avg``.

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
        return _calculate_density_geldsetzer(include_method_uncertainty=include_method_uncertainty, **kwargs)
    elif method.lower() == 'kim_jamieson_table2':
        return _calculate_density_kim_jamieson_table2(include_method_uncertainty=include_method_uncertainty, **kwargs)
    elif method.lower() == 'kim_jamieson_table5':
        return _calculate_density_kim_jamieson_table5(include_method_uncertainty=include_method_uncertainty, **kwargs)

    else:
        available_methods = ['geldsetzer', 'kim_jamieson_table2', 'kim_jamieson_table5']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_density_geldsetzer(hand_hardness_index: UncertainValue, grain_form: str, include_method_uncertainty: bool = True) -> ufloat:
    """
    Calculate density using Geldsetzer et al. empirical formulas.

    This method uses empirical relationships between hand hardness and grain form
    to estimate snow density based on the Geldsetzer et al. dataset.

    Parameters
    ----------
    hand_hardness_index : UncertainValue
        Hand hardness index as a ufloat with measurement uncertainty already
        applied. Obtain via ``Layer.hand_hardness_index``.
    grain_form : str
        Grain form classification. Supported values:
        - 'PP', 'PPgp', 'DF', 'RG', 'RGmx', 'FC', 'FCmx', 'DH'

    Returns
    -------
    ufloat
        Estimated density in kg/m³ with associated uncertainty.
        Returns ufloat(NaN, NaN) if hand_hardness or grain_form values are not
        supported.

    Notes
    -----
    The Geldsetzer formulas apply different regression models based on grain type:
    - Linear regression (rho = A + B*h): Used for most grain types including PP,
      PPgp, DF, RGmx, FC, FCmx, and DH
    - Non-linear regression (rho = A + B*h^x): Applied specifically to rounded
      grain types (RG) which do not conform well to linear relationships

    Standard errors from Table 3 in Geldsetzer et al. (2000) are used as
    uncertainties for density estimates.

    References
    ----------
    Geldsetzer, T., & Jamieson, J. B. (2000). Estimating dry snow density from
    grain form and hand hardness. Proceedings of the International Snow Science
    Workshop, Big Sky, Montana, USA, 1-6 October 2000, 121-127.
    """

    # Validate grain form
    valid_grain_forms = ['PP', 'PPgp', 'DF', 'RG', 'RGmx', 'FC', 'FCmx', 'DH']
    if grain_form not in valid_grain_forms:
        logger.debug("_calculate_density_geldsetzer: unsupported grain_form=%r", grain_form)
        return ufloat(np.nan, np.nan)

    if hand_hardness_index is None:
        logger.debug("_calculate_density_geldsetzer: hand_hardness_index is None")
        return ufloat(np.nan, np.nan)
    h = hand_hardness_index  # already a ufloat from data_structures.py

    # Table 3: Linear regressions of density on hardness index h by groups
    # of grain types. From Geldsetzer and Jamieson (2000)
    # Parameters for rho = A + B*h (linear) or rho = A + B*h^x (non-linear for RG)
    # NOTE: Parameters for RG types are from discussion of equation 5
    regression_parameters = {
        'PP': {'A': 45.0, 'B': 36.0, 'SE': 27.0, 'formula': 'linear'},
        'PPgp': {'A': 83.0, 'B': 37.0, 'SE': 42.0, 'formula': 'linear'},
        'DF': {'A': 65.0, 'B': 36.0, 'SE': 30.0, 'formula': 'linear'},
        'RG': {'A': 154.0, 'B': 1.51, 'SE': 46.0, 'formula': 'nonlinear'},
        # NOTE: SE for nonlinear regression is not provided, SE above is from
        # linear regression
        'RGmx': {'A': 91.0, 'B': 42.0, 'SE': 32.0, 'formula': 'linear'},
        'FC': {'A': 112.0, 'B': 46.0, 'SE': 43.0, 'formula': 'linear'},
        'FCmx': {'A': 56.0, 'B': 64.0, 'SE': 43.0, 'formula': 'linear'},
        'DH': {'A': 185.0, 'B': 25.0, 'SE': 41.0, 'formula': 'linear'}
    }

    # Get regression parameters for the grain form
    params = regression_parameters[grain_form]
    a = params['A']
    b = params['B']
    se = params['SE']

    # Calculate density using appropriate formula
    if params['formula'] == 'linear':
        # Linear regression: rho = A + B*h (Equation 4)
        rho = a + b * h
    elif params['formula'] == 'nonlinear':
        # Non-linear regression for rounded grains: rho = A + B*h^3.15 (Equation 5)
        x = 3.15
        rho = a + b * (h ** x)
    else:
        raise ValueError(f"Unknown formula type for grain form '{grain_form}'")

    # Combine propagated input uncertainty with method SE in quadrature
    if include_method_uncertainty:
        total_std = sqrt(rho.std_dev ** 2 + se ** 2)
    else:
        total_std = rho.std_dev
    return ufloat(rho.nominal_value, total_std)

def _calculate_density_kim_jamieson_table2(
    hand_hardness_index: UncertainValue, grain_form: str, include_method_uncertainty: bool = True
) -> ufloat:
    """
    Calculate density using Kim & Jamieson (2014) empirical formulas based
    on hand hardness and grain form, updated from Geldsetzer et al. (2000)

    Parameters
    ----------
    hand_hardness_index : UncertainValue
        Hand hardness index as a ufloat with measurement uncertainty already
        applied. Obtain via ``Layer.hand_hardness_index``.
    grain_form : str
        Grain form classification. Supported values:
        - 'PP', 'PPgp', 'DF', 'RGxf', 'FC', 'FCxr', 'DH', 'MFcr', 'RG'

    Returns
    -------
    ufloat
        Estimated density in kg/m³ with associated uncertainty.
        Returns ufloat(NaN, NaN) if hand_hardness or grain_form values are not
        supported.

    Notes
    -----
    The Kim & Jamieson (2014) formulas, adapted from Geldsetzer et al. (2000), apply
    different regression models based on grain type:
    - Linear regression (rho = A + B*h): Used for all supported grain types except RG.
      The SE column is a residual standard error of the regression in kg/m³, added in
      quadrature with propagated input measurement uncertainty.
    - Non-linear regression (rho = A*e^(B*h)): Applied specifically to rounded
      grain types (RG) which do not conform well to linear relationships. For this
      model, the SE value (0.2) is the standard error of the fitted exponent
      coefficient B=0.270, not a residual density SE. It is propagated through the
      exponential model automatically via the uncertainties library, producing
      density-dependent method uncertainty (larger at higher densities).

    References
    ----------
    Kim, D. and Jamieson, J.B., 2014. Estimating the Density of Dry Snow Layers
    From Hardness, and Hardness From Density, International Snow Science Workshop
    2014 Proceedings, Banff, Canada, 2014 pp.540-547.
    """

    # Validate grain form
    valid_grain_forms = ['PP', 'PPgp', 'DF', 'RGxf', 'FC', 'FCxr', 'DH', 'MFcr', 'RG']
    if grain_form not in valid_grain_forms:
        logger.debug("_calculate_density_kim_jamieson_table2: unsupported grain_form=%r", grain_form)
        return ufloat(np.nan, np.nan)

    if hand_hardness_index is None:
        logger.debug("_calculate_density_kim_jamieson_table2: hand_hardness_index is None")
        return ufloat(np.nan, np.nan)
    h = hand_hardness_index  # already a ufloat from data_structures.py

    # Table 2: Linear regressions of density on hand hardness index by
    # grain types (Equation 1), except for a non-linear regression for RG (Equation 2)
    # From Kim & Jamieson (2014)
    #
    # For linear grain forms, SE is the residual standard error of the
    # regression in kg/m³ (added in quadrature with propagated input
    # uncertainty).
    #
    # For RG (nonlinear: rho = A * e^(B*h)), the SE value (0.2) is the
    # standard error of coefficient B (0.270 ± 0.2), NOT a residual density
    # SE. It is propagated through the exponential via the uncertainties
    # library by encoding B as a ufloat, rather than being added in
    # quadrature as a density SE. See Kim & Jamieson (2014) Table 2.
    regression_parameters = {
        'PP': {'A': 41.3, 'B': 40.3, 'SE': 27.0, 'formula': 'linear'},
        'PPgp': {'A': 61.8, 'B': 46.4, 'SE': 43.0, 'formula': 'linear'},
        'DF': {'A': 62.5, 'B': 37.4, 'SE': 31.0, 'formula': 'linear'},
        'RGxf': {'A': 85.0, 'B': 46.3, 'SE': 40.0, 'formula': 'linear'},
        'FC': {'A': 103, 'B': 50.6, 'SE': 47.0, 'formula': 'linear'},
        'FCxr': {'A': 68.8, 'B': 58.6, 'SE': 46.0, 'formula': 'linear'},
        'DH': {'A': 214.0, 'B': 19.0, 'SE': 48.0, 'formula': 'linear'},
        'MFcr': {'A': 235, 'B': 15.1, 'SE': 58.0, 'formula': 'linear'},
        'RG': {'A': 91.8, 'B': 0.270, 'B_SE': 0.2, 'formula': 'nonlinear'}
    }

    # Get regression parameters for the grain form
    params = regression_parameters[grain_form]
    a = params['A']

    # Calculate density using appropriate formula
    if params['formula'] == 'linear':
        b = params['B']
        se = params['SE']
        # Linear regression: rho = A + B*h (Equation 1)
        rho = a + b * h
        # Combine propagated input uncertainty with residual density SE in quadrature
        if include_method_uncertainty:
            total_std = sqrt(rho.std_dev ** 2 + se ** 2)
        else:
            total_std = rho.std_dev
    elif params['formula'] == 'nonlinear':
        # Non-linear regression for rounded grains: rho = A*e^(B*h) (Equation 2)
        # B_SE is the standard error of coefficient B, propagated through the
        # exponential automatically by encoding B as a ufloat.
        b_se = params['B_SE'] if include_method_uncertainty else 0.0
        b = ufloat(params['B'], b_se)
        rho = a * math.e ** (b * h)
        total_std = rho.std_dev
    else:
        raise ValueError(f"Unknown formula type for grain form '{grain_form}'")

    return ufloat(rho.nominal_value, total_std)

def _calculate_density_kim_jamieson_table5(
    hand_hardness_index: UncertainValue, grain_form: str, grain_size: UncertainValue, include_method_uncertainty: bool = True
) -> ufloat:
    """
    Calculate density using Kim & Jamieson (2014) empirical formulas based
    on hand hardness, grain form, and grain size.

    This method uses empirical relationships from Kim & Jamieson (2014) Equation (5)
    to estimate snow density: rho = A*h + B*gs + C

    Parameters
    ----------
    hand_hardness_index : UncertainValue
        Hand hardness index as a ufloat with measurement uncertainty already
        applied. Obtain via ``Layer.hand_hardness_index``.
    grain_form : str
        Grain form classification. Supported values:
        - 'FC', 'FCxr', 'PP', 'PPgp', 'DF', 'MF'
    grain_size : UncertainValue
        Grain size in mm with measurement uncertainty already applied
        (``ufloat(gs, U_GRAIN_SIZE)``). Obtain via ``Layer.grain_size_avg``.

    Returns
    -------
    ufloat
        Estimated density in kg/m³ with associated uncertainty.
        Returns ufloat(NaN, NaN) if hand_hardness or grain_form values are not
        supported.

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
    # Validate grain form
    valid_grain_forms = ['FC', 'FCxr', 'PP', 'PPgp', 'DF', 'MF']
    if grain_form not in valid_grain_forms:
        logger.debug("_calculate_density_kim_jamieson_table5: unsupported grain_form=%r", grain_form)
        return ufloat(np.nan, np.nan)

    if hand_hardness_index is None:
        logger.debug("_calculate_density_kim_jamieson_table5: hand_hardness_index is None")
        return ufloat(np.nan, np.nan)
    h = hand_hardness_index  # already a ufloat from data_structures.py

    # Table 6: Significant multivariable linear regression of density on hardness index
    # and grain size by different groups of grain types
    # From Kim and Jamieson (2014)
    regression_parameters = {
        'FC': {'A': 51.9, 'B': 19.7, 'C': 82.8, 'SE': 46.0},
        'FCxr': {'A': 60.4, 'B': 27.7, 'C': 36.7, 'SE': 45.0},
        'PP': {'A': 40.0, 'B': -7.33, 'C': 52.8, 'SE': 25.0},
        'PPgp': {'A': 38.8, 'B': 18.8, 'C': 35.7, 'SE': 33.0},
        'DF': {'A': 37.9, 'B': -8.87, 'C': 71.4, 'SE': 31.0},
        'MF': {'A': 34.9, 'B': 11.2, 'C': 124.5, 'SE': 63.0}
    }

    # Get regression parameters for the grain form
    params = regression_parameters[grain_form]
    a = params['A']
    b = params['B']
    c = params['C']
    se = params['SE']

    # Calculate density using equation 5
    rho = a * h + b * grain_size + c

    # Combine propagated input uncertainty with method SE in quadrature
    if include_method_uncertainty:
        total_std = sqrt(rho.std_dev ** 2 + se ** 2)
    else:
        total_std = rho.std_dev
    return ufloat(rho.nominal_value, total_std)


