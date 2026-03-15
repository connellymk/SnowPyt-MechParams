"""
Tests for the Roch stability criterion.

Unit tests cover:
- calculate_shear_stress(): formula correctness, edge cases, UFloat propagation
- calculate_roch(): natural and skier variants, None-return conditions, result fields
"""

from __future__ import annotations

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.stability_criteria.roch.roch_criterion import calculate_roch
from snowpyt_mechparams.stability_criteria.roch.roch_result import RochResult
from snowpyt_mechparams.stability_criteria.roch.shear_stress import calculate_shear_stress

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_G = 9.81  # m/s²


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

    def test_missing_thickness_returns_nan(self):
        """A layer with thickness=None → returns plain float math.nan."""
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)], missing_thickness_idx=0)
        tau = calculate_shear_stress(slab)
        # shear_stress.py returns float('nan') (plain float) for missing data
        assert isinstance(tau, float) and math.isnan(tau)

    def test_missing_density_calculated_returns_nan(self):
        """A layer with density_calculated=None → returns plain float math.nan."""
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)], missing_density_idx=0)
        tau = calculate_shear_stress(slab)
        assert isinstance(tau, float) and math.isnan(tau)

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

    def test_returns_none_when_angle_is_none(self):
        layer = Layer(thickness=ufloat(50.0, 0.0), density_calculated=ufloat(300.0, 0.0))
        slab = Slab(layers=[layer], angle=None)
        assert calculate_roch(slab, tau_c=ufloat(1500.0, 0.0)) is None

    def test_returns_none_when_layer_missing_density(self):
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)], missing_density_idx=0)
        assert calculate_roch(slab, tau_c=ufloat(1500.0, 0.0)) is None

    def test_natural_returns_none_flat_terrain(self):
        """τ=0 (θ=0°) is undefined for the natural criterion."""
        slab = _make_slab(angle=0.0, layers=[(50.0, 300.0)])
        assert calculate_roch(slab, tau_c=ufloat(1500.0, 0.0)) is None

    def test_natural_returns_none_negative_angle(self):
        """τ<0 (counter-slope) is physically meaningless; must return None."""
        slab = _make_slab(angle=-5.0, layers=[(50.0, 300.0)])
        assert calculate_roch(slab, tau_c=ufloat(1500.0, 0.0)) is None

    def test_skier_returns_none_zero_skier_stress(self):
        """τ_sk=0 makes the skier criterion undefined."""
        slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)])
        assert calculate_roch(slab, tau_c=ufloat(1500.0, 0.0), skier_stress=0.0) is None


class TestCalculateRochNaturalVariant:
    """Numerical correctness and result fields for the natural (S_r) criterion."""

    def setup_method(self):
        self.slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)])
        self.tau_c = ufloat(1500.0, 0.0)
        self.expected_tau = 300.0 * 0.5 * _G * math.sin(math.radians(38.0))
        self.expected_sr = 1500.0 / self.expected_tau

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

    def test_tau_c_stored_in_result(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert result is not None
        assert result.tau_c.nominal_value == pytest.approx(1500.0)

    def test_returns_roch_result_instance(self):
        result = calculate_roch(self.slab, tau_c=self.tau_c)
        assert isinstance(result, RochResult)

    def test_stability_index_below_one_when_unstable(self):
        """τ_c < τ → S_r < 1 (unstable)."""
        tau_c_small = ufloat(500.0, 0.0)  # much less than expected_tau ≈ 906 N/m²
        result = calculate_roch(self.slab, tau_c=tau_c_small)
        assert result is not None
        assert result.stability_index.nominal_value < 1.0

    def test_ufloat_tau_c_propagates_uncertainty(self):
        """Uncertainty in τ_c should propagate to stability_index."""
        tau_c_with_unc = ufloat(1500.0, 50.0)
        result = calculate_roch(self.slab, tau_c=tau_c_with_unc)
        assert result is not None
        assert hasattr(result.stability_index, "std_dev")
        assert result.stability_index.std_dev > 0


class TestCalculateRochSkierVariant:
    """Numerical correctness and result fields for the skier (S_sk) criterion."""

    def setup_method(self):
        self.slab = _make_slab(angle=38.0, layers=[(50.0, 300.0)])
        self.tau_c = ufloat(1500.0, 0.0)
        self.tau_sk = ufloat(1206.0, 0.0)
        self.expected_tau = 300.0 * 0.5 * _G * math.sin(math.radians(38.0))
        self.expected_ssk = (1500.0 - self.expected_tau) / 1206.0

    def test_correct_ssk_value(self):
        """S_sk = (τ_c − τ) / τ_sk should match hand-computed value."""
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
        assert result.skier_stress.nominal_value == pytest.approx(1206.0)

    def test_flat_terrain_is_valid_for_skier(self):
        """θ=0° (τ=0) is valid for the skier criterion; only τ_sk=0 is forbidden."""
        slab_flat = _make_slab(angle=0.0, layers=[(50.0, 300.0)])
        result = calculate_roch(slab_flat, tau_c=self.tau_c, skier_stress=self.tau_sk)
        assert result is not None
        assert result.variant == "skier"
        assert result.stability_index.nominal_value == pytest.approx(1500.0 / 1206.0, rel=1e-4)
