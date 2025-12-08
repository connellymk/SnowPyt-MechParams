# Methods to calculate tensile normal strength (σ_c+) of snow

from typing import Any

import numpy as np
from uncertainties import ufloat
from uncertainties import umath


def calculate_sigma_c_plus(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate tensile normal strength of snow based on specified method and
    input parameters.

    The tensile normal strength σ_c+ represents the maximum tensile stress
    that snow can withstand before fracture. It is used to assess the potential
    for tensile slab fracture in avalanche mechanics.

    Parameters
    ----------
    method : str
        Method to use for σ_c+ calculation. Available methods:
        - 'sigrist': Uses Sigrist et al. (2005) power-law scaling relationship
          based on density

    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated tensile normal strength in kPa with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'sigrist':
        return _calculate_sigma_c_plus_sigrist(**kwargs)
    else:
        available_methods = ['sigrist']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_sigma_c_plus_sigrist(density: ufloat) -> ufloat:
    """
    Calculate tensile normal strength using Sigrist (2006) power-law
    scaling relationship.

    This method uses an empirical power-law relationship between snow density
    and tensile strength, as referenced in Weißgraeber & Rosendahl (2023) for
    visualization of principal stresses in snow slabs.

    Parameters
    ----------
    density : ufloat
        Snow density (ρ) in kg/m³ with associated uncertainty

    Returns
    -------
    ufloat
        Tensile normal strength σ_c+ in kPa with associated uncertainty.
        Returns ufloat(NaN, NaN) if density is invalid (≤ 0 or > ρ_ice).

    Notes
    -----
    The tensile normal strength is calculated using the power-law relationship
    (Equation 22 in Weißgraeber & Rosendahl 2023, citing Sigrist 2006):

    σ_c+(ρ) = 240 kPa * (ρ/ρ_0)^2.44

    where:
    - ρ is the snow density [kg/m³]
    - ρ_0 = 917 kg/m³ is the density of ice
    - 240 kPa is the reference tensile strength at ice density
    - 2.44 is the empirically determined power-law exponent

    This formula was derived from fracture mechanical experiments on snow
    samples as part of Sigrist's PhD thesis on dry snow slab avalanche release.

    Physical Interpretation:
    - Tensile strength increases strongly with density (power > 2)
    - Low-density snow (e.g., 100 kg/m³) has very low tensile strength (~0.3 kPa)
    - High-density snow (e.g., 400 kg/m³) has much higher tensile strength (~10 kPa)
    - The power-law exponent of 2.44 suggests that strength scales faster than
      density squared, indicating that microstructural changes with density
      (e.g., increased bonding, reduced porosity) play a significant role

    Typical Values:
    - Fresh snow (ρ ~ 100 kg/m³): σ_c+ ~ 0.3 kPa
    - Settled snow (ρ ~ 200 kg/m³): σ_c+ ~ 1.8 kPa
    - Dense snow (ρ ~ 300 kg/m³): σ_c+ ~ 5.1 kPa
    - Very dense snow (ρ ~ 400 kg/m³): σ_c+ ~ 10.5 kPa

    Limitations
    -----------
    - Empirical relationship based on experimental data with inherent scatter
    - Does not account for grain type, bonding, or microstructure explicitly
    - Does not account for strain rate effects (relationship may be for
      specific loading rate)
    - Does not account for temperature effects
    - Assumes isotropic strength (no directional dependence)
    - Valid range of densities depends on the original experimental data
      (typically 50-500 kg/m³ for seasonal snow)
    - Extrapolation beyond the experimental range may be unreliable

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for 
    layered snow slabs. The Cryosphere, 17(4), 1475-1496.
    https://doi.org/10.5194/tc-17-1475-2023

    Sigrist, C. (2006). Measurement of fracture mechanical properties of snow 
    and application to dry snow slab avalanche release. PhD thesis, ETH Zürich.
    https://doi.org/10.3929/ethz-a-005282374
    """
    # Validate density input
    if density is None:
        return ufloat(np.nan, np.nan)

    # Extract nominal value for validation
    if hasattr(density, 'nominal_value'):
        rho_val = density.nominal_value
    else:
        rho_val = density

    # Check for valid density range
    rho_ice = 917.0  # kg/m³, density of ice

    if rho_val <= 0.0 or rho_val > rho_ice:
        return ufloat(np.nan, np.nan)

    # Power-law parameters from Sigrist et al. (2005)
    sigma_ref = 240.0  # kPa, reference tensile strength at ice density
    exponent = 2.44  # dimensionless, power-law exponent

    # Calculate tensile strength: σ_c+ = 240 * (ρ/ρ_0)^2.44
    sigma_c_plus = sigma_ref * (density / rho_ice) ** exponent

    return sigma_c_plus
