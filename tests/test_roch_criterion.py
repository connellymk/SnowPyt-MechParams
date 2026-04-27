"""Tests for Roch stability criterion helpers."""

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.stability_criteria.roch import (
    calculate_roch,
    calculate_shear_stress,
)


def _loaded_slab(angle):
    """Return a slab with the density and thickness needed for Roch calculations."""
    return Slab(
        layers=[Layer(thickness=10.0, density_calculated=200.0)],
        angle=angle,
    )


@pytest.mark.parametrize("angle", [None, float("nan")])
def test_shear_stress_missing_angle_returns_none(angle):
    """Missing or NaN slope angle should be treated as missing input."""
    assert calculate_shear_stress(_loaded_slab(angle)) is None


@pytest.mark.parametrize("angle", [None, float("nan")])
def test_roch_missing_angle_returns_none(angle):
    """Roch should fail gracefully when slope angle is unavailable."""
    assert calculate_roch(_loaded_slab(angle), tau_c=1.0) is None


def test_roch_uncertain_angle_preserves_propagated_uncertainty():
    """Use the original uncertain angle after validation, not its nominal value."""
    slab = _loaded_slab(ufloat(30.0, 2.0))

    result = calculate_roch(slab, tau_c=1.0)

    assert result is not None
    assert result.shear_stress.nominal_value == pytest.approx(
        200.0 * 0.10 * 9.81 * math.sin(math.radians(30.0))
    )
    assert result.shear_stress.std_dev > 0.0
    assert result.stability_index.std_dev > 0.0
