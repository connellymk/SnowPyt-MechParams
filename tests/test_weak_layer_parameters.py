"""
Direct unit tests for the weak_layer_parameters module.

Tests cover the public calculate_* functions:
- Correct nominal values and zero uncertainty for reference constants
- ValueError for unknown method strings
- NaN handling and valid output for density-dependent methods
- Return type is uncertainties.UFloat throughout
"""

from __future__ import annotations

import math

import pytest
from uncertainties import ufloat, UFloat

from snowpyt_mechparams.weak_layer_parameters import (
    calculate_G_c,
    calculate_G_Ic,
    calculate_G_IIc,
    calculate_tau_c,
    calculate_sigma_c_plus,
    calculate_sigma_c_minus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nominal(v: UFloat) -> float:
    return float(v.nominal_value)

def _std(v: UFloat) -> float:
    return float(v.std_dev)


# ---------------------------------------------------------------------------
# calculate_G_c
# ---------------------------------------------------------------------------

class TestCalculateGc:
    def test_weissgraeber_rosendahl_nominal(self):
        result = calculate_G_c("weissgraeber_rosendahl")
        assert _nominal(result) == pytest.approx(1.0)

    def test_weissgraeber_rosendahl_zero_uncertainty(self):
        result = calculate_G_c("weissgraeber_rosendahl")
        assert _std(result) == 0.0

    def test_returns_ufloat(self):
        assert isinstance(calculate_G_c("weissgraeber_rosendahl"), UFloat)

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_G_c("no_such_method")

    def test_case_insensitive(self):
        result = calculate_G_c("Weissgraeber_Rosendahl")
        assert _nominal(result) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# calculate_G_Ic
# ---------------------------------------------------------------------------

class TestCalculateGIc:
    def test_weissgraeber_rosendahl_nominal(self):
        result = calculate_G_Ic("weissgraeber_rosendahl")
        assert _nominal(result) == pytest.approx(0.56)

    def test_weissgraeber_rosendahl_zero_uncertainty(self):
        result = calculate_G_Ic("weissgraeber_rosendahl")
        assert _std(result) == 0.0

    def test_returns_ufloat(self):
        assert isinstance(calculate_G_Ic("weissgraeber_rosendahl"), UFloat)

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_G_Ic("no_such_method")


# ---------------------------------------------------------------------------
# calculate_G_IIc
# ---------------------------------------------------------------------------

class TestCalculateGIIc:
    def test_weissgraeber_rosendahl_nominal(self):
        result = calculate_G_IIc("weissgraeber_rosendahl")
        assert _nominal(result) == pytest.approx(0.79)

    def test_weissgraeber_rosendahl_zero_uncertainty(self):
        result = calculate_G_IIc("weissgraeber_rosendahl")
        assert _std(result) == 0.0

    def test_returns_ufloat(self):
        assert isinstance(calculate_G_IIc("weissgraeber_rosendahl"), UFloat)

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_G_IIc("no_such_method")


# ---------------------------------------------------------------------------
# calculate_tau_c
# ---------------------------------------------------------------------------

class TestCalculateTauC:
    def test_weissgraeber_rosendahl_nominal(self):
        result = calculate_tau_c("weissgraeber_rosendahl")
        assert _nominal(result) == pytest.approx(5.09)

    def test_weissgraeber_rosendahl_zero_uncertainty(self):
        result = calculate_tau_c("weissgraeber_rosendahl")
        assert _std(result) == 0.0

    def test_returns_ufloat(self):
        assert isinstance(calculate_tau_c("weissgraeber_rosendahl"), UFloat)

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_tau_c("no_such_method")


# ---------------------------------------------------------------------------
# calculate_sigma_c_plus
# ---------------------------------------------------------------------------

class TestCalculateSigmaCPlus:
    def test_weissgraeber_rosendahl_nominal(self):
        result = calculate_sigma_c_plus("weissgraeber_rosendahl")
        assert _nominal(result) == pytest.approx(6.16)

    def test_weissgraeber_rosendahl_zero_uncertainty(self):
        result = calculate_sigma_c_plus("weissgraeber_rosendahl")
        assert _std(result) == 0.0

    def test_sigrist_returns_ufloat(self):
        result = calculate_sigma_c_plus("sigrist", density=ufloat(250.0, 0.0))
        assert isinstance(result, UFloat)

    def test_sigrist_positive_for_valid_density(self):
        result = calculate_sigma_c_plus("sigrist", density=ufloat(250.0, 0.0))
        assert _nominal(result) > 0.0
        assert not math.isnan(_nominal(result))

    def test_sigrist_nan_for_none_density(self):
        result = calculate_sigma_c_plus("sigrist", density=None)
        assert math.isnan(_nominal(result))

    def test_sigrist_nan_for_negative_density(self):
        result = calculate_sigma_c_plus("sigrist", density=ufloat(-1.0, 0.0))
        assert math.isnan(_nominal(result))

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_sigma_c_plus("no_such_method")


# ---------------------------------------------------------------------------
# calculate_sigma_c_minus
# ---------------------------------------------------------------------------

class TestCalculateSigmaCMinus:
    def test_reiweger_nominal(self):
        result = calculate_sigma_c_minus("reiweger")
        assert _nominal(result) == pytest.approx(2.6)

    def test_reiweger_zero_uncertainty(self):
        result = calculate_sigma_c_minus("reiweger")
        assert _std(result) == 0.0

    def test_reiweger_returns_ufloat(self):
        assert isinstance(calculate_sigma_c_minus("reiweger"), UFloat)

    def test_reiweger_ignores_density(self):
        """density kwarg is accepted for API consistency but doesn't affect output."""
        result_no_density = calculate_sigma_c_minus("reiweger")
        result_with_density = calculate_sigma_c_minus("reiweger", density=ufloat(300.0, 0.0))
        assert _nominal(result_no_density) == pytest.approx(_nominal(result_with_density))

    def test_mellor_returns_ufloat(self):
        result = calculate_sigma_c_minus("mellor", density=ufloat(250.0, 0.0))
        assert isinstance(result, UFloat)

    def test_mellor_positive_for_valid_density(self):
        result = calculate_sigma_c_minus("mellor", density=ufloat(250.0, 0.0))
        assert _nominal(result) > 0.0
        assert not math.isnan(_nominal(result))

    def test_mellor_nan_for_none_density(self):
        result = calculate_sigma_c_minus("mellor", density=None)
        assert math.isnan(_nominal(result))

    def test_mellor_nan_for_negative_density(self):
        result = calculate_sigma_c_minus("mellor", density=ufloat(-1.0, 0.0))
        assert math.isnan(_nominal(result))

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_sigma_c_minus("no_such_method")

    def test_weissgraeber_rosendahl_no_longer_valid(self):
        """weissgraeber_rosendahl was removed — it was a misattribution of Reiweger et al. (2015)."""
        with pytest.raises(ValueError):
            calculate_sigma_c_minus("weissgraeber_rosendahl")
