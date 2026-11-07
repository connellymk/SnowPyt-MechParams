"""Direct slab contracts, analytical integrals, units, and uncertainty."""

import math

import pytest
from uncertainties import nominal_value, std_dev, ufloat

from snowpyt_mechparams.methods.slab import (
    calculate_A11,
    calculate_A55,
    calculate_B11,
    calculate_D11,
    calculate_slab_weight,
    calculate_slab_weight_shear,
    calculate_slab_weight_shear_with_elasticity,
)
from snowpyt_mechparams.models import Layer, Slab

METHOD = "weissgraeber_rosendahl"
STIFFNESSES = [calculate_A11, calculate_B11, calculate_D11, calculate_A55]


def make_slab():
    return Slab(
        layers=[
            Layer(
                depth_top=7,
                thickness=3,
                elastic_modulus=20,
                poissons_ratio=0.2,
                shear_modulus=8,
                density_calculated=200,
            ),
            Layer(
                depth_top=10,
                thickness=7,
                elastic_modulus=50,
                poissons_ratio=0.3,
                shear_modulus=15,
                density_calculated=300,
            ),
        ],
        angle=30,
    )


@pytest.mark.parametrize("calculate", STIFFNESSES)
def test_empty_mutated_slab_is_rejected(calculate):
    # Slab validates construction, but its public layers list remains mutable.
    slab = make_slab()
    slab.layers.clear()
    value = calculate(METHOD, slab=slab)
    assert math.isnan(nominal_value(value))
    assert math.isnan(std_dev(value))


@pytest.mark.parametrize("calculate", [calculate_A11, calculate_B11, calculate_D11])
@pytest.mark.parametrize("missing", ["elastic_modulus", "poissons_ratio", "thickness"])
def test_missing_input_in_later_layer_invalidates_entire_integral(calculate, missing):
    slab = make_slab()
    setattr(slab.layers[1], missing, None)
    value = calculate(METHOD, slab=slab)
    assert math.isnan(nominal_value(value))
    assert math.isnan(std_dev(value))


@pytest.mark.parametrize("missing", ["shear_modulus", "thickness"])
def test_shear_missing_input_in_later_layer(missing):
    slab = make_slab()
    setattr(slab.layers[1], missing, None)
    assert math.isnan(nominal_value(calculate_A55(METHOD, slab=slab)))


@pytest.mark.parametrize("calculate", [calculate_A11, calculate_B11, calculate_D11])
@pytest.mark.parametrize("nu", [-1.01, -1, 1, 1.01])
@pytest.mark.parametrize("uncertain", [False, True])
def test_singular_and_outside_poisson_domain(calculate, nu, uncertain):
    slab = make_slab()
    slab.layers[1].poissons_ratio = ufloat(nu, 0.01) if uncertain else nu
    assert math.isnan(nominal_value(calculate(METHOD, slab=slab)))


@pytest.mark.parametrize("nu", [math.nextafter(-1, 0), math.nextafter(1, 0)])
def test_poisson_neighbors_inside_mathematical_domain(nu):
    slab = Slab(
        layers=[Layer(thickness=1, elastic_modulus=2, poissons_ratio=nu)], angle=0
    )
    result = calculate_A11(METHOD, slab=slab)
    assert result == pytest.approx(20 / (1 - nu**2), rel=1e-12)


def test_mixed_depths_return_nan_instead_of_arithmetic_error():
    slab = make_slab()
    slab.layers[1].depth_top = None
    for calculate in [calculate_A11, calculate_B11, calculate_D11]:
        assert math.isnan(nominal_value(calculate(METHOD, slab=slab)))


@pytest.mark.parametrize("offset", [0, 7, 100])
@pytest.mark.parametrize("reverse", [False, True])
def test_asymmetric_integrals_translation_and_reversal(offset, reverse):
    slab = make_slab()
    if reverse:
        slab.layers.reverse()
    position = offset
    for layer in slab.layers:
        layer.depth_top = position
        position += layer.thickness
    q1, q2 = 20 / 0.96, 50 / 0.91
    # 30/70 mm layers: centroids +35/-15 mm and local inertia h^3/12.
    expected_a = q1 * 30 + q2 * 70
    expected_b = q1 * 30 * 35 - q2 * 70 * 15
    expected_d = q1 * (30**3 / 12 + 30 * 35**2) + q2 * (70**3 / 12 + 70 * 15**2)
    assert calculate_A11(METHOD, slab=slab) == pytest.approx(expected_a)
    assert calculate_B11(METHOD, slab=slab) == pytest.approx(
        -expected_b if reverse else expected_b
    )
    assert calculate_D11(METHOD, slab=slab) == pytest.approx(expected_d)
    assert calculate_A55(METHOD, slab=slab) == pytest.approx(
        (5 / 6) * (8 * 30 + 15 * 70)
    )


def test_extensional_integration_without_depths():
    slab = make_slab()
    for layer in slab.layers:
        layer.depth_top = None
    assert calculate_A11(METHOD, slab=slab) == pytest.approx(
        20 / 0.96 * 30 + 50 / 0.91 * 70
    )


@pytest.mark.parametrize(
    "calculate,power,factor", [(calculate_A11, 1, 1), (calculate_D11, 3, 1 / 12)]
)
def test_homogeneous_uncertainty_including_correlated_boundaries(
    calculate, power, factor
):
    # The same uncertain thickness determines both faces and the centroid.
    slab = Slab(
        layers=[
            Layer(
                depth_top=ufloat(7, 2),
                thickness=ufloat(10, 0.5),
                elastic_modulus=ufloat(20, 1),
                poissons_ratio=ufloat(0.2, 0.01),
            )
        ],
        angle=0,
    )
    mean = factor * 20 / (1 - 0.2**2) * 100**power
    sigma = mean * math.sqrt(
        (1 / 20) ** 2 + (2 * 0.2 * 0.01 / (1 - 0.2**2)) ** 2 + (power * 0.5 / 10) ** 2
    )
    value = calculate(METHOD, slab=slab)
    assert nominal_value(value) == pytest.approx(mean)
    assert std_dev(value) == pytest.approx(sigma, rel=1e-12)
    coupling = calculate_B11(METHOD, slab=slab)
    assert nominal_value(coupling) == pytest.approx(0, abs=1e-12)
    assert std_dev(coupling) == pytest.approx(0, abs=1e-12)


def test_shear_stiffness_analytic_uncertainty():
    slab = Slab(
        layers=[Layer(thickness=ufloat(10, 0.5), shear_modulus=ufloat(8, 0.4))], angle=0
    )
    value = calculate_A55(METHOD, slab=slab)
    assert nominal_value(value) == pytest.approx((5 / 6) * 8 * 100)
    assert std_dev(value) == pytest.approx((5 / 6) * math.hypot(100 * 0.4, 8 * 5))


def test_weight_units_multilayer_sum_and_analytic_uncertainty():
    slab = Slab(
        layers=[
            Layer(thickness=ufloat(10, 0.5), density_calculated=ufloat(200, 10)),
            Layer(thickness=ufloat(20, 1), density_calculated=ufloat(300, 15)),
        ],
        angle=ufloat(30, 2),
    )
    weight = calculate_slab_weight(slab)
    mean = 9.81 * (200 * 0.1 + 300 * 0.2)
    sigma = 9.81 * math.sqrt(
        (0.1 * 10) ** 2 + (200 * 0.005) ** 2 + (0.2 * 15) ** 2 + (300 * 0.01) ** 2
    )
    assert nominal_value(weight) == pytest.approx(mean)
    assert std_dev(weight) == pytest.approx(sigma)
    slab.slab_weight = weight
    shear = calculate_slab_weight_shear(slab)
    assert nominal_value(shear) == pytest.approx(mean * 0.5)
    assert std_dev(shear) == pytest.approx(
        math.hypot(0.5 * sigma, mean * math.cos(math.pi / 6) * math.pi / 180 * 2)
    )


@pytest.mark.parametrize("angle,factor", [(0, 0), (30, 0.5), (90, 1)])
def test_plain_weight_and_degree_projection(angle, factor):
    slab = make_slab()
    slab.angle = angle
    slab.slab_weight = calculate_slab_weight(slab)
    assert slab.slab_weight == pytest.approx(9.81 * (200 * 0.03 + 300 * 0.07))
    slab.slab_weight_shear = calculate_slab_weight_shear(slab)
    assert nominal_value(slab.slab_weight_shear) == pytest.approx(
        slab.slab_weight * factor
    )
    assert calculate_slab_weight_shear_with_elasticity(slab) is slab.slab_weight_shear


@pytest.mark.parametrize("missing", ["density_calculated", "thickness"])
def test_weight_missing_later_layer_input(missing):
    slab = make_slab()
    setattr(slab.layers[1], missing, None)
    assert calculate_slab_weight(slab) is None


def test_weight_empty_mutated_slab():
    slab = make_slab()
    slab.layers.clear()
    assert calculate_slab_weight(slab) is None


@pytest.mark.parametrize("missing", ["slab_weight", "angle"])
def test_shear_weight_requires_weight_and_angle(missing):
    slab = make_slab()
    slab.slab_weight = 100
    setattr(slab, missing, None)
    assert calculate_slab_weight_shear(slab) is None


@pytest.mark.parametrize(
    "missing", ["elastic_modulus", "poissons_ratio", "slab_weight_shear"]
)
def test_elasticity_gate_requires_each_input(missing):
    slab = make_slab()
    slab.slab_weight_shear = ufloat(100, 10)
    if missing == "slab_weight_shear":
        slab.slab_weight_shear = None
    else:
        setattr(slab.layers[1], missing, None)
    assert calculate_slab_weight_shear_with_elasticity(slab) is None
