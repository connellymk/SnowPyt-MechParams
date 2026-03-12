"""Methods to calculate the mode-I fracture toughness (G_Ic) of a weak layer.

G_Ic is the mode-I (opening / tensile) component of the weak-layer fracture
toughness — the energy per unit area associated with normal (tensile) crack
opening.
"""

from typing import Any

from uncertainties import ufloat


def calculate_G_Ic(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate the mode-I fracture toughness of a weak layer.

    Parameters
    ----------
    method : str
        Calculation method. Available methods:
        - ``'weissgraeber_rosendahl'``: Reference value from
          Weißgraeber & Rosendahl (2023).

    **kwargs
        Method-specific parameters (unused for current methods).

    Returns
    -------
    ufloat
        Mode-I fracture toughness in J/m² with associated uncertainty.

    Raises
    ------
    ValueError
        If *method* is not recognised.
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_G_Ic_weissgraeber_rosendahl()
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_G_Ic_weissgraeber_rosendahl() -> ufloat:
    """
    Return the mode-I fracture toughness reference value from
    Weißgraeber & Rosendahl (2023).

    This is also the built-in default used by WEAC (``WeakLayer.G_Ic = 0.56``).

    Returns
    -------
    ufloat
        ``ufloat(0.56, 0.0)`` J/m²  (no uncertainty — constant reference value).

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for
    layered snow slabs. *The Cryosphere*, 17(4), 1475–1496.
    https://doi.org/10.5194/tc-17-1475-2023
    """
    return ufloat(0.56, 0.0)
