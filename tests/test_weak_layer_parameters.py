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


# ---------------------------------------------------------------------------
# Numerical correctness: sigrist and mellor
# ---------------------------------------------------------------------------

class TestSigristNumerical:
    """Verify σ_c+ = 240 * (ρ/ρ_ice)^2.44 against hand-computed values."""

    _RHO_ICE = 917.0

    def test_sigrist_300_kg_m3(self):
        density = ufloat(300.0, 0.0)
        result = calculate_sigma_c_plus("sigrist", density=density)
        expected = 240.0 * (300.0 / self._RHO_ICE) ** 2.44
        assert _nominal(result) == pytest.approx(expected, rel=1e-5)

    def test_sigrist_100_kg_m3(self):
        density = ufloat(100.0, 0.0)
        result = calculate_sigma_c_plus("sigrist", density=density)
        expected = 240.0 * (100.0 / self._RHO_ICE) ** 2.44
        assert _nominal(result) == pytest.approx(expected, rel=1e-5)

    def test_sigrist_uncertainty_propagates(self):
        """Non-zero density uncertainty should produce non-zero output uncertainty."""
        density = ufloat(300.0, 15.0)
        result = calculate_sigma_c_plus("sigrist", density=density)
        assert _std(result) > 0.0

    def test_sigrist_zero_std_for_zero_density_std(self):
        """Zero density uncertainty → zero output uncertainty."""
        density = ufloat(300.0, 0.0)
        result = calculate_sigma_c_plus("sigrist", density=density)
        assert _std(result) == pytest.approx(0.0, abs=1e-12)

    def test_sigrist_increases_with_density(self):
        """Higher density → higher tensile strength."""
        r_low  = calculate_sigma_c_plus("sigrist", density=ufloat(150.0, 0.0))
        r_high = calculate_sigma_c_plus("sigrist", density=ufloat(400.0, 0.0))
        assert _nominal(r_low) < _nominal(r_high)


class TestMellorNumerical:
    """Verify σ_c- = 5000 * (ρ/ρ_ice)^2.5 against hand-computed values."""

    _RHO_ICE = 917.0

    def test_mellor_300_kg_m3(self):
        density = ufloat(300.0, 0.0)
        result = calculate_sigma_c_minus("mellor", density=density)
        expected = 5000.0 * (300.0 / self._RHO_ICE) ** 2.5
        assert _nominal(result) == pytest.approx(expected, rel=1e-5)

    def test_mellor_200_kg_m3(self):
        density = ufloat(200.0, 0.0)
        result = calculate_sigma_c_minus("mellor", density=density)
        expected = 5000.0 * (200.0 / self._RHO_ICE) ** 2.5
        assert _nominal(result) == pytest.approx(expected, rel=1e-5)

    def test_mellor_uncertainty_propagates(self):
        """Non-zero density uncertainty should produce non-zero output uncertainty."""
        density = ufloat(300.0, 15.0)
        result = calculate_sigma_c_minus("mellor", density=density)
        assert _std(result) > 0.0

    def test_mellor_increases_with_density(self):
        """Higher density → higher compressive strength."""
        r_low  = calculate_sigma_c_minus("mellor", density=ufloat(150.0, 0.0))
        r_high = calculate_sigma_c_minus("mellor", density=ufloat(400.0, 0.0))
        assert _nominal(r_low) < _nominal(r_high)


# ---------------------------------------------------------------------------
# Graph integration: sigrist and mellor reachable via find_parameterizations
# ---------------------------------------------------------------------------

class TestSigristMellorGraphIntegration:
    """Verify sigrist and mellor appear as selectable methods in g_delta pathways."""

    @staticmethod
    def _all_edge_names(parameterization):
        """Return the set of all method edge names in a parameterization.

        merge_points is a list of tuples: (branch_indices, merge_node_name, continuation_segments).
        """
        names = set()
        for branch in parameterization.branches:
            for seg in branch.segments:
                if seg.edge_name and seg.edge_name != "data_flow":
                    names.add(seg.edge_name)
        for mp in parameterization.merge_points:
            # mp is (branch_indices, merge_node_name, continuation_segments)
            for seg in mp[2]:
                if seg.edge_name and seg.edge_name != "data_flow":
                    names.add(seg.edge_name)
        return names

    def test_sigrist_appears_in_g_delta_pathways(self):
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.graph.parameter_graph import graph, g_delta

        pathways = find_parameterizations(graph, g_delta)
        has_sigrist = any("sigrist" in self._all_edge_names(p) for p in pathways)
        assert has_sigrist, "No g_delta pathway uses the sigrist method for sigma_c"

    def test_mellor_appears_in_g_delta_pathways(self):
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.graph.parameter_graph import graph, g_delta

        pathways = find_parameterizations(graph, g_delta)
        has_mellor = any("mellor" in self._all_edge_names(p) for p in pathways)
        assert has_mellor, "No g_delta pathway uses the mellor method for sigma_comp"

    def test_g_delta_pathway_count(self):
        """g_delta pathway count after adding sigrist/mellor: 4×4×2×13 = 416."""
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.graph.parameter_graph import graph, g_delta

        pathways = find_parameterizations(graph, g_delta)
        assert len(pathways) == 416

    def test_s_r_pathway_count_unchanged(self):
        """Roch natural pathway count is unaffected by sigrist/mellor (tau_c still constant)."""
        from snowpyt_mechparams.algorithm import find_parameterizations
        from snowpyt_mechparams.graph.parameter_graph import graph, s_r

        pathways = find_parameterizations(graph, s_r)
        assert len(pathways) == 4
