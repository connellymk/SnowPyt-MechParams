"""Numerical validation tests for density calculation methods.

Each test verifies the calculation against hand-computed expected values
derived from the regression coefficients in the source papers.

Sources:
- Geldsetzer & Jamieson (2000), Table 3
- Kim & Jamieson (2014), Tables 2 and 5
"""

import math

import numpy as np
import pytest
from uncertainties import ufloat

from snowpyt_mechparams.layer_parameters.density import calculate_density


# ---------------------------------------------------------------------------
# Geldsetzer
# ---------------------------------------------------------------------------

class TestGeldsetzerNumerical:
    """Verify geldsetzer density against hand-computed values from Table 3."""

    def test_PP_linear(self):
        """PP: rho = 45 + 36*h.  h=1.0 => rho=81."""
        result = calculate_density(
            "geldsetzer",
            hand_hardness_index=ufloat(1.0, 0.0),
            grain_form="PP",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(81.0, abs=0.01)

    def test_FC_linear(self):
        """FC: rho = 112 + 46*h.  h=3.0 => rho=250."""
        result = calculate_density(
            "geldsetzer",
            hand_hardness_index=ufloat(3.0, 0.0),
            grain_form="FC",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(250.0, abs=0.01)

    def test_DH_linear(self):
        """DH: rho = 185 + 25*h.  h=2.0 => rho=235."""
        result = calculate_density(
            "geldsetzer",
            hand_hardness_index=ufloat(2.0, 0.0),
            grain_form="DH",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(235.0, abs=0.01)

    def test_RG_nonlinear(self):
        """RG: rho = 154 + 1.51*h^3.15.  h=3.0 => 154 + 1.51 * 3.0^3.15."""
        h = 3.0
        expected = 154.0 + 1.51 * (h ** 3.15)
        result = calculate_density(
            "geldsetzer",
            hand_hardness_index=ufloat(h, 0.0),
            grain_form="RG",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-4)

    def test_RGmx_linear(self):
        """RGmx: rho = 91 + 42*h.  h=2.0 => rho=175."""
        result = calculate_density(
            "geldsetzer",
            hand_hardness_index=ufloat(2.0, 0.0),
            grain_form="RGmx",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(175.0, abs=0.01)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_density(
            "geldsetzer",
            hand_hardness_index=ufloat(1.0, 0.0),
            grain_form="MF",
        )
        assert math.isnan(result.nominal_value)

    def test_method_uncertainty_adds_SE(self):
        """SE for FC is 43 kg/m³; with exact inputs, std_dev should equal SE."""
        result = calculate_density(
            "geldsetzer",
            hand_hardness_index=ufloat(3.0, 0.0),
            grain_form="FC",
            include_method_uncertainty=True,
        )
        assert result.std_dev == pytest.approx(43.0, abs=0.01)


# ---------------------------------------------------------------------------
# Kim & Jamieson Table 2
# ---------------------------------------------------------------------------

class TestKimJamiesonTable2Numerical:
    """Verify kim_jamieson_table2 density against Table 2 coefficients.

    Table 2 regressions: rho = A + B*h (linear) or rho = A*e^(B*h) (nonlinear for RG).
    Coefficients from Kim & Jamieson (2014) Table 2.
    """

    def test_FC_linear(self):
        """FC: rho = 103 + 50.6*h.  h=2.0 => 103 + 101.2 = 204.2."""
        result = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(2.0, 0.0),
            grain_form="FC",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(103.0 + 50.6 * 2.0, abs=0.01)

    def test_PP_linear(self):
        """PP: rho = 41.3 + 40.3*h.  h=1.0 => 81.6."""
        result = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(1.0, 0.0),
            grain_form="PP",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(41.3 + 40.3 * 1.0, abs=0.01)

    def test_DH_linear(self):
        """DH: rho = 214 + 19*h.  h=1.0 => 233."""
        result = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(1.0, 0.0),
            grain_form="DH",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(214.0 + 19.0 * 1.0, abs=0.01)

    def test_RG_nonlinear(self):
        """RG: rho = 91.8 * e^(0.270*h).  h=2.0 => 91.8*e^0.54."""
        h = 2.0
        expected = 91.8 * math.e ** (0.270 * h)
        result = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(h, 0.0),
            grain_form="RG",
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-4)

    def test_RG_method_uncertainty_propagated_through_exponent(self):
        """RG SE=0.2 is the SE of coefficient B (not a density SE).

        With include_method_uncertainty=True and exact input (h=2, std=0),
        the only source of uncertainty is B=0.270±0.2. The density uncertainty
        should be rho * h * sigma_B = 91.8*e^(0.54) * 2 * 0.2 ≈ 63 kg/m³.
        """
        h = 2.0
        result_with = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(h, 0.0),
            grain_form="RG",
            include_method_uncertainty=True,
        )
        result_without = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(h, 0.0),
            grain_form="RG",
            include_method_uncertainty=False,
        )
        # Nominal values must match regardless of uncertainty flag
        assert result_with.nominal_value == pytest.approx(
            result_without.nominal_value, rel=1e-6
        )
        # With exact input and no method uncertainty, std_dev should be ~0
        assert result_without.std_dev == pytest.approx(0.0, abs=1e-10)
        # With method uncertainty, std_dev should be substantial (~63 kg/m³)
        expected_rho = 91.8 * math.e ** (0.270 * h)
        expected_std = expected_rho * h * 0.2  # rho * h * sigma_B
        assert result_with.std_dev == pytest.approx(expected_std, rel=0.01)

    def test_FC_method_uncertainty_adds_SE(self):
        """Linear SE for FC is 47 kg/m³; with exact inputs, std_dev should equal SE."""
        result = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(2.0, 0.0),
            grain_form="FC",
            include_method_uncertainty=True,
        )
        assert result.std_dev == pytest.approx(47.0, abs=0.01)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_density(
            "kim_jamieson_table2",
            hand_hardness_index=ufloat(1.0, 0.0),
            grain_form="SH",
        )
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# Kim & Jamieson Table 5
# ---------------------------------------------------------------------------

class TestKimJamiesonTable5Numerical:
    """Verify kim_jamieson_table5 density against Table 5 (Table 6 in code) coefficients.

    rho = A*h + B*grain_size + C.
    Coefficients from Kim & Jamieson (2014) Table 5/6.
    """

    def test_FC_multivariate(self):
        """FC: rho = 51.9*h + 19.7*gs + 82.8.  h=2.0, gs=1.0 => 103.8+19.7+82.8=206.3."""
        result = calculate_density(
            "kim_jamieson_table5",
            hand_hardness_index=ufloat(2.0, 0.0),
            grain_form="FC",
            grain_size=ufloat(1.0, 0.0),
            include_method_uncertainty=False,
        )
        expected = 51.9 * 2.0 + 19.7 * 1.0 + 82.8
        assert result.nominal_value == pytest.approx(expected, abs=0.01)

    def test_PP_multivariate(self):
        """PP: rho = 40.0*h + (-7.33)*gs + 52.8.  h=1.0, gs=2.0 => 40-14.66+52.8=78.14."""
        result = calculate_density(
            "kim_jamieson_table5",
            hand_hardness_index=ufloat(1.0, 0.0),
            grain_form="PP",
            grain_size=ufloat(2.0, 0.0),
            include_method_uncertainty=False,
        )
        expected = 40.0 * 1.0 + (-7.33) * 2.0 + 52.8
        assert result.nominal_value == pytest.approx(expected, abs=0.01)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_density(
            "kim_jamieson_table5",
            hand_hardness_index=ufloat(1.0, 0.0),
            grain_form="DH",
            grain_size=ufloat(1.0, 0.0),
        )
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# Unknown method
# ---------------------------------------------------------------------------

class TestUnknownMethod:
    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_density("nonexistent_method", hand_hardness_index=ufloat(1.0, 0.0))
