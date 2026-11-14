"""Regression cases for the source correction and density-assignment sensitivity."""

from pathlib import Path
import math
import sys
from types import SimpleNamespace

import pytest
from uncertainties import ufloat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paper_analysis"))
from reviewer_response_analysis import contained_density  # noqa: E402
from loss_analysis_utils import diagnose_layer  # noqa: E402
from snowpyt_mechparams.execution import ExecutionConfig, ExecutionEngine  # noqa: E402
from snowpyt_mechparams.methods.layer import calculate_elastic_modulus  # noqa: E402
from snowpyt_mechparams.models import Layer, Slab  # noqa: E402


@pytest.mark.parametrize("grain", ["PP", "PPgp", "ppsd"])
def test_wautier_precipitation_subclasses_and_uncertainty(grain):
    rho = ufloat(200, 20)
    result = calculate_elastic_modulus("wautier", density=rho, grain_form=grain)
    expected = 7800 * (200 / 917) ** 2.34
    assert result.nominal_value == pytest.approx(expected)
    assert result.std_dev == pytest.approx(expected * 2.34 * 0.1)
    assert not diagnose_layer(
        Layer(grain_form=grain),
        "elastic_modulus",
        "wautier",
        density=rho,
        output=result,
    )


@pytest.mark.parametrize("grain", ["SH", "IF", "MM"])
def test_wautier_still_rejects_unrepresented_grains(grain):
    result = calculate_elastic_modulus("wautier", density=200, grain_form=grain)
    assert math.isnan(result.nominal_value)


def test_pp_enables_complete_pathway_without_enabling_kochle_poisson():
    slab = Slab(
        layers=[Layer(depth_top=0, thickness=10, grain_form="PP", hand_hardness="P")],
        angle=35,
    )
    methods = {
        "density": "kim_jamieson_table2",
        "elastic_modulus": "wautier",
        "poissons_ratio": "srivastava",
    }
    engine = ExecutionEngine()
    config = ExecutionConfig(include_method_uncertainty=False)
    good = engine.execute_single(slab, "D11", methods, config=config)
    assert good.slab.D11.nominal_value > 0
    bad = engine.execute_single(
        slab, "D11", {**methods, "poissons_ratio": "kochle"}, config=config
    )
    assert bad.slab.D11 is None


def obs(top, h, rho):
    return SimpleNamespace(
        depth_top=[top, "cm"], thickness=[h, "cm"], density=[rho, "kgm-3"]
    )


def test_contained_density_weights_sample_extent_and_preserves_exact_priority():
    layer = obs(10, 20, 0)
    assert contained_density(layer, [obs(12, 2, 100), obs(17, 6, 300)]) == (
        250,
        "contained",
        0.4,
    )
    assert contained_density(layer, [obs(12, 2, 100), obs(10, 20, 200)]) == (
        200,
        "exact",
        1.0,
    )


def test_contained_density_rejects_overlap_boundary_crossing_and_missing_extent():
    layer = obs(10, 20, 0)
    assert (
        contained_density(layer, [obs(12, 5, 100), obs(15, 5, 200)])[1]
        == "overlapping_contained_samples"
    )
    point = obs(15, 2, 300)
    point.thickness = None
    assert contained_density(layer, [obs(5, 10, 100), point])[0] is None
