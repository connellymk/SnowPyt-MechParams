"""Methods to calculate the compressive strength (σ_comp) of snow.

σ_comp is the maximum compressive stress that snow can withstand before collapse.
It is particularly important for weak layers in avalanche mechanics.
"""

from typing import Any

import numpy as np
from uncertainties import ufloat

from snowpyt_mechparams.constants import RHO_ICE


def calculate_sigma_comp(method: str, include_method_uncertainty: bool = True, **kwargs: Any) -> ufloat:
    """
    Calculate compressive strength of snow based on specified method and
    input parameters.

    The compressive strength σ_comp represents the maximum compressive stress
    that snow can withstand before collapse. It is particularly important for
    weak layers in avalanche mechanics.

    Parameters
    ----------
    method : str
        Method to use for σ_comp calculation. Available methods:
        - 'reiweger': Uses Reiweger et al. (2015) reference value for weak
          layers under rapid loading
        - 'mellor': Uses Mellor (1975) power-law scaling relationship based
          on density (for general snow)
    include_method_uncertainty : bool, optional
        Whether to include the uncertainty inherent to the empirical method.
        Default is True. Accepted for API consistency; has no effect for
        current methods, as none report standard errors for their parameters.

    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated compressive strength in kPa with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'reiweger':
        return _calculate_sigma_comp_reiweger(**kwargs)
    elif method.lower() == 'mellor':
        return _calculate_sigma_comp_mellor(**kwargs)
    else:
        available_methods = ['reiweger', 'mellor']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_sigma_comp_reiweger(density: ufloat = None) -> ufloat:
    """
    Calculate compressive strength using Reiweger et al. (2015) reference value
    for weak layers.

    This method provides a reference compressive strength value for weak snow
    layers under rapid loading conditions, as cited in Weißgraeber & Rosendahl
    (2023) for visualization of principal stresses in weak layers.

    Parameters
    ----------
    density : ufloat, optional
        Snow density (ρ) in kg/m³ with associated uncertainty. Accepted for
        API consistency but not used in the calculation, as the Reiweger et al.
        (2015) reference provides a single constant value.

    Returns
    -------
    ufloat
        Compressive strength σ_comp in kPa with associated uncertainty.

    Notes
    -----
    The compressive strength is given as a reference value from Reiweger et al.
    (2015), as cited in Weißgraeber & Rosendahl (2023):

    σ_comp = 2.6 kPa

    This value represents the rapid-loading compressive strength of a weak
    layer and is used for assessing the potential for weak-layer collapse
    under compressive loading. The value comes from a study on mixed-mode
    failure criteria for weak snowpack layers.

    Physical Interpretation:
    - This is a characteristic value for weak layers, not general snow
    - Represents rapid loading conditions (relevant for avalanche triggering)
    - Much lower than typical slab compressive strengths
    - Weak layers fail in compression more easily than in tension

    Limitations
    -----------
    - Single reference value, not density-dependent
    - Specific to weak layers (may not be appropriate for slab layers)
    - Represents rapid loading conditions (strain rate dependent)
    - Does not account for grain type, bonding, or microstructure explicitly
    - Does not account for temperature effects
    - Uncertainty in the value is not specified in the reference

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for
    layered snow slabs. The Cryosphere, 17(4), 1475-1496.
    https://doi.org/10.5194/tc-17-1475-2023

    Reiweger, I., Gaume, J., & Schweizer, J. (2015). A new mixed-mode failure
    criterion for weak snowpack layers. Geophysical Research Letters, 42,
    1427-1432.
    https://doi.org/10.1002/2014GL062780
    """
    # Reference compressive strength for weak layers (Reiweger et al. 2015)
    sigma_comp = 2.6  # kPa

    # Return as ufloat with no uncertainty specified (could be added if known)
    return ufloat(sigma_comp, 0.0)


def _calculate_sigma_comp_mellor(density: ufloat) -> ufloat:
    """
    Calculate compressive strength using Mellor (1975) power-law scaling
    relationship.

    This method uses an empirical power-law relationship between snow density
    and compressive strength, based on experimental data compiled by Mellor
    (1975). This relationship is more general than the Reiweger et al. (2015)
    weak-layer value and can be applied to a range of snow types.

    Parameters
    ----------
    density : ufloat
        Snow density (ρ) in kg/m³ with associated uncertainty

    Returns
    -------
    ufloat
        Compressive strength σ_comp in kPa with associated uncertainty.
        Returns ufloat(NaN, NaN) if density is invalid (≤ 0 or > ρ_ice).

    Notes
    -----
    The compressive strength is calculated using a power-law relationship
    based on Mellor (1975):

    σ_comp(ρ) = C * (ρ/ρ_0)^n

    where:
    - ρ is the snow density [kg/m³]
    - ρ_0 = 917 kg/m³ is the density of ice
    - C is a reference strength coefficient [kPa]
    - n is the power-law exponent [dimensionless]

    This implementation uses representative values for rapid loading:
    - C = 5000 kPa
    - n = 2.5

    These values are approximate and broadly consistent with the range
    reported by Mellor (1975) (C ≈ 3000–10000 kPa, n ≈ 2.0–3.0 depending
    on loading rate and snow type). They are not tabulated directly in
    Mellor (1975); users requiring a more precise source should refer to
    the compilation in Shapiro et al. (1997).

    Physical Interpretation:
    - Compressive strength increases strongly with density
    - Generally much higher than tensile strength for the same density
    - Loading rate significantly affects the measured strength
    - Microstructural factors (grain bonding, type) influence the relationship

    Typical Values (using this formula):
    - Fresh snow (ρ ~ 100 kg/m³): σ_comp ~ 7 kPa
    - Settled snow (ρ ~ 200 kg/m³): σ_comp ~ 40 kPa
    - Dense snow (ρ ~ 300 kg/m³): σ_comp ~ 110 kPa
    - Very dense snow (ρ ~ 400 kg/m³): σ_comp ~ 230 kPa

    Limitations
    -----------
    - Empirical relationship with significant scatter in experimental data
    - Highly dependent on loading rate (this uses rapid loading assumption)
    - Does not account for grain type, bonding, or microstructure explicitly
    - Does not account for temperature effects
    - Assumes isotropic strength (no directional dependence)
    - Parameters (C, n) are representative approximations; actual values vary
      with loading conditions and snow type
    - Valid range depends on original experimental data (typically 50-500 kg/m³)

    References
    ----------
    Mellor, M. (1975). A review of basic snow mechanics. In Snow Mechanics
    (pp. 251-291). International Association of Hydrological Sciences
    Publication No. 114.

    Shapiro, L. H., Johnson, J. B., Sturm, M., & Blaisdell, G. L. (1997).
    Snow mechanics: Review of the state of knowledge and applications.
    CRREL Report 97-3, US Army Cold Regions Research and Engineering Laboratory.
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
    if rho_val <= 0.0 or rho_val > RHO_ICE:
        return ufloat(np.nan, np.nan)

    # Representative power-law parameters for rapid loading (see Notes)
    C = 5000.0  # kPa, reference compressive strength coefficient
    n = 2.5  # dimensionless, power-law exponent

    # Calculate compressive strength: σ_comp = C * (ρ/ρ_0)^n
    sigma_comp = C * (density / RHO_ICE) ** n

    return sigma_comp

