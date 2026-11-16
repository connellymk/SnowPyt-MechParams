"""Regression checks for the three reviewer-response behavior changes."""

import math
from types import SimpleNamespace as NS
import pytest
from uncertainties import ufloat
from snowpyt_mechparams.models.pit_parser import parse_pit
from snowpyt_mechparams.methods.layer.elastic_modulus import calculate_elastic_modulus


def number(value):
    return float(getattr(value, "nominal_value", value))


@pytest.mark.parametrize(
    "grain,low,high",
    [
        ("SH", 67.8358, 175.0897),
        ("DF", 148.5054, 355.6796),
        ("RG", 148.5054, 355.6796),
        ("FC", 150.3388, 462.9335),
        ("DH", 150.3388, 462.9335),
    ],
)
def test_author_supplied_schottner_bounds(grain, low, high):
    for rho, valid in [
        (math.nextafter(low, -math.inf), False),
        (low, True),
        (math.nextafter(low, math.inf), True),
        ((low + high) / 2, True),
        (math.nextafter(high, -math.inf), True),
        (high, True),
        (math.nextafter(high, math.inf), False),
    ]:
        actual = calculate_elastic_modulus(
            "schottner",
            density=ufloat(rho, 50),
            grain_form=grain + "xx",
            include_method_uncertainty=False,
        )
        assert math.isfinite(actual.nominal_value) == valid


@pytest.mark.parametrize("grain", ["PP", "PPgp", "ppsd"])
def test_wautier_precipitation_particles(grain):
    result = calculate_elastic_modulus("wautier", density=200, grain_form=grain)
    assert number(result) == pytest.approx(10000 * 0.78 * (200 / 917) ** 2.34)


def raw_profile(layer_bounds, samples):
    def layer(top, h):
        return NS(
            depth_top=top,
            thickness=h,
            hardness="1F",
            layer_of_concern=False,
            grain_form_primary=NS(
                sub_grain_class_code=None,
                basic_grain_class_code="RG",
                grain_size_avg=[2, "mm"],
            ),
        )

    return NS(
        snow_profile=NS(
            layers=[layer(*b) for b in layer_bounds],
            density_profile=[
                NS(depth_top=t, thickness=h, density=r) for t, h, r in samples
            ],
        ),
        stability_tests=None,
    )


@pytest.mark.parametrize("size", [-1, 0, 0.25, 1, 3])
def test_parser_relative_grain_size(size):
    raw = raw_profile([([0, "cm"], [10, "cm"])], [])
    raw.snow_profile.layers[0].grain_form_primary.grain_size_avg = [size, "mm"]
    value = parse_pit(raw).layers[0].grain_size_avg
    assert value.nominal_value == size
    assert value.std_dev == pytest.approx(0.48 * abs(size))
