"""Methods to calculate the mode-II fracture toughness (G_IIc) of a weak layer.

G_IIc is the mode-II (in-plane shear) component of the weak-layer fracture
toughness — the energy per unit area associated with shear crack sliding.
"""

from typing import Any

from uncertainties import ufloat


def calculate_G_IIc(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate the mode-II fracture toughness of a weak layer.

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
        Mode-II fracture toughness in J/m² with associated uncertainty.

    Raises
    ------
    ValueError
        If *method* is not recognised.
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_G_IIc_weissgraeber_rosendahl()
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_G_IIc_weissgraeber_rosendahl() -> ufloat:
    """
    Return the mode-II fracture toughness reference value from
    Weißgraeber & Rosendahl (2023).

    This is also the built-in default used by WEAC (``WeakLayer.G_IIc = 0.79``).

    Returns
    -------
    ufloat
        ``ufloat(0.79, 0.0)`` J/m²  (no uncertainty — constant reference value).

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for
    layered snow slabs. *The Cryosphere*, 17(4), 1475–1496.
    https://doi.org/10.5194/tc-17-1475-2023
    """
    return ufloat(0.79, 0.0)
