"""Numerical validation tests for elastic modulus calculation methods.

Each test verifies the calculation against hand-computed expected values
derived from the regression coefficients in the source papers.

Sources:
- Bergfeld et al. (2023), Eq. 4 / Appendix B
- Kochle & Schneebeli (2014), Eqs. 11-12
- Wautier et al. (2015), Eq. 5
- Schottner et al. (2026)
"""

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.layer_parameters.elastic_modulus import calculate_elastic_modulus
from snowpyt_mechparams.constants import RHO_ICE


# ---------------------------------------------------------------------------
# Bergfeld
# ---------------------------------------------------------------------------

class TestBergfeldNumerical:
    """E = C0 * (rho/rho_ice)^C1 where C0=6500 MPa, C1=4.4."""

    def test_rho_250(self):
        """rho=250: E = 6500 * (250/917)^4.4."""
        rho = ufloat(250.0, 0.0)
        expected = 6500.0 * (250.0 / RHO_ICE) ** 4.4
        result = calculate_elastic_modulus(
            "bergfeld", density=rho, grain_form="RG",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_rho_200(self):
        """rho=200: E = 6500 * (200/917)^4.4."""
        rho = ufloat(200.0, 0.0)
        expected = 6500.0 * (200.0 / RHO_ICE) ** 4.4
        result = calculate_elastic_modulus(
            "bergfeld", density=rho, grain_form="DF",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_below_range_returns_nan(self):
        """Density < 110 kg/m³ is out of range."""
        result = calculate_elastic_modulus(
            "bergfeld", density=ufloat(100.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_above_range_returns_nan(self):
        """Density > 363 kg/m³ is out of range."""
        result = calculate_elastic_modulus(
            "bergfeld", density=ufloat(400.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_elastic_modulus(
            "bergfeld", density=ufloat(250.0, 0.0), grain_form="FC",
        )
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# Kochle
# ---------------------------------------------------------------------------

class TestKochleNumerical:
    """E = E_ice * C2 * exp(C3 * rho/rho_ice).

    Low density (150-250): C0=0.0061, C1=0.0396
    High density (250-450): C0=6.0457, C1=0.011
    C2 = C0/E_ice, C3 = C1*rho_ice
    """

    def test_low_density_rho_200(self):
        """rho=200, E_ice=10000: C2=0.0061/10000, C3=0.0396*917."""
        import uncertainties.umath as umath
        rho = ufloat(200.0, 0.0)
        E_ice = ufloat(10000.0, 0.0)
        C2 = 0.0061 / 10000.0
        C3 = 0.0396 * RHO_ICE
        expected = 10000.0 * C2 * math.exp(C3 * 200.0 / RHO_ICE)
        result = calculate_elastic_modulus(
            "kochle", density=rho, grain_form="RG",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_high_density_rho_350(self):
        """rho=350, high-density fit: C0=6.0457, C1=0.011."""
        rho = ufloat(350.0, 0.0)
        C2 = 6.0457 / 10000.0
        C3 = 0.011 * RHO_ICE
        expected = 10000.0 * C2 * math.exp(C3 * 350.0 / RHO_ICE)
        result = calculate_elastic_modulus(
            "kochle", density=rho, grain_form="RG",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_below_range_returns_nan(self):
        result = calculate_elastic_modulus(
            "kochle", density=ufloat(100.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_above_range_returns_nan(self):
        result = calculate_elastic_modulus(
            "kochle", density=ufloat(500.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_unsupported_grain_form_returns_nan(self):
        """Kochle only supports RG, RC, DH, MF."""
        result = calculate_elastic_modulus(
            "kochle", density=ufloat(300.0, 0.0), grain_form="PP",
        )
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# Wautier
# ---------------------------------------------------------------------------

class TestWautierNumerical:
    """E = E_ice * A * (rho/rho_ice)^n where A=0.78, n=2.34, E_ice=1060 MPa."""

    def test_rho_300(self):
        """rho=300: E = 1060 * 0.78 * (300/917)^2.34."""
        rho = ufloat(300.0, 0.0)
        E_ice = 1060.0
        expected = E_ice * 0.78 * (300.0 / RHO_ICE) ** 2.34
        result = calculate_elastic_modulus(
            "wautier", density=rho, grain_form="RG",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_rho_200(self):
        rho = ufloat(200.0, 0.0)
        E_ice = 1060.0
        expected = E_ice * 0.78 * (200.0 / RHO_ICE) ** 2.34
        result = calculate_elastic_modulus(
            "wautier", density=rho, grain_form="FC",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_below_range_returns_nan(self):
        result = calculate_elastic_modulus(
            "wautier", density=ufloat(50.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_above_range_returns_nan(self):
        result = calculate_elastic_modulus(
            "wautier", density=ufloat(600.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# Schottner
# ---------------------------------------------------------------------------

class TestSchottnerNumerical:
    """E = E_ice * A * (rho/rho_ice)^n.  Grain-type-dependent A, n.

    E_ice = 10000 MPa (polycrystalline).
    DF/RG: A=0.40, n=4.6
    FC/DH: A=1.8, n=5.1
    SH: A=0.011, n=1.7
    """

    def test_RG_rho_300(self):
        rho = ufloat(300.0, 0.0)
        expected = 10000.0 * 0.40 * (300.0 / RHO_ICE) ** 4.6
        result = calculate_elastic_modulus(
            "schottner", density=rho, grain_form="RG",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_FC_rho_250(self):
        rho = ufloat(250.0, 0.0)
        expected = 10000.0 * 1.8 * (250.0 / RHO_ICE) ** 5.1
        result = calculate_elastic_modulus(
            "schottner", density=rho, grain_form="FC",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_SH_rho_200(self):
        rho = ufloat(200.0, 0.0)
        expected = 10000.0 * 0.011 * (200.0 / RHO_ICE) ** 1.7
        result = calculate_elastic_modulus(
            "schottner", density=rho, grain_form="SH",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_elastic_modulus(
            "schottner", density=ufloat(300.0, 0.0), grain_form="PP",
        )
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# Unknown method
# ---------------------------------------------------------------------------

class TestUnknownElasticModulusMethod:
    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_elastic_modulus(
                "nonexistent", density=ufloat(250.0, 0.0), grain_form="RG"
            )
