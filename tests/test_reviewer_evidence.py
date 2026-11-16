"""Independent fixtures for the retained descriptive evidence and export behavior."""

from copy import deepcopy
from pathlib import Path
import sys

import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paper_analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from review_audit import density_audit
from review_metrics import d11_comparison, number
from tests.test_reviewer_methods import raw_profile
from snowpyt_mechparams.models import Pit, Layer, Slab
from snowpyt_mechparams.methods.slab.bending_stiffness import calculate_D11


def test_audit_does_not_assign_contained_or_point_samples():
    raw = raw_profile(
        [([0, "cm"], [10, "cm"])],
        [([0.02, "m"], [20, "mm"], [0.25, "g/cm3"]), ([4, "cm"], None, [200, "kgm-3"])],
    )
    before = deepcopy(raw)
    observations, layers = density_audit(raw)
    assert raw == before
    assert observations[0]["containers"] == [0]
    assert observations[0]["exact_layers"] == []
    assert observations[1]["invalid_interval"]
    assert observations[1]["point_layers"] == [0]
    assert layers[0]["processing_excluded"]
    assert Pit.from_snow_pit(raw).layers[0].density_measured is None


def test_exact_first_match_and_crossing_sample_are_distinct():
    raw = raw_profile(
        [([0, "cm"], [10, "cm"])],
        [
            ([0, "cm"], [10, "cm"], [200, "kgm-3"]),
            ([0, "cm"], [10, "cm"], [300, "kgm-3"]),
            ([9, "cm"], [2, "cm"], [250, "kgm-3"]),
        ],
    )
    observations, layers = density_audit(raw)
    assert layers[0]["raw_exact_count"] == 2
    assert not layers[0]["processing_excluded"]
    assert observations[2]["boundary_crossing"]
    assert observations[2]["containers"] == []
    assert Pit.from_snow_pit(raw).layers[0].density_measured.nominal_value == 200


def test_overlap_metrics_are_descriptive_and_count_each_pair_once():
    # Intervals [-1,3], [3,5], [9,11]: first two touch and are not disjoint.
    rows = [
        dict(
            target="D11",
            slab_id="s",
            pit_id="p",
            pathway=path,
            success=True,
            value=value,
            sigma=sigma,
            n_layers=1,
            grain_forms="RG",
        )
        for path, value, sigma in [("a", 1.0, 2.0), ("b", 4.0, 1.0), ("c", 10.0, 1.0)]
    ]
    summary, per_slab, common = d11_comparison(pd.DataFrame(rows))
    assert len(common) == 3
    assert per_slab.pair_count.iloc[0] == 3
    assert per_slab.nonoverlap_pairs.iloc[0] == 2
    assert per_slab.range_to_interval_width.iloc[0] == 9 / 4
    assert summary["negative_lower_endpoints"] == 1
    assert summary["pooled_relative_uncertainty"]["median"] == 0.25
    assert len(summary["illustrations"]) == 1


def test_quantile_ties_select_distinct_slabs_deterministically():
    records = pd.DataFrame(
        [
            dict(
                target="D11",
                slab_id=slab,
                pit_id=slab,
                pathway=path,
                success=True,
                value=value,
                sigma=1.0,
                n_layers=1,
                grain_forms="RG",
            )
            for slab in ["c", "a", "b"]
            for path, value in [("x", 1.0), ("y", 2.0)]
        ]
    )
    summary, _, _ = d11_comparison(records)
    assert [x["slab_id"] for x in summary["illustrations"]] == ["a", "b", "c"]


def test_processing_and_domain_failure_partition():
    from loss_analysis_utils import analyze_losses
    from snowpyt_mechparams.models import Layer, Slab

    layer = Layer(depth_top=0, thickness=10, grain_form="SH")
    layer._review_density_processing_excluded = True
    result = analyze_losses(
        [Slab(layers=[layer], angle=30, slab_id="fixture")],
        "slab_weight_shear",
        progress=False,
    )
    direct = result.attempts[result.attempts.pathway == "Direct matched density"].iloc[
        0
    ]
    assert direct.failure_reason_classes == "processing_exclusion"
    empirical = result.attempts[result.attempts.pathway == "Geldsetzer"].iloc[0]
    assert set(empirical.failure_reason_classes.split("+")) == {
        "missing_observation",
        "unsupported_grain",
    }
    assert result.stages.newly_lost.sum() + result.attempts.success.sum() == len(
        result.attempts
    )


def test_figure_export_is_local_unless_explicit(tmp_path, monkeypatch):
    import matplotlib.pyplot as plt
    import paper_figure_utils as figures

    local, external = tmp_path / "local", tmp_path / "external"
    monkeypatch.setattr(figures, "REPO_PAPER_FIGURES_DIR", local)
    monkeypatch.setattr(figures, "EXTERNAL_PAPER_FIGURES_DIR", external)
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    try:
        paths = figures.save_paper_figure(fig, "local")
        assert paths["pdf"].exists() and paths["png"].exists()
        assert not external.exists()
        paths = figures.save_paper_figure(fig, "explicit", external_dir=external)
        assert paths["external_pdf"].read_bytes() == paths["pdf"].read_bytes()
    finally:
        plt.close(fig)


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
