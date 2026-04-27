"""Numerical validation tests for slab parameter calculations (A11, B11, D11, A55).

Tests verify slab-level integrations against hand-computed values using
simple 1- and 2-layer slabs with known properties.

Sources:
- Weissgraeber & Rosendahl (2023), Eqs. 8a-8c
"""

import math

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.methods.slab.extensional_stiffness import calculate_A11
from snowpyt_mechparams.methods.slab.bending_extension_coupling import calculate_B11
from snowpyt_mechparams.methods.slab.bending_stiffness import calculate_D11
from snowpyt_mechparams.methods.slab.shear_stiffness import calculate_A55


def _make_layer(thickness_cm, E_MPa, nu):
    """Helper to create a Layer with elastic_modulus, poissons_ratio, and thickness set."""
    layer = Layer(
        thickness=ufloat(thickness_cm, 0.0),
        elastic_modulus=ufloat(E_MPa, 0.0),
        poissons_ratio=ufloat(nu, 0.0),
    )
    return layer


def _make_shear_layer(thickness_cm, G_MPa):
    """Helper to create a Layer with shear_modulus and thickness set."""
    return Layer(
        thickness=ufloat(thickness_cm, 0.0),
        shear_modulus=ufloat(G_MPa, 0.0),
    )


# ---------------------------------------------------------------------------
# A11 = Sum_i [E_i / (1 - nu_i^2)] * h_i
# ---------------------------------------------------------------------------


class TestA11Numerical:
    """A11 = sum of plane-strain modulus * layer thickness."""

    def test_single_layer(self):
        """One layer: E=100 MPa, nu=0.2, thickness=10 cm=100 mm.

        plane_strain = 100 / (1 - 0.04) = 104.1667
        A11 = 104.1667 * 100 = 10416.67 N/mm
        """
        layer = _make_layer(10.0, 100.0, 0.2)
        slab = Slab(layers=[layer], angle=0.0)
        result = calculate_A11("weissgraeber_rosendahl", slab=slab)
        expected = 100.0 / (1.0 - 0.2**2) * 100.0
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)

    def test_two_layers(self):
        """Two layers: both E=50 MPa, nu=0.3, thickness=5 cm each (50 mm each).

        plane_strain = 50 / (1 - 0.09) = 54.945
        A11 = 54.945 * 50 + 54.945 * 50 = 5494.5 N/mm
        """
        layer1 = _make_layer(5.0, 50.0, 0.3)
        layer2 = _make_layer(5.0, 50.0, 0.3)
        slab = Slab(layers=[layer1, layer2], angle=0.0)
        result = calculate_A11("weissgraeber_rosendahl", slab=slab)
        ps = 50.0 / (1.0 - 0.3**2)
        expected = ps * 50.0 + ps * 50.0
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)

    def test_empty_slab_returns_nan(self):
        """A slab must have at least one layer (constructor enforces this)."""
        with pytest.raises(ValueError):
            Slab(layers=[], angle=0.0)

    def test_missing_E_returns_nan(self):
        layer = Layer(
            thickness=ufloat(10.0, 0.0),
            elastic_modulus=None,
            poissons_ratio=ufloat(0.2, 0.0),
        )
        slab = Slab(layers=[layer], angle=0.0)
        result = calculate_A11("weissgraeber_rosendahl", slab=slab)
        assert math.isnan(result.nominal_value)


# ---------------------------------------------------------------------------
# D11 = (1/3) * Sum_i [E_i / (1 - nu_i^2)] * (z_{i+1}^3 - z_i^3)
# ---------------------------------------------------------------------------


class TestD11Numerical:
    """D11: bending stiffness with z^2 weighting from centroid."""

    def test_single_layer_symmetric(self):
        """One layer: E=100 MPa, nu=0.2, thickness=10 cm = 100 mm.

        h_total = 100 mm, centroid at z=0
        z_top = +50, z_bottom = -50
        plane_strain = 100 / (1 - 0.04) = 104.1667
        D11 = (1/3) * 104.1667 * (50^3 - (-50)^3)
             = (1/3) * 104.1667 * (125000 + 125000)
             = (1/3) * 104.1667 * 250000
             = 8680556
        """
        layer = _make_layer(10.0, 100.0, 0.2)
        slab = Slab(layers=[layer], angle=0.0)
        result = calculate_D11("weissgraeber_rosendahl", slab=slab)
        ps = 100.0 / (1.0 - 0.2**2)
        expected = (1.0 / 3.0) * ps * (50.0**3 - (-50.0) ** 3)
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)

    def test_two_equal_layers(self):
        """Two equal layers: E=80 MPa, nu=0.25, thickness=5 cm each (50 mm).

        h_total = 100 mm, centroid at z=0
        Layer 0 (top):    z_top=+50, z_bottom=0
        Layer 1 (bottom): z_top=0, z_bottom=-50
        plane_strain = 80 / (1 - 0.0625) = 85.333
        D11 = (1/3) * 85.333 * (50^3 - 0^3) + (1/3) * 85.333 * (0^3 - (-50)^3)
            = (1/3) * 85.333 * 250000
        """
        layer1 = _make_layer(5.0, 80.0, 0.25)
        layer2 = _make_layer(5.0, 80.0, 0.25)
        slab = Slab(layers=[layer1, layer2], angle=0.0)
        result = calculate_D11("weissgraeber_rosendahl", slab=slab)
        ps = 80.0 / (1.0 - 0.25**2)
        expected = (1.0 / 3.0) * ps * (50.0**3 - (-50.0) ** 3)
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)

    def test_two_different_layers(self):
        """Two layers with different stiffness.

        Layer 0 (top): E=200 MPa, nu=0.2, thickness=3 cm (30 mm)
        Layer 1 (bottom): E=50 MPa, nu=0.3, thickness=7 cm (70 mm)

        h_total = 100 mm, centroid at z=0
        Layer 0: z_top=+50, z_bottom=+20
        Layer 1: z_top=+20, z_bottom=-50
        """
        layer1 = _make_layer(3.0, 200.0, 0.2)
        layer2 = _make_layer(7.0, 50.0, 0.3)
        slab = Slab(layers=[layer1, layer2], angle=0.0)
        result = calculate_D11("weissgraeber_rosendahl", slab=slab)

        ps1 = 200.0 / (1.0 - 0.2**2)
        ps2 = 50.0 / (1.0 - 0.3**2)
        term1 = (1.0 / 3.0) * ps1 * (50.0**3 - 20.0**3)
        term2 = (1.0 / 3.0) * ps2 * (20.0**3 - (-50.0) ** 3)
        expected = term1 + term2
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# B11 = (1/2) * Sum_i [E_i / (1 - nu_i^2)] * (z_{i+1}^2 - z_i^2)
# ---------------------------------------------------------------------------


class TestB11Numerical:
    """B11: coupling stiffness with z weighting from centroid."""

    def test_single_symmetric_layer_is_zero(self):
        """For a single homogeneous layer centered on the centroid, B11 = 0.

        z_top=+50, z_bottom=-50
        z_top^2 - z_bottom^2 = 2500 - 2500 = 0
        """
        layer = _make_layer(10.0, 100.0, 0.2)
        slab = Slab(layers=[layer], angle=0.0)
        result = calculate_B11("weissgraeber_rosendahl", slab=slab)
        assert result.nominal_value == pytest.approx(0.0, abs=1e-10)

    def test_two_equal_layers_is_zero(self):
        """Two identical layers symmetric about centroid: B11 = 0."""
        layer1 = _make_layer(5.0, 80.0, 0.25)
        layer2 = _make_layer(5.0, 80.0, 0.25)
        slab = Slab(layers=[layer1, layer2], angle=0.0)
        result = calculate_B11("weissgraeber_rosendahl", slab=slab)
        assert result.nominal_value == pytest.approx(0.0, abs=1e-10)

    def test_two_different_layers_nonzero(self):
        """Asymmetric slab has nonzero B11.

        Layer 0 (top): E=200 MPa, nu=0.2, thickness=3 cm (30 mm)
        Layer 1 (bottom): E=50 MPa, nu=0.3, thickness=7 cm (70 mm)

        h_total = 100 mm, centroid at z=0
        Layer 0: z_top=+50, z_bottom=+20
        Layer 1: z_top=+20, z_bottom=-50
        """
        layer1 = _make_layer(3.0, 200.0, 0.2)
        layer2 = _make_layer(7.0, 50.0, 0.3)
        slab = Slab(layers=[layer1, layer2], angle=0.0)
        result = calculate_B11("weissgraeber_rosendahl", slab=slab)

        ps1 = 200.0 / (1.0 - 0.2**2)
        ps2 = 50.0 / (1.0 - 0.3**2)
        term1 = (1.0 / 2.0) * ps1 * (50.0**2 - 20.0**2)
        term2 = (1.0 / 2.0) * ps2 * (20.0**2 - (-50.0) ** 2)
        expected = term1 + term2
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)
        # Stiffer layer on top should make B11 positive
        assert result.nominal_value > 0


# ---------------------------------------------------------------------------
# A55 = κ * Sum_i G_i * h_i,  κ = 5/6
# ---------------------------------------------------------------------------


class TestA55Numerical:
    """A55: shear stiffness with κ = 5/6 correction factor."""

    def test_single_layer(self):
        """One layer: G=50 MPa, thickness=10 cm (100 mm).

        A55 = (5/6) * 50 * 100 = 4166.667 N/mm
        """
        layer = _make_shear_layer(10.0, 50.0)
        slab = Slab(layers=[layer], angle=0.0)
        result = calculate_A55("weissgraeber_rosendahl", slab=slab)
        expected = (5.0 / 6.0) * 50.0 * 100.0
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)

    def test_two_layers(self):
        """Two equal layers: G=50 MPa, 5 cm each (50 mm each).

        A55 = (5/6) * (50*50 + 50*50) = (5/6) * 5000 = 4166.667 N/mm
        Same total as a single 10 cm layer.
        """
        layer1 = _make_shear_layer(5.0, 50.0)
        layer2 = _make_shear_layer(5.0, 50.0)
        slab = Slab(layers=[layer1, layer2], angle=0.0)
        result = calculate_A55("weissgraeber_rosendahl", slab=slab)
        expected = (5.0 / 6.0) * (50.0 * 50.0 + 50.0 * 50.0)
        assert result.nominal_value == pytest.approx(expected, rel=1e-6)

    def test_missing_shear_modulus_returns_nan(self):
        """Layer with shear_modulus=None should return NaN."""
        layer = Layer(
            thickness=ufloat(10.0, 0.0),
            shear_modulus=None,
        )
        slab = Slab(layers=[layer], angle=0.0)
        result = calculate_A55("weissgraeber_rosendahl", slab=slab)
        assert math.isnan(result.nominal_value)

    def test_unknown_method_raises(self):
        layer = _make_shear_layer(10.0, 50.0)
        slab = Slab(layers=[layer], angle=0.0)
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_A55("nonexistent", slab=slab)


# ---------------------------------------------------------------------------
# Unknown method
# ---------------------------------------------------------------------------


class TestUnknownSlabMethod:
    def test_unknown_A11_raises(self):
        layer = _make_layer(10.0, 100.0, 0.2)
        slab = Slab(layers=[layer], angle=0.0)
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_A11("nonexistent", slab=slab)

    def test_unknown_B11_raises(self):
        layer = _make_layer(10.0, 100.0, 0.2)
        slab = Slab(layers=[layer], angle=0.0)
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_B11("nonexistent", slab=slab)

    def test_unknown_D11_raises(self):
        layer = _make_layer(10.0, 100.0, 0.2)
        slab = Slab(layers=[layer], angle=0.0)
        with pytest.raises(ValueError, match="Unknown method"):
            calculate_D11("nonexistent", slab=slab)
