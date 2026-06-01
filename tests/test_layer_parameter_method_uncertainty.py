"""
Tests for the include_method_uncertainty parameter on layer parameter functions.

Covers:
- calculate_density (geldsetzer, kim_jamieson_table2, kim_jamieson_table6)
- calculate_elastic_modulus (bergfeld, kochle, wautier, schottner)
- calculate_poissons_ratio (kochle, srivastava)
- calculate_shear_modulus (lame_relationship)

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

from snowpyt_mechparams.methods.layer.density import calculate_density
from snowpyt_mechparams.methods.layer.elastic_modulus import calculate_elastic_modulus
from snowpyt_mechparams.methods.layer.poissons_ratio import calculate_poissons_ratio
from snowpyt_mechparams.methods.layer.shear_modulus import calculate_shear_modulus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Hand hardness index values (from HARDNESS_MAPPING in constants.py)
# "F" -> 1.0, "1F" -> 3.0, with standard uncertainty ±0.67
HHI_F = ufloat(1.0, 0.67)  # Fist
HHI_4F = ufloat(2.0, 0.67)  # Four Fingers
HHI_1F = ufloat(3.0, 0.67)  # One Finger
# Exact (zero uncertainty) variants for isolating method uncertainty
HHI_F_EXACT = ufloat(1.0, 0.0)
HHI_4F_EXACT = ufloat(2.0, 0.0)
HHI_1F_EXACT = ufloat(3.0, 0.0)

# Grain size with standard uncertainty
GS_1MM = ufloat(1.0, 0.5)
GS_1MM_EXACT = ufloat(1.0, 0.0)


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
        result = calculate_density(
            "geldsetzer", hand_hardness_index=HHI_F, grain_form="RG"
        )
        assert _std(result) > 0

    def test_geldsetzer_false_gives_zero_method_uncertainty(self):
        """With include_method_uncertainty=False and exact inputs, std_dev should be zero."""
        result = calculate_density(
            "geldsetzer",
            include_method_uncertainty=False,
            hand_hardness_index=HHI_F_EXACT,
            grain_form="RG",
        )
        assert _std(result) == 0.0

    def test_geldsetzer_nominal_value_unchanged(self):
        """Nominal value must be the same regardless of the flag."""
        on = calculate_density("geldsetzer", hand_hardness_index=HHI_F, grain_form="RG")
        off = calculate_density(
            "geldsetzer",
            include_method_uncertainty=False,
            hand_hardness_index=HHI_F,
            grain_form="RG",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_geldsetzer_true_explicit_matches_default(self):
        """Passing True explicitly should give the same result as the default."""
        default = calculate_density(
            "geldsetzer", hand_hardness_index=HHI_1F, grain_form="FC"
        )
        explicit = calculate_density(
            "geldsetzer",
            include_method_uncertainty=True,
            hand_hardness_index=HHI_1F,
            grain_form="FC",
        )
        assert _nominal(default) == pytest.approx(_nominal(explicit))
        assert _std(default) == pytest.approx(_std(explicit))

    # --- kim_jamieson_table2 ---

    def test_kim_jamieson_table2_false_gives_zero_method_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table2",
            include_method_uncertainty=False,
            hand_hardness_index=HHI_4F_EXACT,
            grain_form="FC",
        )
        assert _std(result) == 0.0

    def test_kim_jamieson_table2_nominal_value_unchanged(self):
        on = calculate_density(
            "kim_jamieson_table2", hand_hardness_index=HHI_4F, grain_form="FC"
        )
        off = calculate_density(
            "kim_jamieson_table2",
            include_method_uncertainty=False,
            hand_hardness_index=HHI_4F,
            grain_form="FC",
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_kim_jamieson_table2_true_has_nonzero_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table2", hand_hardness_index=HHI_4F, grain_form="FC"
        )
        assert _std(result) > 0

    # --- kim_jamieson_table6 ---

    def test_kim_jamieson_table6_false_gives_zero_method_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table6",
            include_method_uncertainty=False,
            hand_hardness_index=HHI_4F_EXACT,
            grain_form="FC",
            grain_size=GS_1MM_EXACT,
        )
        assert _std(result) == 0.0

    def test_kim_jamieson_table6_nominal_value_unchanged(self):
        on = calculate_density(
            "kim_jamieson_table6",
            hand_hardness_index=HHI_4F,
            grain_form="FC",
            grain_size=GS_1MM,
        )
        off = calculate_density(
            "kim_jamieson_table6",
            include_method_uncertainty=False,
            hand_hardness_index=HHI_4F,
            grain_form="FC",
            grain_size=GS_1MM,
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_kim_jamieson_table6_true_has_nonzero_uncertainty(self):
        result = calculate_density(
            "kim_jamieson_table6",
            hand_hardness_index=HHI_4F,
            grain_form="FC",
            grain_size=GS_1MM,
        )
        assert _std(result) > 0

    def test_kim_jamieson_table5_legacy_alias_matches_table6(self):
        canonical = calculate_density(
            "kim_jamieson_table6",
            hand_hardness_index=HHI_4F,
            grain_form="FC",
            grain_size=GS_1MM,
        )
        legacy = calculate_density(
            "kim_jamieson_table5",
            hand_hardness_index=HHI_4F,
            grain_form="FC",
            grain_size=GS_1MM,
        )
        assert _nominal(legacy) == pytest.approx(_nominal(canonical))
        assert _std(legacy) == pytest.approx(_std(canonical))


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
        on = calculate_elastic_modulus("wautier", density=self._rho, grain_form="RG")
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
        on = calculate_elastic_modulus("schottner", density=self._rho, grain_form="RG")
        off = calculate_elastic_modulus(
            "schottner",
            include_method_uncertainty=False,
            density=self._rho,
            grain_form="RG",
        )
        assert _std(on) > _std(off)

    def test_schottner_nominal_value_unchanged(self):
        on = calculate_elastic_modulus("schottner", density=self._rho, grain_form="RG")
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
        result = calculate_poissons_ratio("srivastava", density=rho, grain_form="RG")
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

    # --- lame_relationship ---

    def test_lame_relationship_nominal_value_unchanged(self):
        """Method flag should not change the Lamé relationship nominal value."""
        elastic_modulus = ufloat(12.0, 1.0)
        poissons_ratio = ufloat(0.2, 0.01)
        on = calculate_shear_modulus(
            "lame_relationship",
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio,
        )
        off = calculate_shear_modulus(
            "lame_relationship",
            include_method_uncertainty=False,
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio,
        )
        assert _nominal(on) == pytest.approx(_nominal(off))

    def test_lame_relationship_false_still_propagates_input_uncertainty(self):
        """Even with method uncertainty off, E/ν uncertainty propagates."""
        elastic_modulus_uncertain = ufloat(18.0, 1.8)
        elastic_modulus_exact = ufloat(18.0, 0.0)
        poissons_ratio = ufloat(0.15, 0.0)

        with_unc = calculate_shear_modulus(
            "lame_relationship",
            include_method_uncertainty=False,
            elastic_modulus=elastic_modulus_uncertain,
            poissons_ratio=poissons_ratio,
        )
        without_unc = calculate_shear_modulus(
            "lame_relationship",
            include_method_uncertainty=False,
            elastic_modulus=elastic_modulus_exact,
            poissons_ratio=poissons_ratio,
        )
        assert _std(with_unc) > _std(without_unc)

    def test_lame_relationship_poissons_ratio_uncertainty_is_input_uncertainty(self):
        """Poisson's ratio uncertainty is an input, not method uncertainty."""
        elastic_modulus = ufloat(18.0, 0.0)
        poissons_ratio_uncertain = ufloat(0.15, 0.02)
        poissons_ratio_exact = ufloat(0.15, 0.0)

        with_nu_unc = calculate_shear_modulus(
            "lame_relationship",
            include_method_uncertainty=False,
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio_uncertain,
        )
        without_nu_unc = calculate_shear_modulus(
            "lame_relationship",
            include_method_uncertainty=False,
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio_exact,
        )
        assert _std(with_nu_unc) > _std(without_nu_unc)

    def test_lame_relationship_true_explicit_matches_default(self):
        elastic_modulus = ufloat(18.0, 1.0)
        poissons_ratio = ufloat(0.17, 0.01)
        default = calculate_shear_modulus(
            "lame_relationship",
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio,
        )
        explicit = calculate_shear_modulus(
            "lame_relationship",
            include_method_uncertainty=True,
            elastic_modulus=elastic_modulus,
            poissons_ratio=poissons_ratio,
        )
        assert _nominal(default) == pytest.approx(_nominal(explicit))
        assert _std(default) == pytest.approx(_std(explicit))
