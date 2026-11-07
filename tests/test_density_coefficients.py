"""Independent coefficient, domain and first-order error checks.

Expected tables are test data, never read from the implementation: Geldsetzer
(2000), Tables 3/4; Kim & Jamieson (2014), Tables 2/3 and Equation 5/Table 6.
The RG uncertainty conventions follow the documented implementation; see the
coverage report for the empirical limitations of those conventions.
"""

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.methods.layer.density import calculate_density

# grain, intercept, slope, residual SE, lower HHI, upper HHI
LINEAR = {
    "geldsetzer": [
        ("PP", 45, 36, 27, 0.67, 4),
        ("PPgp", 83, 37, 42, 0.67, 4),
        ("DF", 65, 36, 30, 0.67, 4.33),
        ("FC", 112, 46, 43, 0.67, 4.67),
        ("DH", 185, 25, 41, 1, 5),
    ],
    "kim_jamieson_table2": [
        ("PP", 41.3, 40.3, 27, 0.67, 4),
        ("PPgp", 61.8, 46.4, 43, 0.67, 4),
        ("DF", 62.5, 37.4, 31, 0.67, 4.67),
        ("RGxf", 85, 46.3, 40, 0.67, 4.33),
        ("FC", 103, 50.6, 47, 0.67, 5),
        ("FCxr", 68.8, 58.6, 46, 0.67, 5.33),
        ("DH", 214, 19, 48, 1, 5),
        ("MFcr", 235, 15.1, 58, 2, 5.33),
    ],
}
# grain, hardness coefficient, grain-size coefficient, intercept, SE, HHI limits
MULTIVARIATE = [
    ("FC", 51.9, 19.7, 82.8, 46, 1.67, 4),
    ("FCxr", 60.4, 27.7, 36.7, 45, 2.33, 4.33),
    ("PP", 40, -7.33, 52.8, 25, 0.67, 2),
    ("PPgp", 38.8, 18.8, 35.7, 33, 1, 3.33),
    ("DF", 37.9, -8.87, 71.4, 31, 1, 3),
    ("MF", 34.9, 11.2, 124.5, 63, 2.33, 4.33),
]


def assert_value(result, mean, sigma):
    assert result.nominal_value == pytest.approx(mean, rel=1e-12)
    assert result.std_dev == pytest.approx(sigma, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize(
    "method,row", [(m, r) for m, rows in LINEAR.items() for r in rows]
)
@pytest.mark.parametrize("with_method", [False, True])
@pytest.mark.parametrize("position", [0, 0.5, 1])
def test_every_linear_coefficient_and_inclusive_boundary(
    method, row, with_method, position
):
    grain, a, b, se, low, high = row
    h = (
        low + position * (high - low)
        if position == 0.5
        else (low if position == 0 else high)
    )
    result = calculate_density(
        method.upper(),
        hand_hardness_index=ufloat(h, 0.12),
        grain_form=grain,
        include_method_uncertainty=with_method,
    )
    assert_value(result, a + b * h, math.hypot(b * 0.12, se if with_method else 0))


@pytest.mark.parametrize("row", MULTIVARIATE)
@pytest.mark.parametrize("with_method", [False, True])
@pytest.mark.parametrize("position", [0, 0.5, 1])
def test_every_multivariate_coefficient_and_inclusive_boundary(
    row, with_method, position
):
    grain, a, b, c, se, low, high = row
    h = (low + high) / 2 if position == 0.5 else (low if position == 0 else high)
    result = calculate_density(
        "kim_jamieson_table6",
        hand_hardness_index=ufloat(h, 0.12),
        grain_form=grain,
        grain_size=ufloat(1.7, 0.25),
        include_method_uncertainty=with_method,
    )
    sigma = math.sqrt(
        (a * 0.12) ** 2 + (b * 0.25) ** 2 + (se if with_method else 0) ** 2
    )
    assert_value(result, a * h + b * 1.7 + c, sigma)


@pytest.mark.parametrize(
    "method,low,high", [("geldsetzer", 1, 5.33), ("kim_jamieson_table2", 0.67, 5.33)]
)
@pytest.mark.parametrize("with_method", [False, True])
@pytest.mark.parametrize("position", [0, 0.5, 1])
def test_nonlinear_values_and_analytic_derivatives(
    method, low, high, with_method, position
):
    h = (low + high) / 2 if position == 0.5 else (low if position == 0 else high)
    if method == "geldsetzer":
        mean = 154 + 1.51 * h**3.15
        input_sigma = 1.51 * 3.15 * h**2.15 * 0.12
        method_sigma = 46
    else:
        mean = 91.8 * math.exp(0.270 * h)
        input_sigma = mean * 0.270 * 0.12
        method_sigma = mean * h * 0.2
    result = calculate_density(
        method,
        hand_hardness_index=ufloat(h, 0.12),
        grain_form="RG",
        include_method_uncertainty=with_method,
    )
    assert_value(
        result, mean, math.hypot(input_sigma, method_sigma if with_method else 0)
    )


DOMAINS = [(m, r[0], r[-2], r[-1]) for m, rows in LINEAR.items() for r in rows]
DOMAINS += [("geldsetzer", "RG", 1, 5.33), ("kim_jamieson_table2", "RG", 0.67, 5.33)]
DOMAINS += [("kim_jamieson_table6", r[0], r[-2], r[-1]) for r in MULTIVARIATE]


@pytest.mark.parametrize("method,grain,low,high", DOMAINS)
@pytest.mark.parametrize("side", ["below", "above", "nan"])
def test_neighboring_invalid_hardness(method, grain, low, high, side):
    h = {
        "below": math.nextafter(low, -math.inf),
        "above": math.nextafter(high, math.inf),
        "nan": math.nan,
    }[side]
    extra = {"grain_size": 1.7} if method == "kim_jamieson_table6" else {}
    result = calculate_density(method, hand_hardness_index=h, grain_form=grain, **extra)
    assert math.isnan(result.nominal_value)
    assert math.isnan(result.std_dev)


@pytest.mark.parametrize(
    "method", ["geldsetzer", "kim_jamieson_table2", "kim_jamieson_table6"]
)
def test_missing_hardness(method):
    extra = {"grain_size": 1.7} if method == "kim_jamieson_table6" else {}
    result = calculate_density(
        method, hand_hardness_index=None, grain_form="PP", **extra
    )
    assert math.isnan(result.nominal_value)
    assert math.isnan(result.std_dev)


@pytest.mark.parametrize(
    "method,expected",
    [
        ("geldsetzer", 117),
        ("kim_jamieson_table2", 121.9),
        ("kim_jamieson_table6", 118.14),
        ("kim_jamieson_table5", 118.14),
    ],
)
def test_plain_numbers_and_legacy_alias(method, expected):
    extra = (
        {"grain_size": 2}
        if method in {"kim_jamieson_table6", "kim_jamieson_table5"}
        else {}
    )
    result = calculate_density(
        method,
        hand_hardness_index=2,
        grain_form="PP",
        include_method_uncertainty=False,
        **extra,
    )
    assert_value(result, expected, 0)
