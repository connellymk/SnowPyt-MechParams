"""Numerical validation tests for shear modulus calculation methods."""

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.methods.layer.shear_modulus import calculate_shear_modulus


class TestLameRelationshipShearModulusNumerical:
    """G = E / (2 * (1 + ν))."""

    def test_exact_inputs(self):
        elastic_modulus = ufloat(12.0, 0.0)
        poissons_ratio = ufloat(0.2, 0.0)
        expected = 12.0 / (2 * (1 + 0.2))
        result = calculate_shear_modulus(
            "lame_relationship",
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio,
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)
        assert result.std_dev == 0.0

    def test_uncertain_inputs(self):
        elastic_modulus = ufloat(18.0, 1.8)
        poissons_ratio = ufloat(0.15, 0.01)
        expected = 18.0 / (2 * (1 + 0.15))
        result = calculate_shear_modulus(
            "lame_relationship",
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio,
            include_method_uncertainty=False,
        )
        assert result.nominal_value == pytest.approx(expected, rel=1e-3)
        assert result.std_dev > 0.0


class TestUnknownShearModulusMethod:
    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_shear_modulus(
                "nonexistent",
                elastic_modulus=ufloat(12.0, 0.0),
                poissons_ratio=ufloat(0.2, 0.0),
            )
