"""Methods to calculate total fracture energy (Gc) of a weak layer.

Gc represents the energy per unit area required to propagate a crack through
the weak layer.

Candidate future methods:
  - Schweizer et al. (2011): Gc from PST critical crack length
  - Gaume et al. (2017): Gc from density and microstructural parameters
"""

from typing import Any

from uncertainties import ufloat


def calculate_G_c(method: str, **kwargs: Any) -> ufloat:
    """
    Calculate the total fracture energy of a weak layer.

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
        Total fracture energy in J/m² with associated uncertainty.

    Raises
    ------
    ValueError
        If *method* is not recognised.
    """
    if method.lower() == 'weissgraeber_rosendahl':
        return _calculate_G_c_weissgraeber_rosendahl()
    else:
        available_methods = ['weissgraeber_rosendahl']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_G_c_weissgraeber_rosendahl() -> ufloat:
    """
    Return the total fracture energy reference value from
    Weißgraeber & Rosendahl (2023).

    This is also the built-in default used by WEAC (``WeakLayer.G_c = 1.0``).

    Returns
    -------
    ufloat
        ``ufloat(1.0, 0.0)`` J/m²  (no uncertainty — constant reference value).

    References
    ----------
    Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for
    layered snow slabs. *The Cryosphere*, 17(4), 1475–1496.
    https://doi.org/10.5194/tc-17-1475-2023
    """
    return ufloat(1.0, 0.0)
