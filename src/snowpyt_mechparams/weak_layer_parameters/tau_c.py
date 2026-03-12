"""Methods to calculate the shear strength (τ_c) of a weak layer.

τ_c is the maximum shear stress the weak layer can sustain before failure.
It is used alongside σ_c+ in WEAC's coupled tensile–shear failure criterion.
"""

from typing import Any

from uncertainties import ufloat


def calculate_tau_c(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate the shear strength of a weak layer.

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
        Shear strength in kPa with associated uncertainty.

    Raises
    ------
    ValueError
        If *method* is not recognised.
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_tau_c_weissgraeber_rosendahl()
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_tau_c_weissgraeber_rosendahl() -> ufloat:
    """
    Return the shear strength reference value from Weißgraeber & Rosendahl (2023).

    This is also the built-in default used by WEAC (``WeakLayer.tau_c = 5.09``).

    Returns
    -------
    ufloat
        ``ufloat(5.09, 0.0)`` kPa  (no uncertainty — constant reference value).

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for
    layered snow slabs. *The Cryosphere*, 17(4), 1475–1496.
    https://doi.org/10.5194/tc-17-1475-2023
    """
    return ufloat(5.09, 0.0)
