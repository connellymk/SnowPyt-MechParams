# Methods to calculate density of a layered slab if not known

from typing import Any, Dict, Optional


def calculate_density(method: str, **kwargs: Any) -> float:
    """
    Calculate density of a snow layer based on specified method and input parameters.

    Parameters
    ----------
    method : str
        Method to use for density calculation. Available methods:
        - 'geldsetzer': Uses Geldsetzer et al. lookup table based on hand hardness
          and grain form
    **kwargs
        Method-specific parameters

    Returns
    -------
    float
        Calculated density in kg/m³

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'geldsetzer':
        return _calculate_density_geldsetzer(**kwargs)
    else:
        raise ValueError(f"Unknown method: {method}. Available methods: 'geldsetzer'")


def _calculate_density_geldsetzer(hand_hardness: str, grain_form: str) -> float:
    """
    Calculate density using Geldsetzer et al. lookup table.

    This method uses empirical relationships between hand hardness and grain form
    to estimate snow density based on the Geldsetzer et al. dataset.

    Parameters
    ----------
    hand_hardness : str
        Hand hardness measurement in string notation
        (e.g., 'F', '4F', '1F', 'P', 'K', with optional '+' or '-')
    grain_form : str
        Grain form classification. Supported values:
        - 'PP': Precipitation particles
        - 'PPgp': Precipitation particles, graupel
        - 'DF': Decomposing and fragmented particles
        - 'RG': Rounded grains
        - 'RGmx': Rounded grains, mixed forms
        - 'FC': Faceted crystals
        - 'FCmx': Faceted crystals, mixed forms
        - 'DH': Depth hoar

    Returns
    -------
    float
        Estimated density in kg/m³

    Raises
    ------
    ValueError
        If hand_hardness or grain_form values are not found in lookup table

    Notes
    -----
    The Geldsetzer lookup table provides density estimates based on empirical
    relationships. Some combinations of hand hardness and grain form may not
    have available data, in which case a ValueError will be raised.

    References
    ----------
    Geldsetzer, T., & Jamieson, J. B. (2000). Estimating dry snow density from
    grain form and hand hardness. Proceedings of the International Snow Science
    Workshop, Big Sky, Montana, USA, 1-6 October 2000, 121-127.
    """
    # Geldsetzer et al. lookup table for density estimation
    # Based on empirical relationships between hand hardness and grain form
    geldsetzer_table: Dict[str, Dict[str, Optional[int]]] = {
        'F-': {
            'PP': 69, 'PPgp': 108, 'DF': 89, 'RG': None, 'RGmx': 119,
            'FC': 143, 'FCmx': None, 'DH': None
        },
        'F': {
            'PP': 81, 'PPgp': 120, 'DF': 101, 'RG': 156, 'RGmx': 133,
            'FC': 158, 'FCmx': 120, 'DH': 210
        },
        'F+': {
            'PP': 93, 'PPgp': 132, 'DF': 113, 'RG': 158, 'RGmx': 147,
            'FC': 173, 'FCmx': 141, 'DH': 218
        },
        '4F-': {
            'PP': 105, 'PPgp': 145, 'DF': 125, 'RG': 162, 'RGmx': 161,
            'FC': 189, 'FCmx': 163, 'DH': 227
        },
        '4F': {
            'PP': 117, 'PPgp': 157, 'DF': 137, 'RG': 167, 'RGmx': 175,
            'FC': 204, 'FCmx': 184, 'DH': 235
        },
        '4F+': {
            'PP': 129, 'PPgp': 169, 'DF': 149, 'RG': 176, 'RGmx': 189,
            'FC': 219, 'FCmx': 205, 'DH': 243
        },
        '1F-': {
            'PP': 141, 'PPgp': 182, 'DF': 161, 'RG': 187, 'RGmx': 203,
            'FC': 235, 'FCmx': 227, 'DH': 252
        },
        '1F': {
            'PP': 153, 'PPgp': 194, 'DF': 173, 'RG': 202, 'RGmx': 217,
            'FC': 250, 'FCmx': 248, 'DH': 260
        },
        '1F+': {
            'PP': 165, 'PPgp': 206, 'DF': 185, 'RG': 221, 'RGmx': 231,
            'FC': 265, 'FCmx': 269, 'DH': 268
        },
        'P-': {
            'PP': 177, 'PPgp': 219, 'DF': 197, 'RG': 244, 'RGmx': 245,
            'FC': 281, 'FCmx': 291, 'DH': 277
        },
        'P': {
            'PP': 189, 'PPgp': 231, 'DF': 209, 'RG': 273, 'RGmx': 259,
            'FC': 296, 'FCmx': 312, 'DH': 285
        },
        'P+': {
            'PP': None, 'PPgp': None, 'DF': 221, 'RG': 306, 'RGmx': 273,
            'FC': 311, 'FCmx': 333, 'DH': 293
        },
        'K-': {
            'PP': None, 'PPgp': None, 'DF': None, 'RG': 347, 'RGmx': None,
            'FC': 327, 'FCmx': 355, 'DH': 302
        },
        'K': {
            'PP': None, 'PPgp': None, 'DF': None, 'RG': 393, 'RGmx': None,
            'FC': None, 'FCmx': 376, 'DH': 310
        },
        'K+': {
            'PP': None, 'PPgp': None, 'DF': None, 'RG': 447, 'RGmx': None,
            'FC': None, 'FCmx': 397, 'DH': None
        },
    }

    # Validate that hand_hardness is a string
    if not isinstance(hand_hardness, str):
        raise ValueError(f"Hand hardness must be a string, got {type(hand_hardness)}")

    # Validate grain form
    valid_grain_forms = ['PP', 'PPgp', 'DF', 'RG', 'RGmx', 'FC', 'FCmx', 'DH']
    if grain_form not in valid_grain_forms:
        raise ValueError(
            f"Invalid grain form '{grain_form}'. Valid options: {valid_grain_forms}"
        )

    # Look up the density value in the table
    if hand_hardness not in geldsetzer_table:
        raise ValueError(f"Hand hardness '{hand_hardness}' not found in lookup table")

    hardness_data = geldsetzer_table[hand_hardness]

    if grain_form not in hardness_data:
        raise ValueError(f"Grain form '{grain_form}' not found in lookup table")

    density_value = hardness_data[grain_form]

    # Check if the value is None (missing data in the table)
    if density_value is None:
        raise ValueError(
            f"No density data available for hand hardness '{hand_hardness}' "
            f"and grain form '{grain_form}' combination"
        )

    return float(density_value)
