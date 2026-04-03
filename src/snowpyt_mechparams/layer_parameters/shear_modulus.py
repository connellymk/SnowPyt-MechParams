"""Methods to calculate shear modulus of a snow layer."""

from typing import Any

from uncertainties import ufloat


def calculate_shear_modulus(method: str, include_method_uncertainty: bool = True, **kwargs: Any) -> ufloat:
    """
    Calculate shear modulus of a slab layer based on specified method and
    input parameters.

    Parameters
    ----------
    method : str
        Method to use for shear modulus calculation. Available methods:
        - 'lame_relationship': Uses the isotropic Lamé relationship
          G = E / (2 * (1 + ν))
    include_method_uncertainty : bool, optional
        Accepted for API consistency but has no effect. The Lamé relationship
        is deterministic, so only elastic_modulus and poissons_ratio
        uncertainties propagate. Default is True.
    **kwargs
        Method-specific parameters

    Returns
    -------
    ufloat
        Calculated shear modulus in MPa with associated uncertainty

    Raises
    ------
    ValueError
        If method is not recognized or required parameters are missing
    """
    if method.lower() == 'lame_relationship':
        return _calculate_shear_modulus_lame_relationship(
            include_method_uncertainty=include_method_uncertainty,
            **kwargs,
        )
    else:
        available_methods = ['lame_relationship']
        raise ValueError(
            f"Unknown method: {method}. Available methods: {available_methods}"
        )


def _calculate_shear_modulus_lame_relationship(
    elastic_modulus: ufloat,
    poissons_ratio: ufloat,
    include_method_uncertainty: bool = True,
) -> ufloat:
    """
    Calculate shear modulus from elastic modulus and Poisson's ratio using the
    isotropic Lamé relationship.

    Parameters
    ----------
    elastic_modulus : ufloat
        Elastic modulus (E) in MPa with associated uncertainty
    poissons_ratio : ufloat
        Poisson's ratio (ν) with associated uncertainty
    include_method_uncertainty : bool, optional
        Accepted for API consistency but has no effect. The Lamé relationship
        has no empirical fit parameters, so only input uncertainties propagate.

    Returns
    -------
    ufloat
        Shear modulus (G) in MPa with associated uncertainty

    Notes
    -----
    For isotropic linear elasticity:

    G = E / (2 * (1 + ν))

    The ``include_method_uncertainty`` flag is a no-op because the relationship
    introduces no additional empirical method uncertainty beyond the propagated
    uncertainty in E and ν.
    """
    return elastic_modulus / (2 * (1 + poissons_ratio))
