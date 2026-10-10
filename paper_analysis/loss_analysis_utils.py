"""Reproducible slab coverage and loss diagnostics for the paper notebook.

ExecutionEngine remains the source of calculated values. Diagnostics inspect
original observations, actual pathway outputs, and the implemented validity
checks rather than trying to infer causes from generic error messages.

The domain tables below mirror methods/layer/{density,elastic_modulus,
poissons_ratio}.py. Boundary tests compare them with the method implementations.
No density interval is imposed on Schöttner, and no grain-size interval is
invented for Kim T6. A layer count refers to distinct source Layer objects;
multiple ECTP slabs can contain the same observed layer.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd

from snowpyt_mechparams.constants import resolve_grain_form_for_method
from snowpyt_mechparams.execution import ExecutionConfig, ExecutionEngine
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.models import Layer, Slab
from snowpyt_mechparams.pathway import find_parameterizations

HARDNESS_RANGES = {
    "geldsetzer": {
        "PP": (0.67, 4.00),
        "PPgp": (0.67, 4.00),
        "DF": (0.67, 4.33),
        "RG": (1.00, 5.33),
        "FC": (0.67, 4.67),
        "DH": (1.00, 5.00),
    },
    "kim_jamieson_table2": {
        "PP": (0.67, 4.00),
        "PPgp": (0.67, 4.00),
        "DF": (0.67, 4.67),
        "RG": (0.67, 5.33),
        "RGxf": (0.67, 4.33),
        "FC": (0.67, 5.00),
        "FCxr": (0.67, 5.33),
        "DH": (1.00, 5.00),
        "MFcr": (2.00, 5.33),
    },
    "kim_jamieson_table6": {
        "FC": (1.67, 4.00),
        "FCxr": (2.33, 4.33),
        "PP": (0.67, 2.00),
        "PPgp": (1.00, 3.33),
        "DF": (1.00, 3.00),
        "MF": (2.33, 4.33),
    },
}
GRAIN_DOMAINS = {
    ("elastic_modulus", "bergfeld"): {"PP", "RG", "DF"},
    ("elastic_modulus", "kochle"): {"RG", "FC", "DH", "MF"},
    ("elastic_modulus", "wautier"): {"DF", "RG", "FC", "DH", "MF"},
    ("elastic_modulus", "schottner"): {"DF", "RG", "FC", "DH", "SH"},
    ("poissons_ratio", "kochle"): {"RG", "FC", "DH"},
    ("poissons_ratio", "srivastava"): {"RG", "PP", "DF", "FC", "DH"},
}
DENSITY_RANGES = {
    "bergfeld": (110.0, 363.0),
    "kochle": (150.0, 450.0),
    "wautier": (103.0, 544.0),
}
METHOD_LABELS = {
    "data_flow": "Measured",
    "geldsetzer": "Geldsetzer",
    "kim_jamieson_table2": "Kim T2",
    "kim_jamieson_table6": "Kim T6",
    "bergfeld": "Bergfeld",
    "kochle": "Köchle",
    "wautier": "Wautier",
    "schottner": "Schöttner",
    "srivastava": "Srivastava",
}
STEPS = {
    "slab_weight_shear": (
        ("density", "Density"),
        ("slab_weight", "Thickness / integrated weight"),
        ("slab_weight_shear", "Slope / shear weight"),
    ),
    "D11": (
        ("density", "Density"),
        ("elastic_modulus", "Young's modulus"),
        ("poissons_ratio", "Poisson's ratio"),
        ("geometry", "Layer geometry"),
        ("D11", "D11 calculation"),
    ),
}


def nominal(value: Any) -> float:
    """Read the nominal value without substituting a missing observation."""
    try:
        return float(getattr(value, "nominal_value", value))
    except (TypeError, ValueError):
        return math.nan


def finite(value: Any) -> bool:
    return math.isfinite(nominal(value))


@dataclass(frozen=True)
class Issue:
    """One independently identifiable constraint on a method or observation."""

    category: str  # missing, validity, blocked, other
    reason: str
    field: str
    grain_form: str = ""
    resolved_grain_form: str = ""
    observed: Any = None
    lower: float | None = None
    upper: float | None = None
    interval: str = ""
    unit: str = ""


def _observation(value: Any, field: str, unit: str = "") -> list[Issue]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return [Issue("missing", "absent observation", field, unit=unit)]
    if not isinstance(value, str) and not finite(value):
        return [Issue("missing", "nonfinite observation", field, unit=unit)]
    return []


def _range_issues(
    value: Any,
    field: str,
    lower: float | None,
    upper: float | None,
    grain_form: str,
    resolved: str,
    unit: str,
    lower_inclusive: bool = True,
) -> list[Issue]:
    if not finite(value):
        return []  # Missing or blocked input is diagnosed separately.
    n = nominal(value)
    interval = f"{'[' if lower_inclusive else '('}{lower if lower is not None else '-inf'}, {upper if upper is not None else 'inf'}]"
    low = lower is not None and (n < lower if lower_inclusive else n <= lower)
    high = upper is not None and n > upper
    return (
        [
            Issue(
                "validity",
                "below lower bound" if low else "above upper bound",
                field,
                grain_form,
                resolved,
                n,
                lower,
                upper,
                interval,
                unit,
            )
        ]
        if low or high
        else []
    )


def diagnose_layer(
    layer: Layer,
    parameter: str,
    method: str,
    density: Any = None,
    output: Any = None,
    error: str | None = None,
) -> list[Issue]:
    """Inspect all evaluable constraints, even if another input blocks a call.

    ``density`` must be the output of this pathway's selected density method.
    A missing computed density is blocked upstream, not a missing observation.
    A present grain form that cannot resolve to a supported form is validity loss.
    """
    issues: list[Issue] = []
    raw = layer.grain_form or ""
    resolved = ""
    if parameter == "density" and method == "data_flow":
        issues.extend(_observation(layer.density_measured, "density_measured", "kg/m³"))
    else:
        issues.extend(_observation(layer.grain_form, "grain_form"))
        resolved = (
            resolve_grain_form_for_method(raw, method) or ""
            if parameter == "density"
            else raw[:2].upper()
        )
        supported = (
            resolved in HARDNESS_RANGES[method]
            if parameter == "density"
            else resolved in GRAIN_DOMAINS[(parameter, method)]
        )
        if raw and not supported:
            issues.append(
                Issue(
                    "validity",
                    "unsupported grain form",
                    "grain_form",
                    raw,
                    resolved,
                    raw,
                )
            )
        if parameter == "density":
            issues.extend(_observation(layer.hand_hardness, "hand_hardness"))
            hhi = layer.hand_hardness_index
            if layer.hand_hardness and hhi is None:
                issues.append(
                    Issue(
                        "other",
                        "unrecognized hardness code",
                        "hand_hardness",
                        raw,
                        resolved,
                        layer.hand_hardness,
                    )
                )
            if supported:
                low, high = HARDNESS_RANGES[method][resolved]
                issues.extend(
                    _range_issues(
                        hhi, "hand_hardness_index", low, high, raw, resolved, "index"
                    )
                )
            if method == "kim_jamieson_table6":
                issues.extend(_observation(layer.grain_size_avg, "grain_size", "mm"))
        else:
            needs_density = parameter == "elastic_modulus" or method == "srivastava"
            if needs_density:
                if density is None:
                    issues.append(
                        Issue("blocked", "density step unsuccessful", "density")
                    )
                elif not finite(density):
                    issues.append(
                        Issue("blocked", "density output nonfinite", "density")
                    )
                if parameter == "elastic_modulus" and method in DENSITY_RANGES:
                    low, high = DENSITY_RANGES[method]
                    issues.extend(
                        _range_issues(
                            density, "density", low, high, raw, resolved, "kg/m³"
                        )
                    )
                elif method == "srivastava":
                    issues.extend(
                        _range_issues(
                            density,
                            "density",
                            200.0,
                            580.0 if resolved == "RG" else None,
                            raw,
                            resolved,
                            "kg/m³",
                            lower_inclusive=False,
                        )
                    )
    if not finite(output) and not issues:
        issues.append(
            Issue("other", error or "nonfinite or absent method output", "output")
        )
    return [
        replace(issue, grain_form=raw, resolved_grain_form=resolved) for issue in issues
    ]


def _geometry_issues(layer: Layer, require_depth: bool) -> list[Issue]:
    issues = _observation(layer.thickness, "thickness", "cm")
    if require_depth:
        issues += _observation(layer.depth_top, "depth_top", "cm")
    return issues


def failure_category(issues: list[Issue]) -> str:
    """Exclusive category for a newly lost slab; detailed reasons can overlap."""
    categories = {i.category for i in issues}
    if categories - {"missing", "validity"}:
        return "other"  # Retain blocked/other causes in the detailed tables.
    if categories == {"missing", "validity"}:
        return "mixed"
    if categories == {"missing"}:
        return "missing_only"
    if categories == {"validity"}:
        return "validity_only"
    return "other"


class _CauseCounter:
    """Stream distinct slab/layer counts; do not retain millions of traces."""

    def __init__(self) -> None:
        self.details: dict[tuple, dict] = {}
        self.summary: dict[tuple, dict] = {}

    @staticmethod
    def _bucket() -> dict:
        return {
            "slabs": set(),
            "layers": set(),
            "minimum": math.inf,
            "maximum": -math.inf,
            "examples": set(),
        }

    def add(
        self,
        slab_index: int,
        layer: Layer | None,
        parameter: str,
        method: str,
        context: str,
        issue: Issue,
    ) -> None:
        summary_key = (parameter, method, context, issue.category)
        detail_key = summary_key + (
            issue.reason,
            issue.field,
            issue.grain_form,
            issue.resolved_grain_form,
            issue.lower,
            issue.upper,
            issue.interval,
            issue.unit,
        )
        for mapping, key in [(self.details, detail_key), (self.summary, summary_key)]:
            bucket = mapping.setdefault(key, self._bucket())
            bucket["slabs"].add(slab_index)
            if layer is not None:
                bucket["layers"].add(id(layer))
            if finite(issue.observed):
                n = nominal(issue.observed)
                bucket["minimum"] = min(bucket["minimum"], n)
                bucket["maximum"] = max(bucket["maximum"], n)
            elif issue.observed is not None and len(bucket["examples"]) < 5:
                bucket["examples"].add(str(issue.observed))

    def frames(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        base = ["parameter", "method", "density_context", "category"]
        extra = [
            "reason",
            "field",
            "grain_form",
            "resolved_grain_form",
            "lower",
            "upper",
            "interval",
            "unit",
        ]
        frames = []
        for mapping, columns in [(self.details, base + extra), (self.summary, base)]:
            rows = []
            for key, bucket in mapping.items():
                row = dict(zip(columns, key))
                row.update(slabs=len(bucket["slabs"]), layers=len(bucket["layers"]))
                if mapping is self.details:
                    row.update(
                        observed_min=bucket["minimum"]
                        if bucket["minimum"] != math.inf
                        else None,
                        observed_max=bucket["maximum"]
                        if bucket["maximum"] != -math.inf
                        else None,
                        observed_examples=", ".join(sorted(bucket["examples"])),
                    )
                rows.append(row)
            count_columns = ["slabs", "layers"]
            value_columns = (
                ["observed_min", "observed_max", "observed_examples"]
                if mapping is self.details
                else []
            )
            frame = pd.DataFrame(rows, columns=columns + count_columns + value_columns)
            if not frame.empty:
                frame = frame.sort_values(
                    base
                    + (
                        ["field", "reason", "grain_form"]
                        if mapping is self.details
                        else []
                    )
                ).reset_index(drop=True)
            frames.append(frame)
        return frames[0], frames[1]


@dataclass
class LossAnalysis:
    target: str
    n_slabs: int
    n_pathways: int
    attempts: pd.DataFrame
    stages: pd.DataFrame
    reasons: pd.DataFrame
    method_summary: pd.DataFrame
    histogram: pd.Series
    coverage: pd.DataFrame

    def details(
        self,
        parameter: str,
        method: str | None = None,
        density_context: str | None = None,
    ) -> pd.DataFrame:
        """Select a readable method detail table; all causes remain available."""
        frame = self.reasons[self.reasons.parameter == parameter]
        if method is not None:
            frame = frame[frame.method == method]
        if density_context is not None:
            frame = frame[frame.density_context == density_context]
        return frame.drop(columns=["parameter"]).reset_index(drop=True)


def _path_label(methods: dict[str, str], target: str) -> str:
    parameters = (
        ["density"]
        if target == "slab_weight_shear"
        else ["density", "elastic_modulus", "poissons_ratio"]
    )
    return " → ".join(METHOD_LABELS[methods[p]] for p in parameters)


def analyze_losses(
    slabs: list[Slab], target: str, progress: bool = True
) -> LossAnalysis:
    """Execute every pathway and accumulate attributable and overlapping loss.

    Reporting order is an explicit slab-level funnel, not an assertion that
    independent branches execute serially. Method counts deduplicate shared
    branches across pathways and physical observations shared by ECTP slabs.
    """
    if target not in STEPS:
        raise ValueError(f"Supported targets: {tuple(STEPS)}")
    if not slabs:
        raise ValueError("The slab cohort is empty")
    pathways = find_parameterizations(default_graph, default_graph.get_node(target))
    engine = ExecutionEngine()
    config = ExecutionConfig(include_method_uncertainty=False)
    causes = _CauseCounter()
    rows = []
    iterator = enumerate(slabs)
    if progress:
        from tqdm.auto import tqdm

        iterator = tqdm(
            iterator, total=len(slabs), desc=target, unit="slab", mininterval=5
        )
    step_parameters = [p for p, _ in STEPS[target]]
    for slab_index, slab in iterator:
        results = engine.execute_all(slab, target, config=config, pathways=pathways)
        # A method shared by multiple pathways is diagnosed only once per slab
        # and upstream context. Source objects remain alive throughout this run.
        diagnosed: dict[tuple, tuple[bool, list[Issue]]] = {}
        for pathway in results.pathways.values():
            methods = pathway.methods_used
            density_method = methods["density"]
            traces = {
                (t.parameter, t.layer_index): t for t in pathway.computation_trace
            }
            stage_issues: dict[str, list[Issue]] = defaultdict(list)
            ready = {}
            for parameter in ["density"] + (
                ["elastic_modulus", "poissons_ratio"] if target == "D11" else []
            ):
                method = methods[parameter]
                context = (
                    density_method
                    if parameter == "elastic_modulus" or method == "srivastava"
                    else ""
                )
                cache_key = (parameter, method, context)
                if cache_key not in diagnosed:
                    parameter_ok = bool(slab.layers)
                    parameter_issues = []
                    for layer_index, source_layer in enumerate(slab.layers):
                        trace = traces[(parameter, layer_index)]
                        density_trace = traces[("density", layer_index)]
                        issues = diagnose_layer(
                            source_layer,
                            parameter,
                            method,
                            density=density_trace.output,
                            output=trace.output,
                            error=trace.error,
                        )
                        parameter_ok &= (
                            trace.success and finite(trace.output) and not issues
                        )
                        parameter_issues.extend(issues)
                        for issue in issues:
                            causes.add(
                                slab_index,
                                source_layer,
                                parameter,
                                method,
                                context,
                                issue,
                            )
                    diagnosed[cache_key] = (parameter_ok, parameter_issues)
                ready[parameter], stage_issues[parameter] = diagnosed[cache_key]

            # Geometry and target prerequisites are observation/branch checks,
            # never counted as new missing data when upstream computation failed.
            geometry_parameter = "geometry" if target == "D11" else "slab_weight"
            geometry_issues = []
            for source_layer in slab.layers:
                issues = _geometry_issues(source_layer, require_depth=target == "D11")
                geometry_issues.extend(issues)
                for issue in issues:
                    causes.add(
                        slab_index,
                        source_layer,
                        geometry_parameter,
                        "observed_geometry",
                        "",
                        issue,
                    )
            stage_issues[geometry_parameter].extend(geometry_issues)
            if target == "D11":
                ready["geometry"] = bool(slab.layers) and not geometry_issues

            for parameter in ["slab_weight", target] if target != "D11" else [target]:
                trace = traces[(parameter, None)]
                issues = (
                    list(geometry_issues) if parameter in {"slab_weight", "D11"} else []
                )
                if parameter == "slab_weight_shear":
                    slope_issues = _observation(slab.angle, "slope_angle", "degrees")
                    issues.extend(slope_issues)
                    for issue in slope_issues:
                        causes.add(
                            slab_index, None, parameter, methods[parameter], "", issue
                        )
                    if not ready.get("slab_weight", False):
                        issues.append(
                            Issue(
                                "blocked",
                                "integrated weight unsuccessful",
                                "slab_weight",
                            )
                        )
                else:
                    prerequisites = (
                        ["density"]
                        if parameter == "slab_weight"
                        else ["elastic_modulus", "poissons_ratio"]
                    )
                    for upstream in prerequisites:
                        if not ready[upstream]:
                            issues.append(
                                Issue(
                                    "blocked", f"{upstream} step unsuccessful", upstream
                                )
                            )
                if not slab.layers:
                    issues.append(Issue("other", "empty slab", "layers"))
                output_ok = trace.success and finite(trace.output)
                if parameter == "D11":
                    output_ok &= nominal(trace.output) > 0
                if not output_ok and not issues:
                    issues.append(
                        Issue(
                            "other",
                            trace.error or "invalid target output",
                            "output",
                            observed=nominal(trace.output)
                            if finite(trace.output)
                            else None,
                        )
                    )
                # Geometry/slope observations have already been counted above.
                for issue in issues:
                    if issue.category in {"blocked", "other"}:
                        causes.add(
                            slab_index,
                            None,
                            parameter,
                            methods[parameter],
                            density_method if target == "D11" else "",
                            issue,
                        )
                stage_issues[parameter].extend(
                    i for i in issues if i not in stage_issues[parameter]
                )
                ready[parameter] = bool(output_ok) and not issues

            success = all(ready[p] for p in step_parameters)
            first_failed = next((p for p in step_parameters if not ready[p]), "")
            category = (
                failure_category(stage_issues[first_failed]) if first_failed else ""
            )
            final_trace = traces[(target, None)]
            rows.append(
                (
                    slab_index,
                    slab.slab_id,
                    slab.pit_id,
                    pathway.pathway_id,
                    _path_label(methods, target),
                    density_method,
                    methods.get("elastic_modulus", ""),
                    methods.get("poissons_ratio", ""),
                    success,
                    nominal(final_trace.output),
                    first_failed,
                    category,
                    *(bool(ready[p]) for p in step_parameters),
                )
            )

    columns = [
        "slab_index",
        "slab_id",
        "pit_id",
        "pathway_id",
        "pathway",
        "density_method",
        "emod_method",
        "nu_method",
        "success",
        "value",
        "first_failed_step",
        "failure_category",
    ] + [f"{p}_ok" for p in step_parameters]
    attempts = pd.DataFrame.from_records(rows, columns=columns)
    del rows
    stage_rows = []
    for pathway, group in attempts.groupby("pathway", sort=True):
        alive = pd.Series(True, index=group.index)
        for order, (parameter, label) in enumerate(STEPS[target], start=1):
            entering = int(alive.sum())
            newly_lost = alive & ~group[f"{parameter}_ok"]
            alive &= group[f"{parameter}_ok"]
            categories = group.loc[newly_lost, "failure_category"].value_counts()
            stage_rows.append(
                {
                    "pathway": pathway,
                    "step": order,
                    "requirement": label,
                    "entering": entering,
                    "surviving": int(alive.sum()),
                    "newly_lost": int(newly_lost.sum()),
                    **{
                        c: int(categories.get(c, 0))
                        for c in ["missing_only", "validity_only", "mixed", "other"]
                    },
                }
            )
    stages = pd.DataFrame(stage_rows)
    counts = (
        attempts.groupby("slab_index")
        .success.sum()
        .reindex(range(len(slabs)), fill_value=0)
    )
    histogram = (
        counts.value_counts()
        .reindex(range(len(pathways) + 1), fill_value=0)
        .sort_index()
    )
    histogram.index.name = "successful_pathways"
    histogram.name = "slab_count"
    coverage = (
        attempts.groupby(
            ["pathway", "density_method", "emod_method", "nu_method"], as_index=False
        )
        .agg(
            successful_slabs=("success", "sum"),
            attempted_slabs=("success", "size"),
        )
        .sort_values(["successful_slabs", "pathway"], ascending=[False, True])
        .reset_index(drop=True)
    )
    coverage["coverage_percent"] = 100 * coverage.successful_slabs / len(slabs)
    reasons, method_summary = causes.frames()
    analysis = LossAnalysis(
        target,
        len(slabs),
        len(pathways),
        attempts,
        stages,
        reasons,
        method_summary,
        histogram,
        coverage,
    )
    validate_analysis(analysis)
    return analysis


def validate_analysis(result: LossAnalysis) -> None:
    """Check cohort completeness, unique attempts, and every funnel identity."""
    assert len(result.attempts) == result.n_slabs * result.n_pathways
    assert not result.attempts.duplicated(["slab_index", "pathway_id"]).any()
    assert result.histogram.sum() == result.n_slabs
    assert (
        result.histogram.index.to_numpy() * result.histogram.to_numpy()
    ).sum() == result.attempts.success.sum()
    categories = ["missing_only", "validity_only", "mixed", "other"]
    assert (result.stages[categories].sum(axis=1) == result.stages.newly_lost).all()
    assert (
        result.stages.entering - result.stages.newly_lost == result.stages.surviving
    ).all()
    for pathway, stages in result.stages.groupby("pathway", sort=False):
        stages = stages.sort_values("step")
        assert stages.iloc[0].entering == result.n_slabs
        assert np.array_equal(
            stages.entering.to_numpy()[1:], stages.surviving.to_numpy()[:-1]
        )
        successes = int(
            result.attempts.loc[result.attempts.pathway == pathway, "success"].sum()
        )
        assert stages.iloc[-1].surviving == successes
        assert stages.newly_lost.sum() + successes == result.n_slabs


def plot_histogram(result: LossAnalysis):
    """One bar per integer, including zero and unoccupied bins."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter

    fig, ax = plt.subplots(figsize=(9 if result.n_pathways > 4 else 6, 3.8))
    ax.bar(
        result.histogram.index,
        result.histogram.values,
        width=0.8,
        color="#0072B2" if result.target == "slab_weight_shear" else "#009E73",
    )
    ax.set(
        xlabel="Number of successfully calculated pathways",
        ylabel="Slab count",
        title=f"{'Shear slab weight' if result.target == 'slab_weight_shear' else 'D11'}: {result.n_slabs:,} ECTP slabs",
        xticks=range(result.n_pathways + 1),
        xlim=(-0.6, result.n_pathways + 0.6),
    )
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


def comparison_table(*results: LossAnalysis) -> pd.DataFrame:
    rows = []
    for result in results:
        lost = result.attempts.loc[
            ~result.attempts.success, "failure_category"
        ].value_counts()
        rows.append(
            {
                "target": result.target,
                "pathways": result.n_pathways,
                "zero successful pathways": int(result.histogram.iloc[0]),
                "at least one successful pathway": int(
                    result.n_slabs - result.histogram.iloc[0]
                ),
                "all pathways successful": int(result.histogram.iloc[-1]),
                "successful slab–pathway attempts": int(result.attempts.success.sum()),
                **{
                    f"lost attempts: {c}": int(lost.get(c, 0))
                    for c in ["missing_only", "validity_only", "mixed", "other"]
                },
            }
        )
    return pd.DataFrame(rows).set_index("target")
