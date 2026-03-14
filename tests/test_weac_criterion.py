"""
Tests for the WEAC skier stability criterion adapter.

Unit tests cover:
- _nominal() helper (no WEAC required)
- calculate_weac_skier() input validation / early-return None paths (no WEAC required)
- WeacSkierResult dataclass structure

Integration tests cover (require ``weac`` installed):
- Full round-trip: Slab → calculate_weac_skier → WeacSkierResult
- Unit-conversion correctness (cm → mm)
- UFloat stripping at adapter boundary
- weak_layer_overrides take precedence over slab.weac_layer
"""

from __future__ import annotations

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.models.weak_layer import WeakLayer
from snowpyt_mechparams.stability_criteria.weac.weac_result import WeacSkierResult
from conftest import requires_weac

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_slab(
    angle: float = 35.0,
    n_layers: int = 1,
    thickness_cm: float = 20.0,
    density: float = 250.0,
    E: float = 5.0,
    nu: float = 0.2,
    G: float = 2.0,
    wl_rho: float = 150.0,
    wl_h_cm: float = 3.0,
    with_weac_layer: bool = True,
) -> Slab:
    """
    Build a minimal ``Slab`` that satisfies every required-input check in
    ``calculate_weac_skier``.

    Parameters
    ----------
    angle : float
        Slope angle in degrees.
    n_layers : int
        Number of identical slab layers to create.
    thickness_cm : float
        Each layer's thickness in cm.
    density, E, nu, G : float
        Mechanical properties of each slab layer.
    wl_rho : float
        Weak-layer density (kg/m³).
    wl_h_cm : float
        Weak-layer thickness (cm).
    with_weac_layer : bool
        If True, attach a ``WeakLayer`` with Weißgraeber/Rosendahl reference values.
    """
    layers = [
        Layer(
            thickness=ufloat(thickness_cm, 0.0),
            density_calculated=ufloat(density, 0.0),
            elastic_modulus=ufloat(E, 0.0),
            poissons_ratio=ufloat(nu, 0.0),
            shear_modulus=ufloat(G, 0.0),
        )
        for _ in range(n_layers)
    ]

    weak_layer = Layer(
        thickness=ufloat(wl_h_cm, 0.0),
        density_measured=ufloat(wl_rho, 0.0),
    )

    weac_layer = None
    if with_weac_layer:
        weac_layer = WeakLayer(
            G_c=ufloat(1.0, 0.0),
            G_Ic=ufloat(0.56, 0.0),
            G_IIc=ufloat(0.79, 0.0),
            sigma_c=ufloat(6.16, 0.0),
            tau_c=ufloat(5.09, 0.0),
            sigma_comp=ufloat(2.6, 0.0),
        )

    return Slab(
        layers=layers,
        angle=ufloat(angle, 0.0),
        weak_layer=weak_layer,
        weac_layer=weac_layer,
    )


# ---------------------------------------------------------------------------
# _nominal() helper — no WEAC required
# ---------------------------------------------------------------------------

class TestNominalHelper:
    """Unit tests for the _nominal() UFloat-stripping helper."""

    def setup_method(self):
        from snowpyt_mechparams.stability_criteria.weac.weac_criterion import _nominal
        self._nominal = _nominal

    def test_none_returns_none(self):
        assert self._nominal(None) is None

    def test_ufloat_returns_nominal_value(self):
        v = ufloat(5.0, 0.25)
        result = self._nominal(v)
        assert result == pytest.approx(5.0)
        assert isinstance(result, float)

    def test_plain_float_passthrough(self):
        assert self._nominal(3.14) == pytest.approx(3.14)
        assert isinstance(self._nominal(3.14), float)

    def test_integer_converted_to_float(self):
        result = self._nominal(7)
        assert result == pytest.approx(7.0)
        assert isinstance(result, float)

    def test_zero_nominal_value(self):
        result = self._nominal(ufloat(0.0, 1.0))
        assert result == pytest.approx(0.0)

    def test_negative_value(self):
        result = self._nominal(ufloat(-3.5, 0.1))
        assert result == pytest.approx(-3.5)


# ---------------------------------------------------------------------------
# calculate_weac_skier — validation / early-return None (no WEAC required)
# ---------------------------------------------------------------------------

class TestCalculateWeacSkierValidation:
    """Tests that verify early-return-None paths before WEAC is called."""

    def setup_method(self):
        from snowpyt_mechparams.stability_criteria.weac.weac_criterion import (
            calculate_weac_skier,
        )
        self.fn = calculate_weac_skier

    def test_returns_none_when_angle_is_none(self):
        """Slab with angle=None should return None."""
        slab = _make_minimal_slab()
        slab.angle = None  # type: ignore[assignment]
        assert self.fn(slab) is None

    def test_returns_none_when_weak_layer_is_none(self):
        """Slab with no weak_layer should return None."""
        layer = Layer(
            thickness=ufloat(20.0, 0.0),
            density_calculated=ufloat(250.0, 0.0),
            elastic_modulus=ufloat(5.0, 0.0),
            poissons_ratio=ufloat(0.2, 0.0),
            shear_modulus=ufloat(2.0, 0.0),
        )
        slab = Slab(layers=[layer], angle=ufloat(35.0, 0.0), weak_layer=None)
        assert self.fn(slab) is None

    def test_returns_none_when_weak_layer_has_no_density(self):
        """Weak layer without density_measured or density_calculated should return None."""
        layer = Layer(
            thickness=ufloat(20.0, 0.0),
            density_calculated=ufloat(250.0, 0.0),
            elastic_modulus=ufloat(5.0, 0.0),
            poissons_ratio=ufloat(0.2, 0.0),
            shear_modulus=ufloat(2.0, 0.0),
        )
        weak_layer = Layer(thickness=ufloat(3.0, 0.0))  # no density
        slab = Slab(layers=[layer], angle=ufloat(35.0, 0.0), weak_layer=weak_layer)
        assert self.fn(slab) is None

    def test_returns_none_when_weak_layer_has_no_thickness(self):
        """Weak layer without thickness should return None."""
        layer = Layer(
            thickness=ufloat(20.0, 0.0),
            density_calculated=ufloat(250.0, 0.0),
            elastic_modulus=ufloat(5.0, 0.0),
            poissons_ratio=ufloat(0.2, 0.0),
            shear_modulus=ufloat(2.0, 0.0),
        )
        weak_layer = Layer(density_measured=ufloat(150.0, 0.0))  # no thickness
        slab = Slab(layers=[layer], angle=ufloat(35.0, 0.0), weak_layer=weak_layer)
        assert self.fn(slab) is None

    def test_returns_none_when_slab_layer_missing_density(self):
        """Slab layer without density_calculated should return None."""
        layer = Layer(
            thickness=ufloat(20.0, 0.0),
            # density_calculated omitted
            elastic_modulus=ufloat(5.0, 0.0),
            poissons_ratio=ufloat(0.2, 0.0),
            shear_modulus=ufloat(2.0, 0.0),
        )
        weak_layer = Layer(
            thickness=ufloat(3.0, 0.0),
            density_measured=ufloat(150.0, 0.0),
        )
        slab = Slab(layers=[layer], angle=ufloat(35.0, 0.0), weak_layer=weak_layer)
        assert self.fn(slab) is None

    def test_returns_none_when_slab_layer_missing_elastic_modulus(self):
        """Slab layer without elastic_modulus should return None."""
        layer = Layer(
            thickness=ufloat(20.0, 0.0),
            density_calculated=ufloat(250.0, 0.0),
            # elastic_modulus omitted
            poissons_ratio=ufloat(0.2, 0.0),
            shear_modulus=ufloat(2.0, 0.0),
        )
        weak_layer = Layer(
            thickness=ufloat(3.0, 0.0),
            density_measured=ufloat(150.0, 0.0),
        )
        slab = Slab(layers=[layer], angle=ufloat(35.0, 0.0), weak_layer=weak_layer)
        assert self.fn(slab) is None

    def test_returns_none_when_slab_layer_missing_shear_modulus(self):
        """Slab layer without shear_modulus should return None."""
        layer = Layer(
            thickness=ufloat(20.0, 0.0),
            density_calculated=ufloat(250.0, 0.0),
            elastic_modulus=ufloat(5.0, 0.0),
            poissons_ratio=ufloat(0.2, 0.0),
            # shear_modulus omitted
        )
        weak_layer = Layer(
            thickness=ufloat(3.0, 0.0),
            density_measured=ufloat(150.0, 0.0),
        )
        slab = Slab(layers=[layer], angle=ufloat(35.0, 0.0), weak_layer=weak_layer)
        assert self.fn(slab) is None


# ---------------------------------------------------------------------------
# WeacSkierResult dataclass structure (no WEAC required)
# ---------------------------------------------------------------------------

class TestWeacSkierResultStructure:
    """Verify WeacSkierResult can be constructed and fields are correct types."""

    def test_construction_with_all_fields(self):
        result = WeacSkierResult(
            g_delta=0.75,
            converged=True,
            G_I=0.42,
            G_II=0.37,
            G_total=0.79,
            critical_skier_weight=784.0,
            crack_length=0.15,
            max_dist_stress=3.5,
            min_dist_stress=-1.2,
            max_dist_ERR_envelope=0.85,
            segment_length=200.0,
            skier_mass=80.0,
        )
        assert result.g_delta == pytest.approx(0.75)
        assert result.converged is True
        assert isinstance(result.G_I, float)
        assert isinstance(result.G_II, float)
        assert isinstance(result.G_total, float)
        assert isinstance(result.critical_skier_weight, float)
        assert isinstance(result.crack_length, float)
        assert isinstance(result.segment_length, float)
        assert isinstance(result.skier_mass, float)

    def test_g_delta_less_than_one_is_stable(self):
        """g_delta < 1 indicates stable, ≥ 1 indicates unstable."""
        stable = WeacSkierResult(
            g_delta=0.5, converged=True, G_I=0.3, G_II=0.2, G_total=0.5,
            critical_skier_weight=2000.0, crack_length=0.05,
            max_dist_stress=1.0, min_dist_stress=-0.5, max_dist_ERR_envelope=0.5,
            segment_length=200.0, skier_mass=80.0,
        )
        unstable = WeacSkierResult(
            g_delta=1.2, converged=True, G_I=0.7, G_II=0.5, G_total=1.2,
            critical_skier_weight=500.0, crack_length=0.2,
            max_dist_stress=5.0, min_dist_stress=-2.0, max_dist_ERR_envelope=1.2,
            segment_length=200.0, skier_mass=80.0,
        )
        assert stable.g_delta < 1.0
        assert unstable.g_delta >= 1.0


# ---------------------------------------------------------------------------
# Integration tests — require weac
# ---------------------------------------------------------------------------

class TestCalculateWeacSkierIntegration:
    """Full round-trip integration tests using the real WEAC solver."""

    def setup_method(self):
        from snowpyt_mechparams.stability_criteria.weac.weac_criterion import (
            calculate_weac_skier,
        )
        self.fn = calculate_weac_skier

    @requires_weac
    def test_returns_weac_skier_result(self):
        """Should return a WeacSkierResult for a valid slab."""
        slab = _make_minimal_slab()
        result = self.fn(slab)
        assert result is not None
        assert isinstance(result, WeacSkierResult)

    @requires_weac
    def test_g_delta_is_finite_float(self):
        """g_delta must be a finite float after a successful run."""
        slab = _make_minimal_slab()
        result = self.fn(slab)
        assert result is not None
        assert math.isfinite(result.g_delta)

    @requires_weac
    def test_converged_is_bool(self):
        slab = _make_minimal_slab()
        result = self.fn(slab)
        assert result is not None
        assert isinstance(result.converged, bool)

    @requires_weac
    def test_G_total_approx_sum_of_G_I_G_II(self):
        """G_total ≈ G_I + G_II (WEAC uses mixed-mode ERR decomposition)."""
        slab = _make_minimal_slab()
        result = self.fn(slab)
        assert result is not None
        assert result.G_total == pytest.approx(result.G_I + result.G_II, rel=1e-4)

    @requires_weac
    def test_skier_mass_preserved_in_result(self):
        """The result should echo back the skier_mass that was passed in."""
        slab = _make_minimal_slab()
        result = self.fn(slab, skier_mass=90.0)
        assert result is not None
        assert result.skier_mass == pytest.approx(90.0)

    @requires_weac
    def test_segment_length_default_derived_from_slab_thickness(self):
        """Default segment_length = total_thickness (cm) × 10 (mm)."""
        slab = _make_minimal_slab(n_layers=1, thickness_cm=20.0)
        result = self.fn(slab)
        assert result is not None
        # total_thickness = 20 cm  → L = 200 mm
        assert result.segment_length == pytest.approx(200.0)

    @requires_weac
    def test_explicit_segment_length_overrides_default(self):
        """Explicit segment_length should be used instead of derived default."""
        slab = _make_minimal_slab()
        result = self.fn(slab, segment_length=500.0)
        assert result is not None
        assert result.segment_length == pytest.approx(500.0)

    @requires_weac
    def test_weak_layer_density_fallback_to_calculated(self):
        """If density_measured is None, density_calculated should be used."""
        slab = _make_minimal_slab()
        # Replace density_measured with density_calculated
        slab.weak_layer.density_measured = None  # type: ignore[union-attr]
        slab.weak_layer.density_calculated = ufloat(150.0, 0.0)  # type: ignore[union-attr]
        result = self.fn(slab)
        assert result is not None
        assert isinstance(result, WeacSkierResult)

    @requires_weac
    def test_ufloat_inputs_stripped_to_nominal(self):
        """UFloat inputs should be silently stripped; result should still be returned."""
        # All inputs have non-zero uncertainty
        layers = [
            Layer(
                thickness=ufloat(20.0, 1.0),
                density_calculated=ufloat(250.0, 10.0),
                elastic_modulus=ufloat(5.0, 0.5),
                poissons_ratio=ufloat(0.2, 0.02),
                shear_modulus=ufloat(2.0, 0.2),
            )
        ]
        weak_layer = Layer(
            thickness=ufloat(3.0, 0.3),
            density_measured=ufloat(150.0, 15.0),
        )
        slab = Slab(
            layers=layers,
            angle=ufloat(35.0, 2.0),
            weak_layer=weak_layer,
        )
        result = self.fn(slab)
        assert result is not None
        assert math.isfinite(result.g_delta)

    @requires_weac
    def test_weak_layer_overrides_take_precedence(self):
        """Caller-supplied weak_layer_overrides should override slab.weac_layer values."""
        slab = _make_minimal_slab()
        # Call twice: once with default values, once with a very high G_IIc override
        result_default = self.fn(slab)
        result_override = self.fn(slab, G_IIc=10.0)
        assert result_default is not None
        assert result_override is not None
        # g_delta values should differ because fracture toughness changed
        assert result_default.g_delta != pytest.approx(result_override.g_delta, rel=1e-6)

    @requires_weac
    def test_multi_layer_slab(self):
        """Should work with a multi-layer slab."""
        slab = _make_minimal_slab(n_layers=3, thickness_cm=8.0)
        result = self.fn(slab)
        assert result is not None
        assert math.isfinite(result.g_delta)

    @requires_weac
    def test_crack_length_positive(self):
        """crack_length should be positive."""
        slab = _make_minimal_slab()
        result = self.fn(slab)
        assert result is not None
        assert result.crack_length > 0

    @requires_weac
    def test_critical_skier_weight_positive(self):
        """critical_skier_weight should be positive (units: kg)."""
        slab = _make_minimal_slab()
        result = self.fn(slab)
        assert result is not None
        assert result.critical_skier_weight > 0
