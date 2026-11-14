"""Explicit MPa equations and analytic first-order uncertainty oracles."""

import math

import pytest
from uncertainties import nominal_value, std_dev, ufloat

from snowpyt_mechparams.methods.layer import (
    calculate_elastic_modulus,
    calculate_poissons_ratio,
    calculate_shear_modulus,
)


@pytest.mark.parametrize(
    "method,grains,low,high",
    [
        ("bergfeld", ["PP", "RG", "DF"], 110, 363),
        ("kochle", ["RG", "FC", "DH", "MF"], 150, 450),
        ("wautier", ["PP", "DF", "RG", "FC", "DH", "MF"], 103, 544),
    ],
)
def test_elastic_domains_and_all_supported_grains(method, grains, low, high):
    for grain in grains:
        for rho in [low, (low + high) / 2, high]:
            if method == "bergfeld":
                expected = 6500 * (rho / 917) ** 4.4
            elif method == "kochle":
                expected = (
                    0.0061 * math.exp(0.0396 * rho)
                    if rho < 250
                    else 6.0457 * math.exp(0.011 * rho)
                )
            else:
                expected = 10000 * 0.78 * (rho / 917) ** 2.34
            value = calculate_elastic_modulus(
                method.upper(),
                density=rho,
                grain_form=grain.lower() + "xx",
                include_method_uncertainty=False,
            )
            assert nominal_value(value) == pytest.approx(expected, rel=1e-12)
            assert std_dev(value) == 0
        for rho in [math.nextafter(low, -math.inf), math.nextafter(high, math.inf)]:
            value = calculate_elastic_modulus(method, density=rho, grain_form=grain)
            assert math.isnan(nominal_value(value))


@pytest.mark.parametrize(
    "rho", [math.nextafter(250, -math.inf), 250, math.nextafter(250, math.inf)]
)
def test_kochle_piecewise_transition_and_ice_cancellation(rho):
    a, b = (0.0061, 0.0396) if rho < 250 else (6.0457, 0.011)
    value = calculate_elastic_modulus(
        "kochle", density=ufloat(rho, 7), grain_form="FC", E_ice=ufloat(9000, 500)
    )
    mean = a * math.exp(b * rho)
    assert nominal_value(value) == pytest.approx(mean, rel=1e-12)
    assert std_dev(value) == pytest.approx(mean * b * 7, rel=1e-12)


@pytest.mark.parametrize("with_method", [False, True])
def test_bergfeld_analytic_uncertainty(with_method):
    value = calculate_elastic_modulus(
        "bergfeld",
        density=ufloat(250, 7),
        grain_form="RG",
        include_method_uncertainty=with_method,
    )
    mean = 6500 * (250 / 917) ** 4.4
    sigma = mean * math.hypot(
        4.4 * 7 / 250, math.log(250 / 917) * (0.18 if with_method else 0)
    )
    assert nominal_value(value) == pytest.approx(mean, rel=1e-12)
    assert std_dev(value) == pytest.approx(sigma, rel=1e-12)


def test_wautier_ice_modulus_units_and_uncertainty():
    value = calculate_elastic_modulus(
        "wautier", density=ufloat(300, 8), grain_form="DF", E_ice=ufloat(9000, 400)
    )
    mean = 9000 * 0.78 * (300 / 917) ** 2.34
    assert nominal_value(value) == pytest.approx(mean, rel=1e-12)
    assert std_dev(value) == pytest.approx(
        mean * math.hypot(400 / 9000, 2.34 * 8 / 300), rel=1e-12
    )


@pytest.mark.parametrize(
    "grain,a,sa,n,sn",
    [
        ("DF", 0.4, 0.3, 4.6, 0.6),
        ("RG", 0.4, 0.3, 4.6, 0.6),
        ("FC", 1.8, 0.7, 5.1, 0.3),
        ("DH", 1.8, 0.7, 5.1, 0.3),
        ("SH", 0.011, 0.009, 1.7, 0.4),
    ],
)
@pytest.mark.parametrize("with_method", [False, True])
@pytest.mark.parametrize("uncertain_input", [False, True])
def test_schottner_every_fit_and_analytic_uncertainty(
    grain, a, sa, n, sn, with_method, uncertain_input
):
    rho = ufloat(300, 8) if uncertain_input else 300
    ice = ufloat(10000, 400) if uncertain_input else 10000
    value = calculate_elastic_modulus(
        "schottner",
        density=rho,
        grain_form=grain.lower() + "xx",
        E_ice=ice,
        include_method_uncertainty=with_method,
    )
    mean = 10000 * a * (300 / 917) ** n
    relative_variance = (
        ((400 / 10000) ** 2 + (n * 8 / 300) ** 2) if uncertain_input else 0
    )
    if with_method:
        relative_variance += (sa / a) ** 2 + (math.log(300 / 917) * sn) ** 2
    assert nominal_value(value) == pytest.approx(mean, rel=1e-12)
    assert std_dev(value) == pytest.approx(
        mean * math.sqrt(relative_variance), rel=1e-12, abs=1e-12
    )


@pytest.mark.parametrize(
    "method,grain,mean,sigma",
    [
        ("kochle", "RG", 0.171, 0.026),
        ("kochle", "FC", 0.13, 0.04),
        ("kochle", "DH", 0.087, 0.063),
        ("srivastava", "RG", 0.191, 0.008),
        ("srivastava", "PP", 0.132, 0.053),
        ("srivastava", "DF", 0.132, 0.053),
        ("srivastava", "FC", 0.17, 0.02),
        ("srivastava", "DH", 0.17, 0.02),
    ],
)
@pytest.mark.parametrize("with_method", [False, True])
def test_poisson_every_grain_and_uncertainty_switch(
    method, grain, mean, sigma, with_method
):
    extra = {"density": ufloat(300, 40)} if method == "srivastava" else {}
    value = calculate_poissons_ratio(
        method.upper(),
        grain_form=grain.lower() + "xx",
        include_method_uncertainty=with_method,
        **extra,
    )
    assert nominal_value(value) == pytest.approx(mean)
    # Density selects the domain; it is not a variable in these constant fits.
    assert std_dev(value) == pytest.approx(sigma if with_method else 0)


@pytest.mark.parametrize("grain", ["RG", "PP", "DF", "FC", "DH"])
def test_srivastava_exact_domain_edges(grain):
    mean = 0.191 if grain == "RG" else (0.132 if grain in ["PP", "DF"] else 0.17)
    for rho in [math.nextafter(200, -math.inf), 200]:
        assert math.isnan(
            nominal_value(
                calculate_poissons_ratio("srivastava", density=rho, grain_form=grain)
            )
        )
    for rho in [math.nextafter(200, math.inf), 580]:
        assert nominal_value(
            calculate_poissons_ratio("srivastava", density=rho, grain_form=grain)
        ) == pytest.approx(mean)
    result = calculate_poissons_ratio(
        "srivastava", density=math.nextafter(580, math.inf), grain_form=grain
    )
    if grain == "RG":
        assert math.isnan(nominal_value(result))
    else:
        assert nominal_value(result) == pytest.approx(mean)


@pytest.mark.parametrize("with_method", [False, True])
def test_lame_analytic_error_and_plain_numbers(with_method):
    kwargs = {"include_method_uncertainty": with_method}
    exact = calculate_shear_modulus(
        "LAME_RELATIONSHIP", elastic_modulus=18, poissons_ratio=0.2, **kwargs
    )
    assert exact == pytest.approx(7.5)
    value = calculate_shear_modulus(
        "lame_relationship",
        elastic_modulus=ufloat(18, 1.8),
        poissons_ratio=ufloat(0.2, 0.01),
        **kwargs,
    )
    assert nominal_value(value) == pytest.approx(7.5)
    assert std_dev(value) == pytest.approx(
        math.hypot(1.8 / 2.4, 18 * 0.01 / (2 * 1.2**2)), rel=1e-12
    )
