"""Independent boundary, provenance, propagation and output-safety checks."""

from pathlib import Path
import math
import sys
from types import SimpleNamespace as NS

import numpy as np
import pandas as pd
import pytest
from uncertainties import ufloat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paper_analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from review_audit import density_audit, assign_contained
from review_metrics import d11_comparison, number
from review_monte_carlo import (
    sample_observations,
    standardized_draws,
    density_vector,
    elastic_vector,
    evaluate,
    summarize,
    synthetic,
)
from snowpyt_mechparams.models import Pit, Slab, Layer
from snowpyt_mechparams.models.pit_parser import parse_pit
from snowpyt_mechparams.methods.layer.elastic_modulus import calculate_elastic_modulus
from snowpyt_mechparams.methods.layer.density import calculate_density
from snowpyt_mechparams.methods.slab.bending_stiffness import calculate_D11


@pytest.mark.parametrize(
    "grain,low,high",
    [
        ("SH", 0.074 * 916.7, 0.191 * 916.7),
        ("DF", 0.162 * 916.7, 0.388 * 916.7),
        ("RG", 0.162 * 916.7, 0.388 * 916.7),
        ("FC", 0.164 * 916.7, 0.505 * 916.7),
        ("DH", 0.164 * 916.7, 0.505 * 916.7),
    ],
)
def test_author_supplied_schottner_bounds(grain, low, high):
    for rho, valid in [
        (math.nextafter(low, -math.inf), False),
        (low, True),
        (math.nextafter(low, math.inf), True),
        ((low + high) / 2, True),
        (math.nextafter(high, -math.inf), True),
        (high, True),
        (math.nextafter(high, math.inf), False),
    ]:
        actual = calculate_elastic_modulus(
            "schottner",
            density=ufloat(rho, 50),
            grain_form=grain + "xx",
            include_method_uncertainty=False,
        )
        assert math.isfinite(actual.nominal_value) == valid


@pytest.mark.parametrize("grain", ["PP", "PPgp", "ppsd"])
def test_wautier_precipitation_particles(grain):
    result = calculate_elastic_modulus("wautier", density=200, grain_form=grain)
    assert number(result) == pytest.approx(10000 * 0.78 * (200 / 917) ** 2.34)


def raw_profile(layer_bounds, samples):
    def layer(top, h):
        return NS(
            depth_top=top,
            thickness=h,
            hardness="1F",
            layer_of_concern=False,
            grain_form_primary=NS(
                sub_grain_class_code=None,
                basic_grain_class_code="RG",
                grain_size_avg=[2, "mm"],
            ),
        )

    return NS(
        snow_profile=NS(
            layers=[layer(*b) for b in layer_bounds],
            density_profile=[
                NS(depth_top=t, thickness=h, density=r) for t, h, r in samples
            ],
        ),
        stability_tests=None,
    )


@pytest.mark.parametrize("size", [-1, 0, 0.25, 1, 3])
def test_parser_relative_grain_size(size):
    raw = raw_profile([([0, "cm"], [10, "cm"])], [])
    raw.snow_profile.layers[0].grain_form_primary.grain_size_avg = [size, "mm"]
    value = parse_pit(raw).layers[0].grain_size_avg
    assert value.nominal_value == size
    assert value.std_dev == pytest.approx(0.48 * abs(size))


def test_density_exact_precedes_contained_and_first_exact_wins():
    raw = raw_profile(
        [([0, "cm"], [10, "cm"])],
        [
            ([0, "cm"], [10, "cm"], [200, "kgm-3"]),
            ([0, "cm"], [10, "cm"], [300, "kgm-3"]),
            ([2, "cm"], [2, "cm"], [400, "kgm-3"]),
        ],
    )
    pit = Pit.from_snow_pit(raw)
    ledger = assign_contained(raw, pit)
    assert ledger[0]["raw_exact_count"] == 2
    assert pit.layers[0].density_measured.nominal_value == 200


def test_single_contained_sample_normalizes_units_and_retains_partial_coverage():
    raw = raw_profile(
        [([0, "cm"], [10, "cm"])], [([0.02, "m"], [20, "mm"], [0.25, "g/cm3"])]
    )
    pit = Pit.from_snow_pit(raw)
    assert pit.layers[0].density_measured is None
    ledger = assign_contained(raw, pit)
    assert pit.layers[0].density_measured.nominal_value == 250
    assert pit.layers[0].density_measured.std_dev == 25
    assert ledger[0]["sampled_fraction"] == pytest.approx(0.2)


def test_point_density_is_processing_exclusion_but_never_assigned():
    raw = raw_profile([([0, "cm"], [10, "cm"])], [([2, "cm"], None, [200, "kgm-3"])])
    observations, ledger = density_audit(raw)
    assert observations[0]["invalid_interval"]
    assert observations[0]["point_layers"] == [0]
    assert ledger[0]["processing_excluded"]
    pit = Pit.from_snow_pit(raw)
    assign_contained(raw, pit)
    assert pit.layers[0].density_measured is None


@pytest.mark.parametrize(
    "samples,bounds",
    [
        (
            [
                ([1, "cm"], [2, "cm"], [200, "kgm-3"]),
                ([4, "cm"], [2, "cm"], [300, "kgm-3"]),
            ],
            [([0, "cm"], [10, "cm"])],
        ),
        (
            [([1, "cm"], [2, "cm"], [200, "kgm-3"])],
            [([0, "cm"], [10, "cm"]), ([0, "cm"], [5, "cm"])],
        ),
        ([([9, "cm"], [2, "cm"], [200, "kgm-3"])], [([0, "cm"], [10, "cm"])]),
        ([([1, "cm"], [0, "cm"], [200, "kgm-3"])], [([0, "cm"], [10, "cm"])]),
        ([([1, "cm"], [2, "cm"], [-200, "kgm-3"])], [([0, "cm"], [10, "cm"])]),
        ([([1, "cm"], [2, "cm"], [float("nan"), "kgm-3"])], [([0, "cm"], [10, "cm"])]),
        ([([1, "cm"], [2, "cm"], [float("inf"), "kgm-3"])], [([0, "cm"], [10, "cm"])]),
    ],
)
def test_density_fallback_rejects_ambiguity_and_invalid_samples(samples, bounds):
    raw = raw_profile(bounds, samples)
    pit = Pit.from_snow_pit(raw)
    assign_contained(raw, pit)
    assert all(layer.density_measured is None for layer in pit.layers)


def test_reference_plane_and_units_independent_D11():
    layers = [
        Layer(depth_top=0, thickness=3, elastic_modulus=200, poissons_ratio=0.2),
        Layer(depth_top=3, thickness=7, elastic_modulus=50, poissons_ratio=0.3),
    ]
    expected = (
        200 / (1 - 0.2**2) * (50**3 - 20**3) + 50 / (1 - 0.3**2) * (20**3 - (-50) ** 3)
    ) / 3
    actual = calculate_D11("weissgraeber_rosendahl", slab=Slab(layers=layers, angle=0))
    assert number(actual) == pytest.approx(expected)
    for layer in layers:
        layer.depth_top += 120
    assert number(
        calculate_D11("weissgraeber_rosendahl", slab=Slab(layers=layers, angle=0))
    ) == pytest.approx(expected)
    downward = (
        200 / (1 - 0.2**2) * ((-20) ** 3 - (-50) ** 3)
        + 50 / (1 - 0.3**2) * (50**3 - (-20) ** 3)
    ) / 3
    assert downward == pytest.approx(expected)
    # SI independently gives N m; source uses MPa/mm and returns N mm.
    expected_si = (
        200e6 / (1 - 0.2**2) * (0.05**3 - 0.02**3)
        + 50e6 / (1 - 0.3**2) * (0.02**3 - (-0.05) ** 3)
    ) / 3
    assert expected / 1000 == pytest.approx(expected_si)


def test_vector_density_matches_all_scalar_methods():
    from loss_analysis_utils import HARDNESS_RANGES

    for method, grains in HARDNESS_RANGES.items():
        for grain, (lo, hi) in grains.items():
            h = np.array([lo - 0.01, lo, (lo + hi) / 2, hi, hi + 0.01])
            samples = {
                "angle": np.zeros(5),
                "hand_hardness_index": h[:, None],
                "grain_size_avg": np.ones((5, 1)),
            }
            rho, valid = density_vector(method, grain, samples, 0)
            for i, x in enumerate(h):
                kw = {
                    "hand_hardness_index": float(x),
                    "grain_form": grain,
                    "include_method_uncertainty": False,
                }
                if method == "kim_jamieson_table6":
                    kw["grain_size"] = 1.0
                scalar = calculate_density(method, **kw)
                assert valid[i] == math.isfinite(number(scalar))
                if valid[i]:
                    assert rho[i] == pytest.approx(number(scalar))


@pytest.mark.parametrize("method", ["bergfeld", "wautier", "kochle", "schottner"])
@pytest.mark.parametrize("grain", ["PP", "RG", "FC", "DH", "SH", "MF", "IF"])
def test_vector_elastic_matches_scalar(method, grain):
    rho = np.array([50, 100, 150, 200, 249, 250, 300, 400, 550])
    values, valid = elastic_vector(method, grain, rho)
    for i, x in enumerate(rho):
        scalar = calculate_elastic_modulus(
            method, density=float(x), grain_form=grain, include_method_uncertainty=False
        )
        assert valid[i] == math.isfinite(number(scalar))
        if valid[i]:
            assert values[i] == pytest.approx(number(scalar))


def test_sampling_reproducibility_correlation_and_partition():
    slab = synthetic(layers=2)
    a = sample_observations(slab, 20000, 0.5, 42)
    b = sample_observations(slab, 20000, 0.5, 42)
    for key in a:
        np.testing.assert_equal(a[key], b[key])
    for correlation in [0, 0.5, 1]:
        z = standardized_draws(20000, 2, correlation, np.random.default_rng(42))
        assert np.corrcoef(z.T)[0, 1] == pytest.approx(correlation, abs=0.02)
    out, masks = evaluate(slab, "D11", ("data_flow", "wautier", "kochle"), a)
    np.testing.assert_equal(sum(m.astype(int) for m in masks.values()), np.ones(20000))
    assert sum(summarize(out, masks)[k] for k in masks) == 20000
    # Gaussian linear control, before validity conditioning.
    z = np.random.default_rng(42).normal(3, 0.1, 20000)
    y = 112 + 46 * z
    assert y.mean() == pytest.approx(250, abs=5 * 4.6 / math.sqrt(20000))
    assert y.std(ddof=1) == pytest.approx(4.6, rel=0.03)


@pytest.mark.parametrize("elastic", ["bergfeld", "wautier", "kochle", "schottner"])
def test_vector_D11_matches_layered_scalar_calculation(elastic):
    from snowpyt_mechparams.methods.layer.poissons_ratio import calculate_poissons_ratio

    slab = synthetic(layers=2)
    slab.layers[1].depth_top = (
        23  # Preserve a measured gap, not reconstructed boundaries.
    )
    samples = sample_observations(slab, 20, 0.5, 793)
    values, masks = evaluate(slab, "D11", ("data_flow", elastic, "kochle"), samples)
    assert masks["success"].any()
    for draw in np.flatnonzero(masks["success"]):
        layers = []
        for i, layer in enumerate(slab.layers):
            rho = float(samples["density_measured"][draw, i])
            layers.append(
                Layer(
                    depth_top=layer.depth_top,
                    thickness=float(samples["thickness"][draw, i]),
                    elastic_modulus=calculate_elastic_modulus(
                        elastic,
                        density=rho,
                        grain_form="RG",
                        include_method_uncertainty=False,
                    ),
                    poissons_ratio=calculate_poissons_ratio(
                        "kochle", grain_form="RG", include_method_uncertainty=False
                    ),
                )
            )
        scalar = calculate_D11(
            "weissgraeber_rosendahl", slab=Slab(layers=layers, angle=30)
        )
        assert values[draw] == pytest.approx(number(scalar))


def test_linear_control_uses_shared_observations_across_pathways():
    slab = synthetic("FC")
    slab.layers[0].hand_hardness = "F+"
    # Central, narrow synthetic errors keep both calibrations applicable.
    samples = sample_observations(slab, 20000, 0, 42)
    samples["hand_hardness_index"] = np.random.default_rng(42).normal(
        2.5, 0.1, (20000, 1)
    )
    a, ma = evaluate(slab, "density", ("geldsetzer", "", ""), samples)
    b, mb = evaluate(slab, "density", ("kim_jamieson_table2", "", ""), samples)
    assert ma["success"].all() and mb["success"].all()
    h = samples["hand_hardness_index"][:, 0]
    np.testing.assert_allclose(a - b, 9 - 4.6 * h)
    assert a.mean() == pytest.approx(112 + 46 * 2.5, abs=5 * 4.6 / math.sqrt(20000))
    assert a.std(ddof=1) == pytest.approx(4.6, rel=0.03)


def test_d11_statistics_pair_count_and_pooled_aggregation():
    rows = [
        dict(
            target="D11",
            slab_id="s",
            pit_id="p",
            pathway=str(i),
            success=True,
            value=float(i + 1),
            sigma=0.1,
            n_layers=1,
            grain_forms="RG",
        )
        for i in range(16)
    ]
    summary, stats, _ = d11_comparison(pd.DataFrame(rows), [str(i) for i in range(16)])
    assert stats.pair_count.iloc[0] == 120
    assert stats.nonoverlap_pairs.iloc[0] == 120
    assert summary["pooled_relative_uncertainty"]["n"] == 16


def test_figures_never_copy_outside_repo_without_explicit_destination(
    tmp_path, monkeypatch
):
    import matplotlib.pyplot as plt
    import paper_figure_utils as figures

    monkeypatch.setattr(
        figures, "EXTERNAL_PAPER_FIGURES_DIR", tmp_path / "must_not_exist"
    )
    fig = plt.figure()
    paths = figures.save_paper_figure(
        fig, "example", output_dir=tmp_path / "local", close=True
    )
    assert paths["pdf"].exists()
    assert not (tmp_path / "must_not_exist").exists()
