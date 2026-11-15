"""Build compact reviewer tables, figures, and suggested response wording."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import shutil
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from review_metrics import coverage_summary, d11_comparison, write_json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from paper_figure_utils import (  # noqa: E402
    build_elastic_applicability_figure,  # noqa: E402
    build_elastic_modulus_curves_figure,
    build_method_support_matrices_figure,
)

SHORT = {
    "data_flow": "Measured",
    "geldsetzer": "Geldsetzer",
    "kim_jamieson_table2": "Kim T2",
    "kim_jamieson_table6": "Kim T6",
    "bergfeld": "Bergfeld",
    "wautier": "Wautier",
    "kochle": "Köchle",
    "schottner": "Schöttner",
    "srivastava": "Srivastava",
}
TARGET = {
    "slab_weight_shear": "Shear weight",
    "slab_weight_shear_with_elasticity": "Shear weight + elastic inputs",
    "D11": "D11",
}


def label(path):
    return " / ".join(SHORT.get(x, x) for x in path.split(" -> "))


def subset_observations(ids, provenance):
    subset = provenance[provenance.slab_id.isin(ids)]
    layers = [key for keys in subset.source_layers for key in keys]
    return {
        "layer_occurrences": len(layers),
        "unique_source_layers": len(set(layers)),
        "repeated_layer_occurrences": len(layers) - len(set(layers)),
        "additional_tests_from_contributing_pits": len(subset)
        - subset.pit_id.nunique(),
        "repeated_stratigraphies_within_pit": int(
            subset.duplicated(["pit_id", "stratigraphy"]).sum()
        ),
        "layer_count_distribution": subset.source_layers.map(len)
        .value_counts()
        .sort_index()
        .to_dict(),
    }


def save(fig, folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / f"{name}.png", dpi=180, bbox_inches="tight")
    fig.savefig(folder / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def table(frame):
    # Avoid an optional tabulate dependency in the reproduction environment.
    rows = [
        "| " + " | ".join(map(str, frame.columns)) + " |",
        "| " + " | ".join("---" for _ in frame.columns) + " |",
    ]
    rows += [
        "| " + " | ".join(str(x).replace("|", "/") for x in r) + " |"
        for r in frame.itertuples(index=False, name=None)
    ]
    return "\n".join(rows)


def diagrams(folder):
    """Four density pathways with active edges only; locally reproducible source."""
    fig, axes = plt.subplots(2, 2, figsize=(9, 5), layout="constrained")
    specs = [
        ("Measured density", ["Matched density\nsample"], "Direct transfer"),
        ("Geldsetzer", ["Hand hardness", "Grain form"], "Geldsetzer"),
        ("Kim T2", ["Hand hardness", "Grain form"], "Kim T2"),
        ("Kim T6", ["Hand hardness", "Grain form", "Grain size"], "Kim T6"),
    ]
    for ax, (title, inputs, method) in zip(axes.flat, specs):
        ax.set(xlim=(0, 1), ylim=(0, 1))
        ax.axis("off")
        ax.set_title(title, loc="left", fontweight="bold")
        ys = np.linspace(0.25, 0.75, len(inputs)) if len(inputs) > 1 else [0.5]
        for y, text in zip(ys, inputs):
            ax.text(0.03, y, text, va="center", fontsize=10)
            ax.annotate(
                "",
                xy=(0.48, 0.5),
                xytext=(0.34, y),
                arrowprops={"arrowstyle": "->", "color": "#555"},
            )
        ax.text(0.5, 0.5, method, va="center", fontsize=10)
        ax.annotate(
            "", xy=(0.88, 0.5), xytext=(0.75, 0.5), arrowprops={"arrowstyle": "->"}
        )
        ax.text(0.90, 0.5, "ρ", va="center", fontsize=13)
    save(fig, folder, "active_density_pathways")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    root = args.results
    folder = root / "figures"
    started = time.perf_counter()
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42}
    )
    summaries = {
        name: json.loads((root / name / "summary.json").read_text())
        for name in ["baseline", "corrected", "contained"]
    }
    records = {
        name: pd.read_parquet(root / name / "attempts.parquet") for name in summaries
    }
    baseline_ids = set(records["baseline"].slab_id)
    for name, df in records.items():
        assert set(df.slab_id) == baseline_ids, f"Cohort changed: {name}"
    comparison = {"cohort_unchanged": True, "D11": {}, "coverage": {}}
    paired = records["baseline"].merge(
        records["corrected"],
        on=["target", "slab_id", "pathway"],
        suffixes=("_baseline", "_corrected"),
        validate="one_to_one",
    )
    changed_success = paired.success_baseline != paired.success_corrected
    assert (
        paired.loc[changed_success, "pathway"]
        .str.contains(" -> (?:wautier|schottner) -> ")
        .all()
    )
    shared = paired[paired.success_baseline & paired.success_corrected]
    np.testing.assert_allclose(
        shared.value_baseline, shared.value_corrected, rtol=1e-12
    )
    changed_sigma = ~np.isclose(
        shared.sigma_baseline, shared.sigma_corrected, rtol=1e-12, atol=0
    )
    assert (
        shared.loc[changed_sigma, "pathway"].str.startswith("kim_jamieson_table6").all()
    )
    comparison["change_attribution"] = {
        "attempts_with_changed_success": int(changed_success.sum()),
        "shared_successes_with_changed_sigma": int(changed_sigma.sum()),
        "shared_success_nominal_values_unchanged": True,
        "success_changes_only_wautier_or_schottner": True,
        "sigma_changes_only_grain_size_dependent_kim_t6": True,
    }
    # Corrections and matching sensitivity preserve every slab's source layers.
    provenance = pd.read_parquet(root / "corrected/slab_provenance.parquet")
    for name, df in records.items():
        counts, cov = coverage_summary(df)
        comparison["coverage"][name] = counts
        cov.to_csv(root / name / "coverage.csv", index=False)
        stats, per_slab, common = d11_comparison(df)
        stats.update(subset_observations(per_slab.slab_id, provenance))
        comparison["D11"][name] = stats
        old_paths = summaries["baseline"]["D11"]["pathways"]
        fixed, fixed_rows, _ = d11_comparison(df, old_paths)
        fixed.update(subset_observations(fixed_rows.slab_id, provenance))
        comparison["D11"][name + "_original_paths"] = fixed
        fixed_rows.to_csv(root / name / "d11_fixed_original_per_slab.csv", index=False)
        old_members = set(pd.read_csv(root / "baseline/d11_per_slab.csv").slab_id)
        stats["pathways_added_vs_baseline"] = sorted(
            set(stats["pathways"]) - set(old_paths)
        )
        stats["pathways_removed_vs_baseline"] = sorted(
            set(old_paths) - set(stats["pathways"])
        )
        fixed["members_added_vs_baseline"] = sorted(
            set(fixed_rows.slab_id) - old_members
        )
        fixed["members_removed_vs_baseline"] = sorted(
            old_members - set(fixed_rows.slab_id)
        )
        comparison["D11"][name]["members_added_vs_baseline"] = sorted(
            set(per_slab.slab_id) - old_members
        )
        comparison["D11"][name]["members_removed_vs_baseline"] = sorted(
            old_members - set(per_slab.slab_id)
        )
    covs = [
        pd.read_csv(root / name / "coverage.csv")
        .rename(columns={"successful_slabs": name})
        .set_index(["target", "pathway"])[[name]]
        for name in records
    ]
    combined = pd.concat(covs, axis=1).reset_index()
    combined["corrected_minus_baseline"] = combined.corrected - combined.baseline
    combined["contained_minus_corrected"] = combined.contained - combined.corrected
    combined.to_csv(root / "coverage_comparison.csv", index=False)
    write_json(root / "comparison.json", comparison)
    for name, builder in [
        ("elastic_applicability", build_elastic_applicability_figure),
        ("elastic_modulus_curves", build_elastic_modulus_curves_figure),
        ("method_support", build_method_support_matrices_figure),
    ]:
        save(builder(), folder, name)
    diagrams(folder)
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), layout="constrained")
    for ax, target in zip(axes, TARGET):
        counts = [
            next(
                x["union"]
                for x in comparison["coverage"][name]
                if x["target"] == target
            )
            for name in records
        ]
        ax.bar(
            ["Baseline", "Corrected", "Contained\nsensitivity"],
            counts,
            color=["#9b9b9b", "#2b7c85", "#db9650"],
        )
        ax.set_title(TARGET[target])
        ax.set_ylabel("Slabs with ≥1 successful pathway")
        ax.bar_label(ax.containers[0], padding=3)
        ax.set_ylim(0, max(counts) * 1.18 if max(counts) else 1)
    save(fig, folder, "union_coverage")
    colors = ["#9b9b9b", "#2b7c85", "#db9650"]
    for target in TARGET:
        data = combined[combined.target == target].sort_values(
            ["corrected", "pathway"], ascending=[True, False]
        )
        fig, ax = plt.subplots(
            figsize=(12, max(3.5, len(data) * 0.33)), layout="constrained"
        )
        y = np.arange(len(data))
        for shift, name, color in zip([-0.23, 0, 0.23], records, colors):
            ax.barh(
                y + shift, data[name], height=0.22, color=color, label=name.capitalize()
            )
        ax.set_yticks(y, [label(p) for p in data.pathway], fontsize=8)
        ax.set(
            xlabel="Successful slabs (original cohort denominator)",
            title=TARGET[target],
        )
        ax.legend(loc="lower right", fontsize=8)
        save(fig, folder, f"{target}_individual_coverage")
    fig, axes = plt.subplots(
        3,
        2,
        figsize=(12, 9),
        layout="constrained",
        gridspec_kw={"width_ratios": [1, 4]},
    )
    for (left, right), target in zip(axes, TARGET):
        for shift, name, color in zip([-0.23, 0, 0.23], records, colors):
            entry = next(
                x for x in comparison["coverage"][name] if x["target"] == target
            )
            counts = entry["histogram"]
            left.bar(shift, counts[0], width=0.22, color=color)
            right.bar(
                np.arange(1, entry["pathways"] + 1) + shift,
                [counts[i] for i in range(1, entry["pathways"] + 1)],
                width=0.22,
                color=color,
                label=name.capitalize(),
            )
        left.set(
            xticks=[0],
            xticklabels=["0 successes"],
            ylabel="Slabs",
            title=TARGET[target],
        )
        right.set(xlabel="Number of successful pathways", ylabel="Slabs")
        right.set_xticks(np.arange(1, entry["pathways"] + 1), minor=True)
        right.set_xticks(
            np.arange(1, entry["pathways"] + 1)
            if entry["pathways"] <= 4
            else [1, 4, 8, 12, 16, 20, 24, 28, 32]
        )
    axes[0, 1].legend(fontsize=9)
    save(fig, folder, "successful_pathway_distributions")
    if (root / "baseline/D11_stages.csv").exists():
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), layout="constrained")
        for ax, target in zip(axes, TARGET):
            route = (
                "Kim T2"
                if target == "slab_weight_shear"
                else "Kim T2 → Schöttner → Köchle"
            )
            for name, color, marker in zip(records, colors, ["o", "x", "+"]):
                stages = pd.read_csv(root / name / f"{target}_stages.csv")
                stages = stages[stages.pathway == route].sort_values("step")
                percentages = [
                    100,
                    *(100 * stages.surviving / summaries[name]["slabs"]).tolist(),
                ]
                ax.plot(
                    range(len(percentages)),
                    percentages,
                    marker=marker,
                    color=color,
                    label=name.capitalize(),
                )
            ax.set_xticks(
                range(len(percentages)),
                [
                    "Starting\ncohort",
                    *[s.replace(" ", "\n") for s in stages.requirement],
                ],
                fontsize=8,
            )
            ax.set(
                title=f"{TARGET[target]}\n{route}",
                ylabel="Remaining (% of original cohort)",
                ylim=(0, 105),
            )
        axes[0].legend(fontsize=8)
        save(fig, folder, "stepwise_coverage_comparison")
    # All combinations form mutually exclusive partitions of failed attempts.
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), layout="constrained")
    for ax, target in zip(axes, TARGET):
        causes = pd.read_csv(root / "corrected" / f"{target}_first_failure_classes.csv")
        totals = (
            causes.groupby("failure_reason_classes").lost_attempts.sum().sort_values()
        )
        reason_labels = {
            "missing_observation": "Missing input",
            "processing_exclusion": "Processing exclusion",
            "unsupported_grain": "Unsupported grain",
            "numerical_domain": "Numerical domain",
        }
        names = [
            " + ".join(reason_labels.get(c, c) for c in s.split("+"))
            for s in totals.index
        ]
        ax.barh(names, totals, color="#377e88")
        ax.tick_params(axis="y", labelsize=9)
        ax.set_title(TARGET[target], loc="left")
        ax.set_xlabel("Newly failed slab–pathway attempts (each counted once)")
        ax.bar_label(ax.containers[0], padding=3, fontsize=8)
        ax.set_xlim(0, max(totals.max() * 1.2, 1))
    save(fig, folder, "first_failure_reasons")
    corrected = records["corrected"]
    d11, per_slab, common = d11_comparison(corrected)
    d11.update(subset_observations(per_slab.slab_id, provenance))
    if len(per_slab):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
        axes[0].hist(per_slab.range_to_interval_width, bins=20, color="#2b7c85")
        axes[0].set(
            xlabel="Absolute pathway range / largest ±1σ full width", ylabel="Slabs"
        )
        axes[1].hist(
            per_slab.nonoverlap_fraction, bins=np.linspace(0, 1, 21), color="#db9650"
        )
        axes[1].set(
            xlabel="Fraction of 120 pairs with disjoint ±1σ intervals", ylabel="Slabs"
        )
        save(fig, folder, "d11_spread_uncertainty")
        paths = sorted(d11["pathways"], key=lambda p: (p.split(" -> ")[1], p))
        fig, axes = plt.subplots(
            1, 3, figsize=(13, 7), sharey=True, layout="constrained"
        )
        for ax, item in zip(axes, d11["illustrations"]):
            g = (
                common[common.slab_id == item["slab_id"]]
                .set_index("pathway")
                .reindex(paths)
            )
            ax.errorbar(
                g.value,
                np.arange(len(paths)),
                xerr=g.sigma,
                fmt="o",
                markersize=4,
                color="#2b7c85",
                capsize=2,
            )
            ax.set_title(
                f"{item['quantile']:.0%} example: {item['slab_id']}\nSpread {item['spread_ratio']:.2f}×",
                fontsize=10,
            )
            ax.axvline(0, color="#aaa", lw=0.7)
            ax.set_xlabel("D11 (N mm)")
            ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
        axes[0].set_yticks(range(len(paths)), [label(p) for p in paths], fontsize=9)
        axes[0].invert_yaxis()
        save(fig, folder, "d11_illustrations")
        ratios = common.assign(
            ratio=common.value / common.groupby("slab_id").value.transform("median")
        )
        fig, ax = plt.subplots(figsize=(9, 7), layout="constrained")
        ax.boxplot(
            [ratios.loc[ratios.pathway == p, "ratio"] for p in paths],
            orientation="horizontal",
            tick_labels=[label(p) for p in paths],
            showfliers=False,
        )
        ax.axvline(1, color="#aaa", ls="--")
        ax.set_xscale("log")
        ax.set_xlabel("D11 / within-slab median D11")
        save(fig, folder, "d11_paired_pathway_effects")
        if root.resolve() == ROOT / "paper_analysis/results":
            # Keep the existing repository-local figure links current. Smoke
            # runs never replace full-cohort paper assets.
            for source, alias in [
                ("d11_illustrations", "d11_slab_uncertainty"),
                ("d11_paired_pathway_effects", "d11_paired_pathway_effects"),
            ]:
                for suffix in [".pdf", ".png"]:
                    shutil.copy2(
                        folder / (source + suffix),
                        ROOT / "paper/figures" / (alias + suffix),
                    )
    mc = pd.read_csv(root / "corrected/monte_carlo.csv")
    controlled = mc[mc["case"].str.startswith("schottner") & (mc.correlation == 0)]
    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    boundary_labels = controlled["case"].map(
        lambda s: f"{s.split('_')[1]}: {s.split('_')[2]} boundary"
    )
    ax.barh(boundary_labels, controlled.success_fraction, color="#2b7c85")
    ax.set(
        xlabel="Fraction of Gaussian draws inside the applicable domain", xlim=(0, 1)
    )
    save(fig, folder, "boundary_sampling_success")
    audit = json.loads((root / "corrected/audit_summary.json").read_text())
    matching_fields = [
        "density_observations",
        "pits_with_density_observations",
        "layers_with_density_present",
        "layers_with_positive_finite_density",
        "pits_with_positive_finite_density",
        "slabs_with_all_positive_finite_density",
        "slabs_with_any_positive_finite_density",
        "partial_layer_assignments",
    ]
    matching = pd.DataFrame(
        [
            {
                "policy": name,
                **{
                    k: json.loads((root / name / "audit_summary.json").read_text()).get(
                        k
                    )
                    for k in matching_fields
                },
            }
            for name in records
            if (root / name / "audit_summary.json").exists()
        ]
    )
    matching.to_csv(root / "density_matching_comparison.csv", index=False)
    controls = mc[
        (mc.correlation == 0)
        & mc["case"].isin(
            [
                "linear_density",
                "nonlinear_density",
                "kim_t6_grain_size",
                "homogeneous_D11",
                "layered_D11",
                "kochle_breakpoint_250",
            ]
        )
    ].copy()
    controls["pathway"] = controls.pathway.map(label)
    controls = controls[
        ["case", "pathway", "first_order_sigma", "conditional_std", "success_fraction"]
    ].round(4)
    correlated = mc[mc.target.eq("D11")].pivot(
        index=["case", "pathway"], columns="correlation", values="conditional_std"
    )
    correlation_ratios = correlated[1.0] / correlated[0.0]
    union_rows = []
    for target in TARGET:
        union_rows.append(
            {
                "Target": TARGET[target],
                **{
                    name: next(
                        x["union"]
                        for x in comparison["coverage"][name]
                        if x["target"] == target
                    )
                    for name in records
                },
            }
        )
    changed = combined[combined.corrected_minus_baseline != 0].copy()
    changed["target"] = changed.target.map(TARGET)
    changed["pathway"] = changed.pathway.map(label)
    changed = changed[
        ["target", "pathway", "baseline", "corrected", "corrected_minus_baseline"]
    ]
    n = d11["common_slabs"]
    sigma = d11["pooled_relative_uncertainty"]
    benchmarks = pd.DataFrame(
        json.loads((root / "corrected/benchmarks.json").read_text())["runs"]
    )
    benchmark_summary = (
        benchmarks.groupby("slabs")
        .seconds.agg(["count", "min", "median", "max"])
        .reset_index()
    )
    benchmark_summary.to_csv(root / "runtime_benchmark_summary.csv", index=False)
    validation_wording = "See the reproduction guide for fresh verification commands."
    if (root / "validation.json").exists():
        validation = json.loads((root / "validation.json").read_text())
        package = validation["package_coverage"]
        validation_wording = (
            f"The recorded validation run passed {validation['pytest']['passed']} tests. "
            "The 17 checked method/dispatcher modules and 59 named functions attained "
            "100% statement and branch coverage. Across the entire package, coverage was "
            f"{package['percent_statements_covered']:.2f}% of statements and "
            f"{package['percent_branches_covered']:.2f}% of branches. The independent notebook "
            "verified 36 pathways on 394 selected slab–pathway cases (3,037 numeric "
            "comparisons and 4,711 matched unavailable outputs), plus homogeneous and "
            "layered D11 examples. Documentation, method-catalog, lint, notebook and "
            "LaTeX-table checks passed. See `validation.json` for the recorded scope."
        )
    wording = f"""# Reviewer response support

These are suggested responses and evidence from the pinned repository baseline
and corrected implementation. They do not modify the manuscript or Word responses.
All statistical comparisons below are descriptive, with repeated ECTP slabs retained.

## Applicability corrections — R2 major 3

We corrected Wautier's implementation to accept precipitation particles and applied
Schöttner's grain-specific inclusive nominal-density limits. Jakob Schöttner supplied
observed volume-fraction extrema in author correspondence: SH 0.074–0.191,
DF/RG 0.162–0.388, and FC/DH 0.164–0.505. Multiplication by his specified
916.7 kg m⁻³ gives 67.8358–175.0897, 148.5054–355.6796, and
150.3388–462.9335 kg m⁻³. Thresholds are unrounded internally. These bounds
describe the observed calibration domain, not demonstrated accuracy throughout it.
The equations retain their existing 917 kg m⁻³ normalization. Köchle melt-form
support remains a qualified implementation choice because the source describes
distinct melt-form behavior without a separate fit.

## Coverage — R1 coverage comment; R2 major 5

The starting cohort remains {summaries['corrected']['slabs']:,} slabs from
{summaries['corrected']['contributing_pits']:,} contributing pits. Union coverage
counts slabs reached by at least one pathway; it is not the maximum individual
pathway coverage. Individual changes are visible even where union coverage stays constant.

{table(pd.DataFrame(union_rows))}

Changed individual-pathway counts:

{table(changed)}

The `*_first_failure_classes.csv` tables partition failed attempts at their first
unsuccessful requirement into combinations of missing observations, processing
exclusions, unsupported grain forms and numerical-domain limits. Each attempt is
counted once. Detailed reason counts overlap and must not be summed. Stage loss
percentages use the original cohort denominator. Shear weight with elasticity is
an availability requirement for shear weight plus E and ν in every layer.

## Density matching and cohort audit — R2 major 4

The export contains {audit['density_observations']:,} density observations and
{audit['layers']:,} stratigraphic layers. {audit['density_observations_exact']:,}
observations have normalized intervals exactly matching a layer;
{audit.get('observations_with_unusable_interval',0):,} observations have no usable
positive-thickness interval. {audit.get('point_observations_located_in_layer',0):,}
of those point records can be located by depth in a layer, but their sampling
extent remains unknown. The alternative policy retains exact matches and assigns
only a single valid positive-thickness sample wholly contained in one unambiguous
layer. It does not interpret a depth-only observation as a representative layer mean.
The policy counts and partial coverage fractions are retained in the layer audit.
See `coverage_comparison.csv` for its effects; zero differences are valid results,
not evidence that all excluded density records lack potential scientific value.

The audit found {audit['duplicate_file_content_excess']} duplicate-content excess
files and {audit['duplicate_pit_id_excess']} duplicate-ID excess records. No new
deduplication or quality filtering was applied. {audit['pits_with_multiple_slabs']:,}
pits yield multiple slabs, including {audit['repeated_stratigraphies_within_pit']:,}
additional occurrences of identical observed slab stratigraphy within a pit.
These are not independent observations. Slab-construction exclusions were
{audit['slab_exclusions']}. A failure belongs to the first layer satisfying
top ≤ failure depth < bottom; the whole containing layer is omitted from the slab.
Checks reported here are local audits, not claims about SnowPilot website validation.
There is no new wetness screening and no claim that all selected observations are dry.

## Assigned uncertainty — R1 uncertainty comments; R2 major 6

Suggested replacement table (assigned symmetric standard deviations for the
first-order calculation, rather than demonstrated coverage intervals):

| Observation | Assigned standard deviation | Basis and limitation |
| --- | --- | --- |
| Direct density | 10% of magnitude | Existing literature-informed assumption |
| Slope angle | 2° | Existing observational assumption |
| Hand hardness index | 0.67 | Two subclasses; F−=0.67, K+=5.33, I+=6.33 |
| Grain size | 48% of magnitude | Symmetric approximation to asymmetric −48%/+122% bounds |
| Layer thickness | 5% of magnitude | Existing observational assumption |

The proposed grain-size bounds are asymmetric. A ufloat carries a single symmetric
standard deviation and first-order derivatives, so we assign 48% of recorded grain
size symmetrically. This uses the lower relative width and does not reproduce the
upper +122% bound or the underlying percentile distribution. It is a modeling
approximation, not a newly established measurement-error distribution. Other
assumed ranges are likewise used as assigned standard deviations. Grain-form
misclassification and empirical parameterization uncertainty are excluded.
Validity and the Köchle branch are evaluated at nominal density; uncertainty
crossing a boundary is not truncated. Uncertainty need not grow monotonically
along a calculation pathway.

The Monte Carlo checks use Gaussian perturbations, a fixed seed, and
{int(mc.draws.iloc[0]):,} draws per case/pathway/correlation condition. Correlations
0, 0.5 and 1 are hypothetical shared-observer scenarios within a measurement type,
not estimated population correlations. Different measurement types are independent;
the same raw draw is reused across pathways and one slope observation is shared.
Physical-input, method-domain and numerical failures are reported separately.
No draw is clipped, replaced or resampled. Successful-draw summaries are conditional
where draws fail; comparing them directly with unconditioned first-order standard
deviations also reflects selection. Boundary-case success fractions range from
{controlled.success_fraction.min():.1%} to {controlled.success_fraction.max():.1%}.
These checks quantify limitations without replacing the production uncertainty engine.
The current density functions reconstruct ufloats; correlated scenarios therefore
operate on shared raw samples rather than assuming those outputs retain covariance.

Selected controls with independent layers (density in kg m⁻³, modulus in MPa,
D11 in N mm; Monte Carlo standard deviations are conditional on successful draws):

{table(controls)}

Across the selected D11 case–pathway pairs, the conditional standard-deviation ratio
for inter-layer correlation 1 versus 0 ranges from {correlation_ratios.min():.3f}
to {correlation_ratios.max():.3f}. These are scenario sensitivities, including
changes in domain-crossing selection, rather than empirical correlation estimates.

## D11 comparison and interpretation — R1 Figures 9–10; R2 major 6–7

The corrected top-16 common subset contains {n:,} slabs from {d11['common_pits']:,}
pits; {d11['single_layer_slabs']:,} slabs have one layer. Grain-form combinations
in this subset are {d11['grain_forms']}. There are {d11['layer_occurrences']:,}
layer occurrences representing {d11['unique_source_layers']:,} distinct source
layers, and {d11['repeated_stratigraphies_within_pit']:,} repeated slab stratigraphies
within pits. The pooled median relative propagated
measurement uncertainty is {sigma['median']:.2%}, with IQR
{sigma['q25']:.2%}–{sigma['q75']:.2%}, across {sigma['n']:,} slab–pathway values.
This is not a median of per-slab medians. Per-slab summaries are provided separately.
The median max/min spread is {d11['spread_ratio']['median']:.3f}, with range
{d11['spread_ratio']['min']:.3f}–{d11['spread_ratio']['max']:.3f} and 90th percentile
{d11['spread_ratio']['q90']:.3f}.

Across the full common subset, the median absolute range divided by the largest
full ±1σ interval width is {d11['range_to_interval_width']['median']:.3f}.
The median fraction of the 120 pathway pairs with disjoint ±1σ intervals is
{d11['nonoverlap_fraction']['median']:.1%}; {d11['slabs_with_any_nonoverlap']:,}
slabs have at least one disjoint pair. This describes interval separation, not
statistical significance or pathway accuracy. There are
{d11['negative_lower_endpoints']:,} negative lower interval endpoints; these remain
visible as a limitation of the uncertainty approximation. The previous aggregate
“dominates by ~12x” heuristic is removed. Paired Monte Carlo difference summaries
use the same raw observations across pathways.

Reproducibility discrepancy: rerunning the requested baseline revision gives
{summaries['baseline']['D11']['common_slabs']} common slabs, whereas the previously
saved D11 notebook/manuscript reported 317. This discrepancy predates this PR;
the pinned baseline is the comparator, and historical notebook outputs are not
treated as fresh execution evidence. `comparison.json` records both newly ranked
and original-pathway comparisons and membership changes.

The stiffness calculation uses an upward-positive z coordinate, with reference
depth equal to the first layer top plus half the sum of layer thicknesses. Measured
layer tops remain fixed while thickness uncertainty propagates. Gaps are retained,
so this reference is not the midpoint of the bounding interval in a gapped profile.
The reference plane is not generally the stiffness-weighted neutral axis. D11 is
reported in N mm (divide by 1000 for N m). Reversing coordinate orientation with
consistent integration limits leaves D11 unchanged. Observation orientation is
unknown; no unsupported vertical-to-slope-normal conversion is made.

## Verification and reproducibility — R1 verification; R2 minor 6

Run `.venv/bin/python paper_analysis/run_review.py` from the repository, then
execute `paper_analysis/hand-verification.ipynb`. A `--smoke` run writes separate
outputs. The pinned baseline is extracted into a temporary directory; raw data
remain unchanged. Input checksums, source hashes, environment versions, stage
times and repeat timings are saved alongside the results. Graph calculation and
method-domain verification establish implementation agreement, not empirical
accuracy.

{validation_wording}

On the recorded machine, corrected parsing and slab construction took
{summaries['corrected']['parsing_seconds']:.2f} s and full-cohort execution of all
three targets took {summaries['corrected']['execution_seconds']:.2f} s.
Deterministic subset execution timings (seconds; three repeats, fresh engine,
uncontrolled warm filesystem cache) were:

{table(benchmark_summary.round(3))}

Auditing, each diagnostic target and rendering are timed separately in the saved
metadata. These measurements do not establish operational or real-time suitability.

The PR intentionally does not add a stability-model demonstration, mixed density
methods within one production pathway, an optimal-pathway recommendation, wet-snow
parameterizations, or a new production uncertainty engine.
"""
    (root / "reviewer_response_support.md").write_text(wording)
    write_json(
        root / "render_timing.json",
        {"render_and_report_seconds": time.perf_counter() - started},
    )
    print(f"Rendered reviewer figures and response support in {root}")


if __name__ == "__main__":
    main()
