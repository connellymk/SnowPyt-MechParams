"""Independent method-domain checks and loss-accounting regression scenarios."""

import sys
from pathlib import Path

import numpy as np
import pytest
from uncertainties import ufloat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paper_analysis"))
from loss_analysis_utils import (  # noqa: E402
    DENSITY_RANGES,
    GRAIN_DOMAINS,
    HARDNESS_RANGES,
    Issue,
    analyze_losses,
    diagnose_layer,
    failure_category,
    finite,
    plot_histogram,
)
from snowpyt_mechparams.constants import HARDNESS_MAPPING  # noqa: E402
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher  # noqa: E402
from snowpyt_mechparams.models import Layer, Slab  # noqa: E402


def test_absent_and_unsupported_grain_forms_are_distinct():
    missing = diagnose_layer(Layer(hand_hardness="1F"), "density", "geldsetzer")
    unsupported = diagnose_layer(
        Layer(grain_form="MF", hand_hardness="1F"), "density", "geldsetzer"
    )
    assert {i.category for i in missing} == {"missing"}
    assert {i.category for i in unsupported} == {"validity"}
    assert unsupported[0].grain_form == "MF"
    assert unsupported[0].resolved_grain_form == ""


@pytest.mark.parametrize("method", list(HARDNESS_RANGES))
def test_density_domains_match_dispatcher_for_every_grain_and_hardness(method):
    """Check actual methods at all recorded HH values, including both bounds."""
    grains = set(HARDNESS_RANGES[method]) | {"RGwp", "RGxf", "FCxr", "MFcr", "SH", "IF"}
    dispatcher = MethodDispatcher()
    for grain in grains:
        for hardness in HARDNESS_MAPPING:
            layer = Layer(
                grain_form=grain,
                hand_hardness=hardness,
                grain_size_avg=ufloat(0.5, 0.1),
            )
            output, error = dispatcher.execute(
                "density", method, layer=layer, include_method_uncertainty=False
            )
            issues = diagnose_layer(
                layer, "density", method, output=output, error=error
            )
            assert finite(output) == (not issues), (method, grain, hardness, issues)
            assert not any(i.category == "other" for i in issues)


def test_density_subclasses_resolve_without_losing_original_code():
    layer = Layer(grain_form="RGxf", hand_hardness="F-")
    issues = diagnose_layer(layer, "density", "geldsetzer")
    assert len(issues) == 1
    assert issues[0].field == "hand_hardness_index"
    assert issues[0].grain_form == "RGxf"
    assert issues[0].resolved_grain_form == "RG"
    assert issues[0].lower == 1.0


@pytest.mark.parametrize("method", list(DENSITY_RANGES))
def test_elastic_density_boundaries_match_actual_method(method):
    low, high = DENSITY_RANGES[method]
    dispatcher = MethodDispatcher()
    for density in [low - 0.001, low, low + 0.001, high - 0.001, high, high + 0.001]:
        layer = Layer(grain_form="RG", density_calculated=ufloat(density, 1))
        output, error = dispatcher.execute(
            "elastic_modulus", method, layer=layer, include_method_uncertainty=False
        )
        issues = diagnose_layer(
            layer,
            "elastic_modulus",
            method,
            density=layer.density_calculated,
            output=output,
            error=error,
        )
        assert finite(output) == (not issues)
        assert not any(i.category == "other" for i in issues)


@pytest.mark.parametrize("grain", ["RG", "FC", "PP"])
def test_srivastava_density_bounds_and_unbounded_non_rg(grain):
    dispatcher = MethodDispatcher()
    for density in [199.999, 200, 200.001, 580, 580.001, 1000]:
        layer = Layer(grain_form=grain, density_calculated=ufloat(density, 1))
        output, error = dispatcher.execute(
            "poissons_ratio",
            "srivastava",
            layer=layer,
            include_method_uncertainty=False,
        )
        issues = diagnose_layer(
            layer,
            "poissons_ratio",
            "srivastava",
            density=layer.density_calculated,
            output=output,
            error=error,
        )
        assert finite(output) == (not issues)
        assert not any(i.category == "other" for i in issues)


@pytest.mark.parametrize("parameter,method", list(GRAIN_DOMAINS))
def test_elastic_grain_domains_match_actual_methods(parameter, method):
    dispatcher = MethodDispatcher()
    for grain in ["PP", "DF", "RGwp", "FCxr", "DH", "SH", "MFcr", "IF"]:
        layer = Layer(grain_form=grain, density_calculated=ufloat(250, 1))
        output, error = dispatcher.execute(
            parameter, method, layer=layer, include_method_uncertainty=False
        )
        issues = diagnose_layer(
            layer,
            parameter,
            method,
            density=layer.density_calculated,
            output=output,
            error=error,
        )
        assert finite(output) == (not issues), (parameter, method, grain, issues)
        assert not any(i.category == "other" for i in issues)


def test_all_evaluable_causes_and_blocking_are_preserved():
    layer = Layer(grain_form="IF")
    density_issues = diagnose_layer(layer, "density", "kim_jamieson_table6")
    assert {i.field for i in density_issues} == {
        "grain_form",
        "hand_hardness",
        "grain_size",
    }
    assert failure_category(density_issues) == "mixed"
    downstream = diagnose_layer(layer, "elastic_modulus", "bergfeld")
    assert {i.category for i in downstream} == {"blocked", "validity"}
    assert not any(i.category == "missing" for i in downstream)
    # When density exists, both independently violated constraints are reported.
    observed = diagnose_layer(layer, "elastic_modulus", "bergfeld", density=500)
    assert {i.field for i in observed} == {"grain_form", "density"}
    assert {i.category for i in observed} == {"validity"}


def test_unrecognized_hardness_is_not_missing_or_a_published_range():
    issues = diagnose_layer(
        Layer(grain_form="RG", hand_hardness="unknown"), "density", "geldsetzer"
    )
    assert {i.category for i in issues} == {"other"}
    assert issues[0].observed == "unknown"


def _slab(layer, index, angle=30):
    return Slab(layers=[layer], angle=angle, slab_id=f"slab_{index}", pit_id="pit")


@pytest.mark.parametrize("target", ["D11", "slab_weight_shear_with_elasticity"])
def test_shared_branches_and_layers_are_deduplicated_and_funnels_reconcile(target):
    source = Layer(
        depth_top=0, thickness=10, grain_form="RG", density_measured=ufloat(250, 25)
    )
    slabs = [_slab(source, 0), _slab(source, 1)]
    result = analyze_losses(slabs, target, progress=False)
    assert len(result.attempts) == 64
    rows = result.method_summary
    missing = rows[
        (rows.parameter == "density")
        & (rows.method == "geldsetzer")
        & (rows.category == "missing")
    ].iloc[0]
    assert missing.slabs == 2 and missing.layers == 1
    emod = rows[
        (rows.parameter == "elastic_modulus")
        & (rows.method == "bergfeld")
        & (rows.density_context == "geldsetzer")
        & (rows.category == "blocked")
    ].iloc[0]
    assert emod.slabs == 2 and emod.layers == 1
    assert not result.attempts.loc[
        result.attempts.density_method != "data_flow", "success"
    ].any()
    assert result.attempts.loc[
        result.attempts.density_method == "data_flow", "success"
    ].any()
    assert result.histogram.sum() == 2
    assert len(result.histogram) == 33
    assert (result.stages.newly_lost.sum() + result.attempts.success.sum()) == 64


def test_zero_weight_and_nonfinite_slope_and_mixed_loss():
    valid = Layer(
        depth_top=0,
        thickness=10,
        grain_form="RG",
        hand_hardness="1F",
        density_measured=ufloat(250, 25),
        grain_size_avg=ufloat(0.5, 0.1),
    )
    invalid = Layer(depth_top=0, thickness=10, grain_form="IF")
    slabs = [_slab(valid, 0, angle=0), _slab(valid, 1, angle=np.nan), _slab(invalid, 2)]
    result = analyze_losses(slabs, "slab_weight_shear", progress=False)
    assert result.attempts[result.attempts.slab_index == 0].success.sum() == 3
    assert (
        result.attempts.loc[result.attempts.slab_index == 0, "value"]
        .dropna()
        .eq(0)
        .all()
    )
    assert not result.attempts[result.attempts.slab_index == 1].success.any()
    mixed = result.attempts[
        (result.attempts.slab_index == 2)
        & (result.attempts.density_method == "geldsetzer")
    ]
    assert mixed.iloc[0].failure_category == "mixed"
    assert list(result.histogram.index) == list(range(5))
    figure = plot_histogram(result)
    assert len(figure.axes[0].patches) == 5
    assert figure.axes[0].get_ylabel() == "ECTP slabs"
    import matplotlib.pyplot as plt

    plt.close(figure)


def test_missing_geometry_is_observation_loss_and_nonpositive_d11_is_other():
    missing = Layer(depth_top=0, grain_form="RG", density_measured=ufloat(250, 1))
    result = analyze_losses([_slab(missing, 0)], "D11", progress=False)
    assert not result.attempts.success.any()
    assert result.details("geometry").iloc[0].category == "missing"
    zero = Layer(
        depth_top=0, thickness=0, grain_form="RG", density_measured=ufloat(250, 1)
    )
    result = analyze_losses([_slab(zero, 0)], "D11", progress=False)
    direct = result.attempts[result.attempts.density_method == "data_flow"]
    assert set(direct.first_failed_step) == {"D11"}
    assert set(direct.failure_category) == {"other"}


def test_failure_partition_covers_all_cases():
    assert failure_category([Issue("missing", "absent", "hh")]) == "missing_only"
    assert failure_category([Issue("validity", "unsupported", "gf")]) == "validity_only"
    assert (
        failure_category(
            [Issue("missing", "absent", "hh"), Issue("validity", "unsupported", "gf")]
        )
        == "mixed"
    )
    assert failure_category([Issue("other", "error", "output")]) == "other"


@pytest.mark.parametrize("target", ["D11", "slab_weight_shear_with_elasticity"])
def test_heatmap_uses_starting_cohort_not_step_survivors(target):
    """After one of three slabs fails density, another loss is 33%, not 50%."""
    from loss_analysis_utils import plot_loss_heatmap
    import matplotlib.pyplot as plt

    missing = Layer(depth_top=0, thickness=10, grain_form="RG")
    unsupported = Layer(
        depth_top=0, thickness=10, grain_form="IF", density_measured=ufloat(250, 1)
    )
    valid = Layer(
        depth_top=0, thickness=10, grain_form="RG", density_measured=ufloat(250, 1)
    )
    result = analyze_losses(
        [_slab(layer, i) for i, layer in enumerate([missing, unsupported, valid])],
        target,
        progress=False,
    )
    figure = plot_loss_heatmap(result)
    measured = figure.axes[0].images[0].get_array()
    assert measured[0, 0] == pytest.approx(100 / 3)
    emod_step = 1 if target == "D11" else 2
    assert measured[0, emod_step] == pytest.approx(100 / 3)
    assert (
        sum(ax.images[0].get_array().shape[0] for ax in figure.axes if ax.images) == 32
    )
    plt.close(figure)


def test_elastic_shear_matches_weight_without_requiring_depth_and_allows_zero():
    layer = Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1))
    result = analyze_losses(
        [_slab(layer, 0, angle=0)],
        "slab_weight_shear_with_elasticity",
        progress=False,
    )
    direct = result.attempts[result.attempts.density_method == "data_flow"]
    assert direct.success.all()
    assert direct.value.eq(0).all()
    assert result.histogram.loc[8] == 1
    assert "geometry" not in set(result.reasons.parameter)
    figure = plot_histogram(result)
    assert len(figure.axes[0].patches) == 33
    assert "Shear weight with elasticity" in figure.axes[0].get_title()
    import matplotlib.pyplot as plt

    plt.close(figure)


def test_elastic_shear_loses_missing_thickness_or_slope_before_elasticity():
    # PP independently fails Köchle E, but missing geometry is first in the
    # paper's reporting order. Missing thickness must not become "blocked" loss.
    missing_thickness = Layer(grain_form="PP", density_measured=ufloat(250, 1))
    missing_slope = Layer(
        thickness=10, grain_form="PP", density_measured=ufloat(250, 1)
    )
    result = analyze_losses(
        [_slab(missing_thickness, 0), _slab(missing_slope, 1, angle=None)],
        "slab_weight_shear_with_elasticity",
        progress=False,
    )
    direct = result.attempts[result.attempts.density_method == "data_flow"]
    assert set(direct.first_failed_step) == {"slab_weight_shear"}
    assert set(direct.failure_category) == {"missing_only"}
    assert not result.attempts.success.any()
    assert not result.details("elastic_modulus", "kochle").empty
    stages = result.stages[
        result.stages.pathway == "Direct matched density → Köchle → Köchle"
    ]
    assert stages.surviving.tolist() == [2, 0, 0, 0]


def test_cause_bars_keep_overlapping_grain_and_density_failures_separate():
    """One observed layer can violate two limits; neither bar becomes a sum."""
    from loss_analysis_utils import plot_method_causes, plot_stepwise_losses
    import matplotlib.pyplot as plt

    layer = Layer(
        depth_top=0, thickness=10, grain_form="IF", density_measured=ufloat(500, 1)
    )
    result = analyze_losses([_slab(layer, 0)], "D11", progress=False)
    figure = plot_method_causes(result, "elastic_modulus", "bergfeld", "data_flow")
    bars = figure.axes[0].patches
    assert len(bars) == 2
    assert all(b.get_x() == 0 and b.get_width() == 1 for b in bars)
    labels = [tick.get_text() for tick in figure.axes[0].get_yticklabels()]
    assert any("unsupported primary grain form" in label for label in labels)
    assert any(r"363 kg m$^{-3}$" in label for label in labels)
    plt.close(figure)
    with pytest.raises(ValueError, match="Unknown pathway"):
        plot_stepwise_losses(result, "not a pathway")


@pytest.mark.parametrize("method", list(HARDNESS_RANGES))
def test_missing_hardness_bar_combines_grains_without_double_counting(method):
    from loss_analysis_utils import plot_method_causes
    import matplotlib.pyplot as plt

    rounded = Layer(thickness=10, grain_form="RG")
    faceted = Layer(thickness=10, grain_form="FC")
    precipitation = Layer(thickness=10, grain_form="PP")
    slabs = [
        Slab(layers=[rounded, faceted], angle=30, slab_id="mixed", pit_id="pit"),
        _slab(rounded, 1),
        _slab(precipitation, 2),
    ]
    result = analyze_losses(slabs, "slab_weight_shear", progress=False)
    details = result.details("density", method)
    missing = details[
        (details.category == "missing") & (details.field == "hand_hardness")
    ]
    assert len(missing) == 1
    assert missing.iloc[0].slabs == 3 and missing.iloc[0].layers == 3
    assert missing.iloc[0].grain_form == ""
    assert missing.iloc[0].resolved_grain_form == ""
    figure = plot_method_causes(result, "density", method, top_n=1)
    axis = figure.axes[0]
    assert [tick.get_text() for tick in axis.get_yticklabels()] == [
        "Missing observation: hand hardness"
    ]
    assert len(axis.patches) == 1 and axis.patches[0].get_width() == 3
    plt.close(figure)


def test_two_step_weight_preserves_thickness_checks_and_missing_attribution():
    missing_thickness = Layer(grain_form="RG", density_measured=ufloat(250, 1))
    missing_slope = Layer(
        thickness=10, grain_form="RG", density_measured=ufloat(250, 1)
    )
    valid = Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1))
    result = analyze_losses(
        [
            _slab(missing_thickness, 0),
            _slab(missing_slope, 1, angle=None),
            _slab(valid, 2),
        ],
        "slab_weight_shear",
        progress=False,
    )
    stages = result.stages[result.stages.pathway == "Direct matched density"]
    assert stages.step.tolist() == [1, 2]
    assert stages.surviving.tolist() == [3, 1]
    assert stages.missing_only.tolist() == [0, 2]
    direct = result.attempts[result.attempts.density_method == "data_flow"]
    assert direct.first_failed_step.tolist() == [
        "slab_weight_shear",
        "slab_weight_shear",
        "",
    ]
    assert direct.failure_category.tolist() == ["missing_only", "missing_only", ""]
    assert not result.details("slab_weight").empty


def test_stepwise_plot_shows_other_errors_and_reconciles_bar_lengths():
    from loss_analysis_utils import LOSS_COLORS, plot_stepwise_losses
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba

    unknown = Layer(thickness=10, grain_form="RG", hand_hardness="unknown")
    mixed = Layer(thickness=10, grain_form="IF")
    result = analyze_losses(
        [_slab(unknown, 0), _slab(mixed, 1)], "slab_weight_shear", progress=False
    )
    figure = plot_stepwise_losses(result, "Geldsetzer")
    axis = figure.axes[0]
    density_bars = [
        p for p in axis.patches if p.get_y() < 1 < p.get_y() + p.get_height()
    ]
    assert sum(p.get_width() for p in density_bars) == 2
    other = [
        p for p in density_bars if p.get_facecolor() == to_rgba(LOSS_COLORS["other"])
    ]
    assert len(other) == 1 and other[0].get_width() == 1
    mixed_bars = [p for p in density_bars if p.get_hatch()]
    assert len(mixed_bars) == 1 and mixed_bars[0].get_width() == 1
    assert mixed_bars[0].get_facecolor() == to_rgba(LOSS_COLORS["missing_only"])
    assert mixed_bars[0].get_edgecolor() == to_rgba(LOSS_COLORS["validity_only"])
    assert "Other errors" in [t.get_text() for t in figure.legends[0].get_texts()]
    plt.close(figure)


@pytest.mark.parametrize(
    "target", ["slab_weight_shear", "slab_weight_shear_with_elasticity"]
)
def test_horizontal_stepwise_final_target_and_parameter_method_labels(target):
    from loss_analysis_utils import plot_stepwise_losses, LOSS_COLORS
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba

    layer = Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1))
    result = analyze_losses([_slab(layer, 0)], target, progress=False)
    pathway = result.coverage.iloc[0].pathway
    stages = result.stages[result.stages.pathway == pathway]
    figure = plot_stepwise_losses(result, pathway)
    axis = figure.axes[0]
    final_y = len(stages) + 1
    final_bars = [
        p for p in axis.patches if p.get_y() < final_y < p.get_y() + p.get_height()
    ]
    if target == "slab_weight_shear":
        assert not final_bars
        assert not any(t.get_text() == "1\n0 lost (0.0%)" for t in axis.texts)
    else:
        assert len(final_bars) == 1
        assert final_bars[0].get_width() == stages.iloc[-1].surviving == 1
        assert final_bars[0].get_facecolor() == to_rgba(LOSS_COLORS["surviving"])
        assert any(t.get_text() == "1\n0 lost (0.0%)" for t in axis.texts)
    labels = [t.get_text() for t in axis.get_yticklabels()]
    assert len(labels) == len(stages) + (1 if target == "slab_weight_shear" else 2)
    assert "Density" in labels[1] and r"$\rho$" in labels[1]
    assert "(Join:" in labels[2] and "slope angle" in labels[2]
    assert "Shear weight" in labels[-1]
    methods = result.coverage.set_index("pathway").loc[pathway]
    from loss_analysis_utils import METHOD_LABELS

    for column, symbol in [
        ("density_method", r"$\rho$"),
        ("emod_method", "$E$"),
        ("nu_method", r"$\nu$"),
    ]:
        method = methods[column]
        if method:
            assert f"{METHOD_LABELS[method]} ({symbol})" in figure._suptitle.get_text()
            assert not any(METHOD_LABELS[method] in label for label in labels)
    if target == "slab_weight_shear_with_elasticity":
        assert "(Join:" in labels[-1] and "$E$" in labels[-1] and r"$\nu$" in labels[-1]
    plt.close(figure)


def test_stepwise_comparison_shares_scale_and_only_elasticity_has_final_bar():
    from loss_analysis_utils import plot_stepwise_comparison
    import matplotlib.pyplot as plt

    slab = _slab(
        Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1)), 0
    )
    weight = analyze_losses([slab], "slab_weight_shear", progress=False)
    elastic = analyze_losses(
        [slab], "slab_weight_shear_with_elasticity", progress=False
    )
    figure = plot_stepwise_comparison(weight, elastic)
    left, right = figure.axes
    assert left.get_shared_x_axes().joined(left, right)
    assert left.get_xlim() == right.get_xlim() == (0, 1)
    assert left.get_ylim() == right.get_ylim()
    assert left.get_yticks()[-1] == 2 and right.get_yticks()[-1] == 5
    assert not any(p.get_y() < 5 < p.get_y() + p.get_height() for p in left.patches)
    final = [p for p in right.patches if p.get_y() < 5 < p.get_y() + p.get_height()]
    assert len(final) == 1 and final[0].get_width() == 1
    assert any(t.get_text() == "1\n0 lost (0.0%)" for t in right.texts)
    assert len(figure.legends) == 1
    plt.close(figure)


def test_stepwise_loss_percentages_use_starting_cohort_for_every_step():
    from loss_analysis_utils import plot_stepwise_losses
    import matplotlib.pyplot as plt

    measured = Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1))
    slabs = [
        _slab(Layer(thickness=10), 0),
        _slab(measured, 1, angle=None),
        _slab(measured, 2),
    ]
    result = analyze_losses(slabs, "slab_weight_shear", progress=False)
    figure = plot_stepwise_losses(result, "Direct matched density")
    labels = [t.get_text() for t in figure.axes[0].texts]
    assert "2 survive\n1 lost (33.3%)" in labels
    assert "1 survive\n1 lost (33.3%)" in labels
    assert not any("50.0%" in label for label in labels)
    plt.close(figure)


def test_distribution_exports_preserve_zero_bins_percentages_and_inapplicable_cells(
    tmp_path,
):
    from loss_analysis_utils import (
        successful_pathway_table,
        export_successful_pathway_table,
    )
    import pandas as pd

    valid = Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1))
    absent = Layer(thickness=10)
    slabs = [_slab(valid, 0), _slab(absent, 1)]
    weight = analyze_losses(slabs, "slab_weight_shear", progress=False)
    elastic = analyze_losses(slabs, "slab_weight_shear_with_elasticity", progress=False)
    full = successful_pathway_table(weight, elastic)
    assert full.index.tolist() == list(range(33))
    assert full.loc[0, "Shear weight: slabs"] == 1
    assert full.loc[0, "With elasticity: %"] == 50
    assert full.loc[5:, "Shear weight: slabs"].isna().all()
    assert full.loc[32, "With elasticity: slabs"] == 0
    assert (
        full["Shear weight: slabs"].sum() == full["With elasticity: slabs"].sum() == 2
    )
    assert full["Shear weight: %"].sum() == full["With elasticity: %"].sum() == 100
    compact = successful_pathway_table(weight, elastic, compact=True)
    assert compact.index.tolist() == [0, 1, 8]
    paths = export_successful_pathway_table(
        weight, elastic, [tmp_path / "repo", tmp_path / "paper"]
    )
    assert paths[0].read_bytes() == paths[3].read_bytes()
    assert paths[1].read_bytes() == paths[4].read_bytes()
    assert paths[2].read_bytes() == paths[5].read_bytes()
    csv = pd.read_csv(paths[0], index_col=0)
    assert len(csv) == 33 and pd.isna(csv.loc[32, "Shear weight: slabs"])
    tex = paths[1].read_text()
    assert "8 & --- & --- & 1 & 50.00" in tex
    assert "0 & 1 & 50.00 & 1 & 50.00" in tex
    rows = [line for line in tex.splitlines() if line.split(" & ")[0].isdigit()]
    assert [int(line.split(" & ")[0]) for line in rows] == list(range(33))
    assert "32 & --- & --- & 0 & 0.00" in tex


def test_weight_heatmap_has_only_density_and_shear_weight_columns():
    from loss_analysis_utils import plot_loss_heatmap
    import matplotlib.pyplot as plt

    result = analyze_losses(
        [_slab(Layer(thickness=10), 0)], "slab_weight_shear", progress=False
    )
    figure = plot_loss_heatmap(result)
    assert figure.axes[0].images[0].get_array().shape == (4, 2)
    labels = [t.get_text() for t in figure.axes[0].get_xticklabels()]
    assert labels == [r"Density, $\rho$", r"Shear weight, $W_{\mathrm{shear}}$"]
    plt.close(figure)


def test_table_distribution_panels_share_scale_and_align_exact_counts():
    from loss_analysis_utils import plot_pathway_distribution
    import matplotlib.pyplot as plt

    slabs = [
        _slab(Layer(thickness=10, grain_form="RG", density_measured=ufloat(250, 1)), 0),
        _slab(Layer(thickness=10), 1),
    ]
    weight = analyze_losses(slabs, "slab_weight_shear", progress=False)
    elastic = analyze_losses(slabs, "slab_weight_shear_with_elasticity", progress=False)
    figure = plot_pathway_distribution(weight, elastic)
    weight_table, weight_bars, elastic_table, elastic_bars = figure.axes
    assert weight_bars.get_xlim() == elastic_bars.get_xlim()
    assert weight_bars.get_ylim() == elastic_bars.get_ylim()
    for result, tab_ax, bar_ax in [
        (weight, weight_table, weight_bars),
        (elastic, elastic_table, elastic_bars),
    ]:
        assert [
            p.get_width() for p in bar_ax.containers[0].patches
        ] == result.histogram.tolist()
        assert [
            p.get_y() + p.get_height() / 2 for p in bar_ax.containers[0].patches
        ] == pytest.approx(result.histogram.index.tolist())
        assert len([t for t in tab_ax.texts if t.get_text() == "32"]) == 1
    assert (
        len(weight_bars.containers[0].patches) == 5
        and len(elastic_bars.containers[0].patches) == 33
    )
    assert len([t for t in weight_table.texts if t.get_text() == "—"]) == 2 * 28
    plt.close(figure)
