"""Numerical validation tests for shear modulus calculation methods.

Sources:
- Wautier et al. (2015), Eq. 5: G_snow/G_ice = A * (rho/rho_ice)^n
  A=0.92, n=2.51
"""

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.layer_parameters.shear_modulus import calculate_shear_modulus
from snowpyt_mechparams.constants import RHO_ICE, G_ICE


class TestWautierShearModulusNumerical:
    """G = G_ice * A * (rho/rho_ice)^n, A=0.92, n=2.51, G_ice=407.7 MPa."""

    def test_rho_300(self):
        rho = ufloat(300.0, 0.0)
        G_ice_val = 407.7
        expected = G_ice_val * 0.92 * (300.0 / RHO_ICE) ** 2.51
        result = calculate_shear_modulus(
            "wautier", density=rho, grain_form="RG",
            include_method_uncertainty=False,
            G_ice=ufloat(G_ice_val, 0.0),
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_rho_200(self):
        rho = ufloat(200.0, 0.0)
        G_ice_val = 407.7
        expected = G_ice_val * 0.92 * (200.0 / RHO_ICE) ** 2.51
        result = calculate_shear_modulus(
            "wautier", density=rho, grain_form="FC",
            include_method_uncertainty=False,
            G_ice=ufloat(G_ice_val, 0.0),
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_below_range_returns_nan(self):
        result = calculate_shear_modulus(
            "wautier", density=ufloat(50.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_above_range_returns_nan(self):
        result = calculate_shear_modulus(
            "wautier", density=ufloat(600.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_shear_modulus(
            "wautier", density=ufloat(300.0, 0.0), grain_form="PP",
        )
        assert math.isnan(result.nominal_value)


class TestUnknownShearModulusMethod:
    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_shear_modulus("nonexistent", density=ufloat(300.0, 0.0), grain_form="RG")
