"""Numerical validation tests for Poisson's ratio calculation methods.

Sources:
- Kochle & Schneebeli (2014) — grain-type-specific mean values
- Srivastava et al. (2016) — grain-type-specific mean values
"""

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.layer_parameters.poissons_ratio import calculate_poissons_ratio


# ---------------------------------------------------------------------------
# Kochle
# ---------------------------------------------------------------------------

class TestKochleNumerical:
    """Kochle Poisson's ratio: lookup by grain form.

    RG: 0.171 ± 0.026
    FC: 0.130 ± 0.040
    DH: 0.087 ± 0.063
    """

    def test_RG_nominal(self):
        result = calculate_poissons_ratio("kochle", grain_form="RG")
        assert result.nominal_value == pytest.approx(0.171, abs=1e-6)

    def test_FC_nominal(self):
        result = calculate_poissons_ratio("kochle", grain_form="FC")
        assert result.nominal_value == pytest.approx(0.130, abs=1e-6)

    def test_DH_nominal(self):
        result = calculate_poissons_ratio("kochle", grain_form="DH")
        assert result.nominal_value == pytest.approx(0.087, abs=1e-6)

    def test_RG_uncertainty(self):
        result = calculate_poissons_ratio("kochle", grain_form="RG")
        assert result.std_dev == pytest.approx(0.026, abs=1e-6)

    def test_FC_uncertainty(self):
        result = calculate_poissons_ratio("kochle", grain_form="FC")
        assert result.std_dev == pytest.approx(0.040, abs=1e-6)

    def test_DH_uncertainty(self):
        result = calculate_poissons_ratio("kochle", grain_form="DH")
        assert result.std_dev == pytest.approx(0.063, abs=1e-6)

    def test_subgrain_code_extracts_basic(self):
        """'FCxr' should use the first two chars -> FC."""
        result = calculate_poissons_ratio("kochle", grain_form="FCxr")
        assert result.nominal_value == pytest.approx(0.130, abs=1e-6)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_poissons_ratio("kochle", grain_form="PP")
        assert math.isnan(result.nominal_value)

    def test_no_method_uncertainty(self):
        result = calculate_poissons_ratio(
            "kochle", grain_form="RG", include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(0.171, abs=1e-6)
        assert result.std_dev == 0.0


# ---------------------------------------------------------------------------
# Srivastava
# ---------------------------------------------------------------------------

class TestSrivastavaNumerical:
    """Srivastava Poisson's ratio: lookup by grain form, requires density > 200.

    RG: 0.191 ± 0.008 (density 200-580)
    PP/DF: 0.132 ± 0.053
    FC/DH: 0.17 ± 0.02
    """

    def test_RG_nominal(self):
        result = calculate_poissons_ratio(
            "srivastava", density=ufloat(300.0, 0.0), grain_form="RG",
        )
        assert result.nominal_value == pytest.approx(0.191, abs=1e-6)

    def test_PP_nominal(self):
        result = calculate_poissons_ratio(
            "srivastava", density=ufloat(250.0, 0.0), grain_form="PP",
        )
        assert result.nominal_value == pytest.approx(0.132, abs=1e-6)

    def test_FC_nominal(self):
        result = calculate_poissons_ratio(
            "srivastava", density=ufloat(300.0, 0.0), grain_form="FC",
        )
        assert result.nominal_value == pytest.approx(0.17, abs=1e-6)

    def test_DH_nominal(self):
        result = calculate_poissons_ratio(
            "srivastava", density=ufloat(300.0, 0.0), grain_form="DH",
        )
        assert result.nominal_value == pytest.approx(0.17, abs=1e-6)

    def test_density_below_200_returns_nan(self):
        result = calculate_poissons_ratio(
            "srivastava", density=ufloat(150.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_RG_density_above_580_returns_nan(self):
        result = calculate_poissons_ratio(
            "srivastava", density=ufloat(600.0, 0.0), grain_form="RG",
        )
        assert math.isnan(result.nominal_value)

    def test_unsupported_grain_form_returns_nan(self):
        result = calculate_poissons_ratio(
            "srivastava", density=ufloat(300.0, 0.0), grain_form="MF",
        )
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# Unknown method
# ---------------------------------------------------------------------------

class TestUnknownPoissonsRatioMethod:
    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_poissons_ratio("nonexistent", grain_form="RG")
