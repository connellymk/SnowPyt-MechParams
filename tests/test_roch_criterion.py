"""
Tests for the Roch stability criterion.

Unit tests cover:
- calculate_shear_stress(): formula correctness, edge cases, UFloat propagation
- calculate_roch(): natural and skier variants, None-return conditions, result fields

tau_c is passed in kPa (matching WeakLayer.tau_c units). calculate_roch converts
to Pa internally, so RochResult.tau_c is stored in Pa.
"""

from __future__ import annotations

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.constants import (
    g,
    STANDARD_SKIER_MASS_KG,
    STANDARD_SKI_CONTACT_AREA_M2,
)
from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.models.weak_layer import WeakLayer
from snowpyt_mechparams.stability_criteria.roch.roch_criterion import calculate_roch
from snowpyt_mechparams.stability_criteria.roch.roch_result import RochResult
from snowpyt_mechparams.stability_criteria.roch.shear_stress import calculate_shear_stress

# Standard skier shear stress (Pa) — mirrors _ROCH_SKIER_STRESS_N_M2 in dispatcher.
# 80 kg × 9.81 m/s² / 0.65 m² ≈ 1207.4 N/m²
_SKIER_STRESS = STANDARD_SKIER_MASS_KG * g / STANDARD_SKI_CONTACT_AREA_M2

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_G = g


def _make_slab(
    angle: float,
    layers: list[tuple[float, float]],  # (thickness_cm, density_kg_m3) per layer
    missing_density_idx: int | None = None,
    missing_thickness_idx: int | None = None,
) -> Slab:
    """
    Build a minimal ``Slab`` for testing the Roch criterion.

    Parameters
    ----------
    angle : float
        Slope angle in degrees.
    layers : list of (thickness_cm, density_kg_m3)
        Each tuple defines one slab layer.
    missing_density_idx : int, optional
        If set, sets ``density_calculated=None`` on that layer index.
    missing_thickness_idx : int, optional
        If set, sets ``thickness=None`` on that layer index.
    """
    layer_objs = []
    for i, (h, rho) in enumerate(layers):
        thickness = None if i == missing_thickness_idx else ufloat(h, 0.0)
        density = None if i == missing_density_idx else ufloat(rho, 0.0)
        layer_objs.append(Layer(thickness=thickness, density_calculated=density))
    return Slab(layers=layer_objs, angle=angle)


# ---------------------------------------------------------------------------
# calculate_shear_stress
# ---------------------------------------------------------------------------


class TestCalculateShearStress:
    """Tests for the gravitational shear stress formula τ = Σρᵢhᵢg·sinθ."""

    def test_single_layer_known_value(self):
        """ρ=300 kg/m³, h=50 cm, θ=38° → τ ≈ 905.9 N/m²."""
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)])
        tau = calculate_shear_stress(slab)
        expected = 300.0 * 0.5 * _G * math.sin(math.radians(38.0))
        assert tau.nominal_value == pytest.approx(expected, rel=1e-5)

    def test_multi_layer_sum(self):
        """τ should equal the sum of each layer's contribution."""
        slab = _make_slab(angle=38.0, layers=[(30.0, 300.0), (20.0, 250.0)])
        tau = calculate_shear_stress(slab)
        expected = (300.0 * 0.30 + 250.0 * 0.20) * _G * math.sin(math.radians(38.0))
        assert tau.nominal_value == pytest.approx(expected, rel=1e-5)

    def test_flat_terrain_returns_zero(self):
        """θ=0° → sinθ=0 → τ=0."""
        slab = _make_slab(angle=0.0, layers=[(50.0, 300.0)])
        tau = calculate_shear_stress(slab)
        assert tau.nominal_value == pytest.approx(0.0, abs=1e-10)

    def test_missing_thickness_returns_none(self):
        """A layer with thickness=None → returns None."""
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)], missing_thickness_idx=0)
        tau = calculate_shear_stress(slab)
        assert tau is None

    def test_missing_density_calculated_returns_none(self):
        """A layer with density_calculated=None → returns None."""
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)], missing_density_idx=0)
        tau = calculate_shear_stress(slab)
        assert tau is None

    def test_ufloat_inputs_propagate_uncertainty(self):
        """UFloat inputs produce a UFloat result with non-zero uncertainty."""
        layer = Layer(
            thickness=ufloat(50.0, 2.0),
            density_calculated=ufloat(300.0, 15.0),
        )
        slab = Slab(layers=[layer], angle=ufloat(38.0, 1.0))
        tau = calculate_shear_stress(slab)
        assert hasattr(tau, "std_dev")
        assert tau.std_dev > 0


# ---------------------------------------------------------------------------
# calculate_roch
# ---------------------------------------------------------------------------


class TestCalculateRochNoneConditions:
    """Cases where calculate_roch must return None."""

    def test_returns_none_when_layer_missing_density(self):
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)], missing_density_idx=0)
        assert calculate_roch(slab, tau_c=ufloat(1.5, 0.0)) is None

    def test_natural_returns_none_flat_terrain(self):
        """τ=0 (θ=0°) is undefined for the natural criterion."""
        slab = _make_slab(angle=0.0, layers=[(50.0, 300.0)])
        assert calculate_roch(slab, tau_c=ufloat(1.5, 0.0)) is None

    def test_natural_returns_none_negative_angle(self):
        """τ<0 (counter-slope) is physically meaningless; must return None."""
        slab = _make_slab(angle=-5.0, layers=[(50.0, 300.0)])
        assert calculate_roch(slab, tau_c=ufloat(1.5, 0.0)) is None

    def test_skier_returns_none_zero_skier_stress(self):
        """τ_sk=0 makes the skier criterion undefined."""
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)])
        assert calculate_roch(slab, tau_c=ufloat(1.5, 0.0), skier_stress=0.0) is None


class TestCalculateRochNaturalVariant:
    """Numerical correctness and result fields for the natural (S_r) criterion."""

    def setup_method(self):
        self.slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)])
        self.tau_c = ufloat(1.5, 0.0)          # 1.5 kPa = 1500 Pa
        self.expected_tau = 300.0 * 0.5 * _G * math.sin(math.radians(38.0))  # Pa
        self.expected_sr = 1500.0 / self.expected_tau  # tau_c in Pa after conversion

    def test_correct_sr_value(self):
        """S_r = τ_c / τ should match hand-computed value."""
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert result is not None
        assert result.stability_index.nominal_value == pytest.approx(self.expected_sr, rel=1e-4)

    def test_variant_is_natural(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert result is not None
        assert result.variant == "natural"

    def test_skier_stress_is_none(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert result is not None
        assert result.skier_stress is None

    def test_shear_stress_stored_in_result(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert result is not None
        assert result.shear_stress.nominal_value == pytest.approx(self.expected_tau, rel=1e-5)

    def test_tau_c_stored_in_result_as_pa(self):
        """RochResult.tau_c is stored in Pa (converted from 1.5 kPa input)."""
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert result is not None
        assert result.tau_c.nominal_value == pytest.approx(1500.0)  # 1.5 kPa → 1500 Pa

    def test_returns_roch_result_instance(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert isinstance(result, RochResult)

    def test_stability_index_below_one_when_unstable(self):
        """τ_c < τ → S_r < 1 (unstable)."""
        tau_c_small = ufloat(0.5, 0.0)  # 0.5 kPa = 500 Pa — much less than expected_tau ≈ 906 N/m²
        result = calculate_roch(self.slab, tau_c=tau_c_small)
        assert result is not None
        assert result.stability_index.nominal_value < 1.0

    def test_ufloat_tau_c_propagates_uncertainty(self):
        """Uncertainty in τ_c should propagate to stability_index."""
        tau_c_with_unc = ufloat(1.5, 0.05)  # 1.5 kPa ± 0.05 kPa
        result = calculate_roch(self.slab, tau_c=tau_c_with_unc)
        assert result is not None
        assert hasattr(result.stability_index, "std_dev")
        assert result.stability_index.std_dev > 0


class TestCalculateRochSkierVariant:
    """Numerical correctness and result fields for the skier (S_sk) criterion."""

    def setup_method(self):
        self.slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)])
        self.tau_c = ufloat(1.5, 0.0)               # 1.5 kPa = 1500 Pa
        self.tau_sk = ufloat(_SKIER_STRESS, 0.0)    # 80 kg × g / 0.65 m² ≈ 1207.4 N/m²
        self.expected_tau = 300.0 * 0.5 * _G * math.sin(math.radians(38.0))  # Pa
        self.expected_ssk = 1500.0 / (self.expected_tau + _SKIER_STRESS)

    def test_correct_ssk_value(self):
        """S_a = τ_c / (τ + δτ) should match hand-computed value."""
        result = calculate_roch(self.slab, tau_c=self.tau_c, skier_stress=self.tau_sk)
        assert result is not None
        assert result.stability_index.nominal_value == pytest.approx(self.expected_ssk, rel=1e-4)

    def test_variant_is_skier(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c, skier_stress=self.tau_sk)
        assert result is not None
        assert result.variant == "skier"

    def test_skier_stress_stored_in_result(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c, skier_stress=self.tau_sk)
        assert result is not None
        assert result.skier_stress.nominal_value == pytest.approx(_SKIER_STRESS)

    def test_flat_terrain_is_valid_for_skier(self):
        """θ=0° (τ=0) is valid for the skier criterion; only τ_sk=0 is forbidden."""
        slab_flat = _make_slab(angle=0.0, layers=[(50.0, 300.0)])
        result = calculate_roch(slab_flat, tau_c=self.tau_c, skier_stress=self.tau_sk)
        assert result is not None
        assert result.variant == "skier"
        # τ=0, so S_a = tau_c_pa / (0 + tau_sk) = 1500 / _SKIER_STRESS
        assert result.stability_index.nominal_value == pytest.approx(
            1500.0 / _SKIER_STRESS, rel=1e-4
        )

    def test_stability_index_below_one_when_slope_stress_exceeds_strength(self):
        """τ_c < τ → S_a < 1 (slope stress alone exceeds weak layer strength).

        S_a = τ_c / (τ + δτ) is always ≥ 0; instability is indicated by S_a < 1.
        τ ≈ 400×0.80×9.81×sin(50°) ≈ 2413 N/m² >> tau_c = 0.5 kPa = 500 Pa.
        """
        steep_slab = _make_slab(angle=50.0, layers=[(80.0, 400.0)])
        tau_c_tiny = ufloat(0.5, 0.0)  # 0.5 kPa = 500 Pa
        result = calculate_roch(steep_slab, tau_c=tau_c_tiny, skier_stress=self.tau_sk)
        assert result is not None
        assert result.stability_index.nominal_value < 1.0


# ---------------------------------------------------------------------------
# Engine integration tests
# ---------------------------------------------------------------------------


class TestRochEngineIntegration:
    """Full-stack tests: ExecutionEngine → PathwayExecutor → dispatcher → calculate_roch.

    These tests verify the complete pathway from raw pit inputs (hand hardness,
    grain form) through density estimation and tau_c assignment to the stored
    ``RochResult`` on the output slab.  They complement the unit tests above,
    which test ``calculate_roch`` and ``calculate_shear_stress`` in isolation.
    """

    def _make_engine_slab(self) -> Slab:
        """
        Return a two-layer slab with a weak layer suitable for s_r / s_sk.

        Both slab layers and the weak layer have ``hand_hardness`` and
        ``grain_form`` set so that the geldsetzer, kim_jamieson_table2, and
        kim_jamieson_table5 density pathways can each attempt computation
        (data_flow will fail since no density_measured is provided).
        ``tau_c`` is intentionally left as ``None`` — the engine populates it
        via the ``weissgraeber_rosendahl`` method before running Roch.
        """
        from snowpyt_mechparams.graph.parameter_graph import graph  # noqa: F401 (import here for clarity)
        wl = WeakLayer(hand_hardness="1F", grain_form="FC")
        layers = [
            Layer(
                thickness=ufloat(30.0, 0.0),
                hand_hardness="4F",
                grain_form="RG",
            ),
            Layer(
                thickness=ufloat(20.0, 0.0),
                hand_hardness="1F",
                grain_form="FC",
            ),
        ]
        return Slab(layers=layers, angle=35.0, weak_layer=wl)

    def test_execute_all_sr_returns_four_pathways(self):
        """s_r has exactly 4 density methods → 4 total pathways."""
        from snowpyt_mechparams.graph.parameter_graph import graph
        from snowpyt_mechparams.execution.engine import ExecutionEngine

        engine = ExecutionEngine(graph)
        slab = self._make_engine_slab()
        results = engine.execute_all(slab, "s_r")
        assert results.total_pathways == 4

    def test_execute_all_sr_populates_roch_result(self):
        """At least one s_r pathway succeeds and sets slab.roch_result."""
        from snowpyt_mechparams.graph.parameter_graph import graph
        from snowpyt_mechparams.execution.engine import ExecutionEngine

        engine = ExecutionEngine(graph)
        slab = self._make_engine_slab()
        results = engine.execute_all(slab, "s_r")
        successful = results.get_successful_pathways()
        assert len(successful) > 0, "expected at least one successful s_r pathway"
        for _, pr in successful.items():
            assert pr.slab.roch_result is not None
            assert pr.slab.roch_result.variant == "natural"
            # stability_index must be a UFloat (uncertainty propagated)
            assert hasattr(pr.slab.roch_result.stability_index, "nominal_value")

    def test_execute_all_ssk_populates_roch_skier_result(self):
        """At least one s_sk pathway succeeds and sets slab.roch_skier_result.

        Also verifies Fix 1: skier_stress is stored as a UFloat (not a plain
        float), so .nominal_value is accessible without AttributeError.
        """
        from snowpyt_mechparams.graph.parameter_graph import graph
        from snowpyt_mechparams.execution.engine import ExecutionEngine

        engine = ExecutionEngine(graph)
        slab = self._make_engine_slab()
        results = engine.execute_all(slab, "s_sk")
        successful = results.get_successful_pathways()
        assert len(successful) > 0, "expected at least one successful s_sk pathway"
        for _, pr in successful.items():
            assert pr.slab.roch_skier_result is not None
            assert pr.slab.roch_skier_result.variant == "skier"
            # skier_stress must be a UFloat — plain float would raise AttributeError here.
            stress = pr.slab.roch_skier_result.skier_stress
            assert hasattr(stress, "nominal_value"), (
                "roch_skier_result.skier_stress is a plain float, not a ufloat; "
                "check that _ROCH_SKIER_STRESS_N_M2 in dispatcher.py is wrapped in ufloat()"
            )
            assert stress.nominal_value == pytest.approx(_SKIER_STRESS, rel=1e-5)

    def test_missing_weak_layer_causes_all_sr_pathways_to_fail(self):
        """Slab without a weak_layer → tau_c unavailable → all s_r pathways fail."""
        from snowpyt_mechparams.graph.parameter_graph import graph
        from snowpyt_mechparams.execution.engine import ExecutionEngine

        engine = ExecutionEngine(graph)
        slab = Slab(
            layers=[
                Layer(
                    thickness=ufloat(30.0, 0.0),
                    hand_hardness="4F",
                    grain_form="RG",
                )
            ],
            angle=35.0,
            weak_layer=None,
        )
        results = engine.execute_all(slab, "s_r")
        assert results.successful_pathways == 0
