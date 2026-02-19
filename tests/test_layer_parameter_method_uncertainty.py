"""
Tests for the include_method_uncertainty parameter on layer parameter functions.

Covers:
- calculate_density (geldsetzer, kim_jamieson_table2, kim_jamieson_table5)
- calculate_elastic_modulus (bergfeld, kochle, wautier, schottner)
- calculate_poissons_ratio (kochle, srivastava)
- calculate_shear_modulus (wautier)

For each method the tests verify:
1. Default behaviour is unchanged (include_method_uncertainty=True)
2. Nominal value is the same regardless of the flag
3. When False, the method contributes zero uncertainty
4. When True, the method contributes non-zero uncertainty
5. Input uncertainties still propagate when the flag is False
"""

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.layer_parameters.density import calculate_density
from snowpyt_mechparams.layer_parameters.elastic_modulus import calculate_elastic_modulus
from snowpyt_mechparams.layer_parameters.poissons_ratio import calculate_poissons_ratio
from snowpyt_mechparams.layer_parameters.shear_modulus import calculate_shear_modulus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nominal(x):
    """Return nominal value regardless of whether x is a ufloat or float."""
    return x.nominal_value if hasattr(x, "nominal_value") else float(x)


def _std(x):
    """Return std_dev regardless of whether x is a ufloat or float."""
    return x.std_dev if hasattr(x, "std_dev") else 0.0


# ---------------------------------------------------------------------------
# Density
# ---------------------------------------------------------------------------

class TestDensityMethodUncertainty:
    """Tests for include_method_uncertainty in calculate_density."""

    # --- geldsetzer ---

    def test_geldsetzer_default_includes_method_uncertainty(self):
        """Default call should include the regression SE as uncertainty."""
        result = calculate_density("geldsetzer", hand_hardness="F", grain_form="RG")
        assert _std(result) > 0

    def test_geldsetzer_false_gives_zero_method_uncertainty(self):
        """With include_method_uncertainty=False, std_dev should be zero."""
        result = calculate_density(
            "geldsetzer",
            include_method_uncertainty=False,
            hand_hardness="F",
            grain_form="RG",
        )
        assert _std(result) == 0.0

    def test_geldsetzer_nominal_value_unchanged(self):
        """Nominal value must be the same regardless of the flag."""
        on = calculate_density("geldsetzer", hand_hardness="F", grain_form="RG")
        off = calculate_density(
            "geldsetzer",
            include_method_uncertainty=False,
            hand_hardness="F",
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_geldsetzer_true_explicit_matches_default(self):
        """Passing True explicitly should give the same result as the default."""
        default = calculate_density("geldsetzer", hand_hardness="1F", grain_form="FC")
        explicit = calculate_density(
            "geldsetzer",
            include_method_uncertainty=True,
            hand_hardness="1F",
            grain_form="FC",
        )
        assert _nominal(default) == pytest.approx(_nominal(explicit))
        assert _std(default) == pytest.approx(_std(explicit))

    # --- kim_jamieson_table2 ---

    def test_kim_jamieson_table2_false_gives_zero_method_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table2",
            include_method_uncertainty=False,
            hand_hardness="F",
            grain_form="FC",
        )
        assert _std(result) == 0.0

    def test_kim_jamieson_table2_nominal_value_unchanged(self):
        on = calculate_density(
            "kim_jamieson_table2", hand_hardness="F", grain_form="FC"
        )
        off = calculate_density(
            "kim_jamieson_table2",
            include_method_uncertainty=False,
            hand_hardness="F",
            grain_form="FC",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_kim_jamieson_table2_true_has_nonzero_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table2", hand_hardness="F", grain_form="FC"
        )
        assert _std(result) > 0

    # --- kim_jamieson_table5 ---

    def test_kim_jamieson_table5_false_gives_zero_method_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table5",
            include_method_uncertainty=False,
            hand_hardness="F",
            grain_form="FC",
            grain_size=1.0,
        )
        assert _std(result) == 0.0

    def test_kim_jamieson_table5_nominal_value_unchanged(self):
        on = calculate_density(
            "kim_jamieson_table5",
            hand_hardness="F",
            grain_form="FC",
            grain_size=1.0,
        )
        off = calculate_density(
            "kim_jamieson_table5",
            include_method_uncertainty=False,
            hand_hardness="F",
            grain_form="FC",
            grain_size=1.0,
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_kim_jamieson_table5_true_has_nonzero_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table5",
            hand_hardness="F",
            grain_form="FC",
            grain_size=1.0,
        )
        assert _std(result) > 0


# ---------------------------------------------------------------------------
# Elastic modulus
# ---------------------------------------------------------------------------

class TestElasticModulusMethodUncertainty:
    """Tests for include_method_uncertainty in calculate_elastic_modulus."""

    # Density with uncertainty used as input for most methods
    _rho = ufloat(250.0, 10.0)

    # --- bergfeld ---

    def test_bergfeld_false_reduces_uncertainty(self):
        """Removing fitted-exponent uncertainty should reduce total std_dev."""
        on = calculate_elastic_modulus("bergfeld", density=self._rho, grain_form="RG")
        off = calculate_elastic_modulus(
            "bergfeld",
            include_method_uncertainty=False,
            density=self._rho,
            grain_form="RG",
        )
        assert _std(on) > _std(off)

    def test_bergfeld_nominal_value_unchanged(self):
        on = calculate_elastic_modulus("bergfeld", density=self._rho, grain_form="RG")
        off = calculate_elastic_modulus(
            "bergfeld",
            include_method_uncertainty=False,
            density=self._rho,
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_bergfeld_default_has_nonzero_uncertainty(self):
        result = calculate_elastic_modulus(
            "bergfeld", density=self._rho, grain_form="RG"
        )
        assert _std(result) > 0

    def test_bergfeld_false_still_propagates_input_uncertainty(self):
        """Even with method uncertainty off, density uncertainty propagates."""
        rho_uncertain = ufloat(250.0, 20.0)
        rho_exact = ufloat(250.0, 0.0)

        with_input_unc = calculate_elastic_modulus(
            "bergfeld",
            include_method_uncertainty=False,
            density=rho_uncertain,
            grain_form="RG",
        )
        without_input_unc = calculate_elastic_modulus(
            "bergfeld",
            include_method_uncertainty=False,
            density=rho_exact,
            grain_form="RG",
        )
        assert _std(with_input_unc) > _std(without_input_unc)

    # --- kochle ---

    def test_kochle_nominal_value_unchanged(self):
        """kochle has no stated coefficient uncertainty; nominal must still match."""
        rho = ufloat(300.0, 10.0)
        on = calculate_elastic_modulus("kochle", density=rho, grain_form="RG")
        off = calculate_elastic_modulus(
            "kochle",
            include_method_uncertainty=False,
            density=rho,
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_kochle_false_still_propagates_input_uncertainty(self):
        rho_uncertain = ufloat(300.0, 20.0)
        rho_exact = ufloat(300.0, 0.0)

        with_unc = calculate_elastic_modulus(
            "kochle",
            include_method_uncertainty=False,
            density=rho_uncertain,
            grain_form="RG",
        )
        without_unc = calculate_elastic_modulus(
            "kochle",
            include_method_uncertainty=False,
            density=rho_exact,
            grain_form="RG",
        )
        assert _std(with_unc) > _std(without_unc)

    # --- wautier ---

    def test_wautier_nominal_value_unchanged(self):
        """wautier A/n have zero uncertainty; nominal must match."""
        on = calculate_elastic_modulus(
            "wautier", density=self._rho, grain_form="RG"
        )
        off = calculate_elastic_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=self._rho,
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_wautier_false_still_propagates_input_uncertainty(self):
        rho_uncertain = ufloat(250.0, 25.0)
        rho_exact = ufloat(250.0, 0.0)

        with_unc = calculate_elastic_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=rho_uncertain,
            grain_form="RG",
        )
        without_unc = calculate_elastic_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=rho_exact,
            grain_form="RG",
        )
        assert _std(with_unc) > _std(without_unc)

    # --- schottner ---

    def test_schottner_false_reduces_uncertainty(self):
        """Removing A/n coefficient uncertainties should reduce total std_dev."""
        on = calculate_elastic_modulus(
            "schottner", density=self._rho, grain_form="RG"
        )
        off = calculate_elastic_modulus(
            "schottner",
            include_method_uncertainty=False,
            density=self._rho,
            grain_form="RG",
        )
        assert _std(on) > _std(off)

    def test_schottner_nominal_value_unchanged(self):
        on = calculate_elastic_modulus(
            "schottner", density=self._rho, grain_form="RG"
        )
        off = calculate_elastic_modulus(
            "schottner",
            include_method_uncertainty=False,
            density=self._rho,
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    @pytest.mark.parametrize("grain_form", ["RG", "FC", "DH", "SH"])
    def test_schottner_all_grain_types_nominal_unchanged(self, grain_form):
        """Nominal value must be consistent across all grain types."""
        rho = ufloat(250.0, 10.0)
        on = calculate_elastic_modulus("schottner", density=rho, grain_form=grain_form)
        off = calculate_elastic_modulus(
            "schottner",
            include_method_uncertainty=False,
            density=rho,
            grain_form=grain_form,
        )
        if not math.isnan(_nominal(on)):
            assert _nominal(on) == pytest.approx(_nominal(off))

    def test_schottner_false_still_propagates_input_uncertainty(self):
        rho_uncertain = ufloat(250.0, 25.0)
        rho_exact = ufloat(250.0, 0.0)

        with_unc = calculate_elastic_modulus(
            "schottner",
            include_method_uncertainty=False,
            density=rho_uncertain,
            grain_form="RG",
        )
        without_unc = calculate_elastic_modulus(
            "schottner",
            include_method_uncertainty=False,
            density=rho_exact,
            grain_form="RG",
        )
        assert _std(with_unc) > _std(without_unc)


# ---------------------------------------------------------------------------
# Poisson's ratio
# ---------------------------------------------------------------------------

class TestPoissonsRatioMethodUncertainty:
    """Tests for include_method_uncertainty in calculate_poissons_ratio."""

    # --- kochle ---

    def test_kochle_false_gives_zero_method_uncertainty(self):
        result = calculate_poissons_ratio(
            "kochle", include_method_uncertainty=False, grain_form="RG"
        )
        assert _std(result) == 0.0

    def test_kochle_true_has_nonzero_uncertainty(self):
        result = calculate_poissons_ratio("kochle", grain_form="RG")
        assert _std(result) > 0

    def test_kochle_nominal_value_unchanged(self):
        on = calculate_poissons_ratio("kochle", grain_form="RG")
        off = calculate_poissons_ratio(
            "kochle", include_method_uncertainty=False, grain_form="RG"
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    @pytest.mark.parametrize("grain_form", ["RG", "FC", "DH"])
    def test_kochle_all_grain_forms_nominal_unchanged(self, grain_form):
        on = calculate_poissons_ratio("kochle", grain_form=grain_form)
        off = calculate_poissons_ratio(
            "kochle", include_method_uncertainty=False, grain_form=grain_form
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    @pytest.mark.parametrize("grain_form", ["RG", "FC", "DH"])
    def test_kochle_all_grain_forms_false_gives_zero_std(self, grain_form):
        result = calculate_poissons_ratio(
            "kochle", include_method_uncertainty=False, grain_form=grain_form
        )
        assert _std(result) == 0.0

    # --- srivastava ---

    def test_srivastava_false_gives_zero_method_uncertainty(self):
        rho = ufloat(300.0, 0.0)  # exact density - any std_dev would be from method
        result = calculate_poissons_ratio(
            "srivastava",
            include_method_uncertainty=False,
            density=rho,
            grain_form="RG",
        )
        assert _std(result) == 0.0

    def test_srivastava_true_has_nonzero_uncertainty(self):
        rho = ufloat(300.0, 10.0)
        result = calculate_poissons_ratio(
            "srivastava", density=rho, grain_form="RG"
        )
        assert _std(result) > 0

    def test_srivastava_nominal_value_unchanged(self):
        rho = ufloat(300.0, 10.0)
        on = calculate_poissons_ratio("srivastava", density=rho, grain_form="RG")
        off = calculate_poissons_ratio(
            "srivastava",
            include_method_uncertainty=False,
            density=rho,
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    @pytest.mark.parametrize("grain_form", ["RG", "PP", "DF", "FC", "DH"])
    def test_srivastava_all_grain_forms_nominal_unchanged(self, grain_form):
        rho = ufloat(300.0, 10.0)
        on = calculate_poissons_ratio("srivastava", density=rho, grain_form=grain_form)
        off = calculate_poissons_ratio(
            "srivastava",
            include_method_uncertainty=False,
            density=rho,
            grain_form=grain_form,
        )
        if not math.isnan(_nominal(on)):
            assert _nominal(on) == pytest.approx(_nominal(off))

    @pytest.mark.parametrize("grain_form", ["PP", "DF", "FC", "DH"])
    def test_srivastava_all_grain_forms_false_gives_zero_std(self, grain_form):
        rho = ufloat(300.0, 0.0)
        result = calculate_poissons_ratio(
            "srivastava",
            include_method_uncertainty=False,
            density=rho,
            grain_form=grain_form,
        )
        assert _std(result) == 0.0


# ---------------------------------------------------------------------------
# Shear modulus
# ---------------------------------------------------------------------------

class TestShearModulusMethodUncertainty:
    """Tests for include_method_uncertainty in calculate_shear_modulus."""

    # --- wautier ---

    def test_wautier_nominal_value_unchanged(self):
        """wautier A/n have zero uncertainty; nominal must be consistent."""
        rho = ufloat(300.0, 10.0)
        on = calculate_shear_modulus("wautier", density=rho, grain_form="RG")
        off = calculate_shear_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=rho,
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_wautier_false_still_propagates_input_uncertainty(self):
        """Even with method uncertainty off, density uncertainty propagates."""
        rho_uncertain = ufloat(300.0, 30.0)
        rho_exact = ufloat(300.0, 0.0)

        with_unc = calculate_shear_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=rho_uncertain,
            grain_form="RG",
        )
        without_unc = calculate_shear_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=rho_exact,
            grain_form="RG",
        )
        assert _std(with_unc) > _std(without_unc)

    def test_wautier_custom_G_ice_uncertainty_is_not_method_uncertainty(self):
        """G_ice uncertainty is an input parameter, not a method choice.
        Passing include_method_uncertainty=False should NOT zero G_ice's std_dev."""
        rho = ufloat(300.0, 0.0)
        G_ice_uncertain = ufloat(407.7, 65.4)
        G_ice_exact = ufloat(407.7, 0.0)

        with_G_ice_unc = calculate_shear_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=rho,
            grain_form="RG",
            G_ice=G_ice_uncertain,
        )
        without_G_ice_unc = calculate_shear_modulus(
            "wautier",
            include_method_uncertainty=False,
            density=rho,
            grain_form="RG",
            G_ice=G_ice_exact,
        )
        assert _std(with_G_ice_unc) > _std(without_G_ice_unc)

    def test_wautier_true_explicit_matches_default(self):
        rho = ufloat(300.0, 10.0)
        default = calculate_shear_modulus("wautier", density=rho, grain_form="FC")
        explicit = calculate_shear_modulus(
            "wautier",
            include_method_uncertainty=True,
            density=rho,
            grain_form="FC",
        )
        assert _nominal(default) == pytest.approx(_nominal(explicit))
        assert _std(default) == pytest.approx(_std(explicit))
