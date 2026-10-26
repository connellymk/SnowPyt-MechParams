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
from pathlib import Path
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
    "data_flow": "Direct matched density",
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
        ("density", r"Density, $\rho$"),
        ("slab_weight_shear", r"Shear weight, $W_{\mathrm{shear}}$"),
    ),
    "slab_weight_shear_with_elasticity": (
        ("density", r"Density, $\rho$"),
        ("slab_weight_shear", r"Shear weight, $W_{\mathrm{shear}}$"),
        ("elastic_modulus", "Young's modulus, $E$"),
        ("poissons_ratio", r"Poisson's ratio, $\nu$"),
    ),
    "D11": (
        ("density", "Density"),
        ("elastic_modulus", "Young's modulus"),
        ("poissons_ratio", "Poisson's ratio"),
        ("geometry", "Layer geometry"),
        ("D11", "D11 calculation"),
    ),
}
TARGET_LABELS = {
    "slab_weight_shear": "Shear weight",
    "slab_weight_shear_with_elasticity": "Shear weight with elasticity",
    "D11": "D11",
}
PARAMETER_LABELS = {
    "density": r"Density, $\rho$",
    "elastic_modulus": "Young's modulus, $E$",
    "poissons_ratio": r"Poisson's ratio, $\nu$",
    "slab_weight": "Slab weight per unit area, $W$",
    "slab_weight_shear": r"Shear weight, $W_{\mathrm{shear}}$",
    "slab_weight_shear_with_elasticity": "Shear weight with elasticity",
    "D11": r"Bending stiffness, $D_{11}$",
}
FIELD_LABELS = {
    "density_measured": "matched density observation",
    "density": r"density, $\rho$",
    "hand_hardness": "hand hardness",
    "hand_hardness_index": "hand hardness index",
    "grain_form": "primary grain form",
    "grain_size": "average grain size",
    "thickness": "layer thickness",
    "depth_top": "layer top depth",
    "slope_angle": r"slope angle, $\psi$",
    "output": "calculated output",
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
        # Missing hardness is the same observation gap for every grain form.
        # Merge before counting so slabs with several affected layers count once.
        if issue.category == "missing" and issue.field == "hand_hardness":
            issue = replace(
                issue,
                reason="missing observation",
                grain_form="",
                resolved_grain_form="",
            )
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
                        observed_min=(
                            bucket["minimum"] if bucket["minimum"] != math.inf else None
                        ),
                        observed_max=(
                            bucket["maximum"]
                            if bucket["maximum"] != -math.inf
                            else None
                        ),
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
                ["elastic_modulus", "poissons_ratio"]
                if target != "slab_weight_shear"
                else []
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

            slab_parameters = (
                [target]
                if target == "D11"
                else ["slab_weight", "slab_weight_shear"]
                + ([target] if target == "slab_weight_shear_with_elasticity" else [])
            )
            for parameter in slab_parameters:
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
                    if parameter == "slab_weight_shear_with_elasticity":
                        prerequisites = ["slab_weight_shear", *prerequisites]
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
                            observed=(
                                nominal(trace.output) if finite(trace.output) else None
                            ),
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

            if target in {"slab_weight_shear", "slab_weight_shear_with_elasticity"}:
                # Both funnels combine thickness and slope. Preserve genuine
                # integrated-weight errors, but omit blocked consequences of
                # an earlier loss. Thickness remains checked for every layer.
                stage_issues["slab_weight_shear"] = (
                    geometry_issues
                    + [i for i in stage_issues["slab_weight"] if i.category == "other"]
                    + [
                        i
                        for i in stage_issues["slab_weight_shear"]
                        if i.category != "blocked"
                    ]
                )
            if target == "slab_weight_shear_with_elasticity":
                # A final-output error after all four requirements passed is
                # charged to the last step so the four-stage funnel reconciles.
                if all(ready[p] for p in step_parameters) and not ready[target]:
                    ready["poissons_ratio"] = False
                    stage_issues["poissons_ratio"] = stage_issues[target]

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
        color=LOSS_COLORS["missing_only"],
        edgecolor="#30383B",
        linewidth=0.4,
    )
    ax.set(
        xlabel="Successful calculation pathways per slab",
        ylabel="ECTP slabs",
        title=f"{TARGET_LABELS[result.target]}: {result.n_slabs:,} ECTP slabs",
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


def successful_pathway_table(
    weight: LossAnalysis, elastic_weight: LossAnalysis, compact: bool = False
) -> pd.DataFrame:
    """Exact integer bins; inapplicable bins are NA, not zero coverage.

    The default paper table and CSV retain all bins through 32, including
    unoccupied bins and zero-success slabs. An optional compact diagnostic
    view omits bins empty for both targets.
    """
    if (weight.target, elastic_weight.target) != (
        "slab_weight_shear",
        "slab_weight_shear_with_elasticity",
    ):
        raise ValueError(
            "Expected shear-weight and shear-weight-with-elasticity results"
        )
    if weight.n_slabs != elastic_weight.n_slabs:
        raise ValueError("Both distributions must use the same cohort")
    frame = pd.DataFrame(index=range(elastic_weight.n_pathways + 1))
    frame.index.name = "Successful pathways"
    for label, result in [
        ("Shear weight", weight),
        ("With elasticity", elastic_weight),
    ]:
        counts = result.histogram.reindex(frame.index).astype("Int64")
        frame[f"{label}: slabs"] = counts
        frame[f"{label}: %"] = 100 * counts / result.n_slabs
    if compact:
        columns = [c for c in frame if c.endswith(": slabs")]
        frame = frame.loc[frame[columns].fillna(0).sum(axis=1) > 0]
    return frame


def plot_pathway_distribution(weight: LossAnalysis, elastic_weight: LossAnalysis):
    """Align a count/percentage table and horizontal bars for each target.

    Both panels use rows 0..32 and the same linear slab-count scale. Rows above
    four are inapplicable to shear weight, so they have dashes and no bar.
    """
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter

    table = successful_pathway_table(weight, elastic_weight)
    n_rows = len(table)
    ticks = MaxNLocator(nbins=3, integer=True).tick_values(0, weight.n_slabs)
    limit = ticks[-1]
    fig = plt.figure(figsize=(7, 8.2))
    outer = fig.add_gridspec(
        1, 2, left=0.025, right=0.99, bottom=0.12, top=0.91, wspace=0.13
    )
    for panel, (label, result) in enumerate(
        [("Shear weight", weight), ("With elasticity", elastic_weight)]
    ):
        grid = outer[panel].subgridspec(1, 2, width_ratios=[1.15, 1.45], wspace=0.06)
        tab_ax = fig.add_subplot(grid[0])
        bar_ax = fig.add_subplot(grid[1], sharey=tab_ax)
        for ax in [tab_ax, bar_ax]:
            ax.set_ylim(n_rows - 0.5, -2.0)
            for row in range(n_rows):
                if row % 2 == 0:
                    ax.axhspan(row - 0.5, row + 0.5, color="#F2F4F4", zorder=0)
            ax.axhline(-0.6, color="#60686A", linewidth=0.5)
        tab_ax.set_xlim(0, 1)
        tab_ax.axis("off")
        positions = [0.13, 0.62, 0.98]
        for x, header, align in zip(
            positions,
            ["Successful\npathways", "Slabs", "%"],
            ["center", "right", "right"],
        ):
            tab_ax.text(x, -1.25, header, ha=align, va="center", fontsize=7)
        bar_ax.text(
            0.5,
            -1.25,
            "Slab count",
            ha="center",
            va="center",
            fontsize=7,
            transform=bar_ax.get_yaxis_transform(),
        )
        for k in table.index:
            count = table.loc[k, f"{label}: slabs"]
            percent = table.loc[k, f"{label}: %"]
            applicable = pd.notna(count)
            text_color = "#222222" if applicable else "#909898"
            entries = [
                str(k),
                f"{int(count):,}" if applicable else "—",
                f"{percent:.2f}" if applicable else "—",
            ]
            for x, value, align in zip(
                positions, entries, ["center", "right", "right"]
            ):
                tab_ax.text(
                    x, k, value, ha=align, va="center", fontsize=7, color=text_color
                )
        counts = result.histogram
        bar_ax.barh(
            counts.index,
            counts.values,
            height=0.7,
            color="#4C9085",
            edgecolor="#30383B",
            linewidth=0.25,
            zorder=2,
        )
        bar_ax.set_xlim(0, limit)
        bar_ax.set_xticks(ticks)
        bar_ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        bar_ax.set_xlabel("ECTP slabs", fontsize=7.5)
        bar_ax.tick_params(axis="x", labelsize=6.5, length=2)
        bar_ax.tick_params(axis="y", left=False, labelleft=False)
        bar_ax.spines[["top", "right", "left"]].set_visible(False)
        bar_ax.grid(axis="x", color="#D8D8D8", linewidth=0.4, zorder=1)
        bar_ax.set_axisbelow(True)
        bounds = outer[panel].get_position(fig)
        title = (
            r"(a) Shear weight, $W_{\mathrm{shear}}$"
            if panel == 0
            else r"(b) Shear weight with elasticity"
            + "\n"
            + r"($E$ and $\nu$ required)"
        )
        fig.text(
            (bounds.x0 + bounds.x1) / 2,
            0.965,
            title,
            ha="center",
            va="top",
            fontsize=8.5,
        )
    fig.text(
        0.025,
        0.065,
        "Bars count slabs with exactly the successful-pathway count shown in each row.\n"
        f"Both targets use {weight.n_slabs:,} ECTP slabs; percentages use this full cohort.\n"
        "Dashes indicate counts above the four available shear-weight pathways.",
        fontsize=7,
        ha="left",
        va="top",
        linespacing=1.5,
    )
    return fig


def write_successful_pathway_preview(table_path: Path) -> Path:
    """Add a compilable document beside the manuscript's table include."""
    preview = table_path.with_name(f"{table_path.stem}_preview.tex")
    preview.write_text(
        "\n".join(
            [
                r"\documentclass[10pt]{article}",
                r"\usepackage[margin=1in]{geometry}",
                r"\usepackage{booktabs,threeparttable}",
                r"\pagestyle{empty}",
                r"\begin{document}",
                rf"\input{{{table_path.name}}}",
                r"\end{document}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return preview


def export_successful_pathway_table(
    weight: LossAnalysis, elastic_weight: LossAnalysis, directories
) -> list[Path]:
    """Write a table include, its complete CSV, and a compilable preview."""
    full = successful_pathway_table(weight, elastic_weight)
    lines = [
        "% Manuscript include; compile successful_pathway_distribution_preview.tex for a standalone PDF.",
        r"\begin{table}[t]",
        r"\centering",
        r"\begin{threeparttable}",
        r"\caption{Distribution of successful calculation pathways per ECTP slab. "
        + f"Both targets use the same {weight.n_slabs:,}".replace(",", r"{,}")
        + r" slabs; shear weight has four pathways and shear weight with elasticity has 32.}",
        r"\label{tab:successful_pathway_distribution}",
        r"\small",
        r"\begin{tabular}{@{}rrrrr@{}}",
        r"\toprule",
        r" & \multicolumn{2}{c}{Shear weight, $W_{\mathrm{shear}}$}"
        r" & \multicolumn{2}{c}{With elasticity} \\",
        r"\cmidrule(lr){2-3}\cmidrule(l){4-5}",
        r"Successful pathways & Slabs & (\%) & Slabs & (\%) \\",
        r"\midrule",
    ]
    for k, row in full.iterrows():
        cells = [str(k)]
        for label in ["Shear weight", "With elasticity"]:
            count, percent = row[f"{label}: slabs"], row[f"{label}: %"]
            cells.extend(
                ["---", "---"]
                if pd.isna(count)
                else [f"{int(count):,}".replace(",", r"{,}"), f"{percent:.2f}"]
            )
        lines.append(" & ".join(cells) + r" \\")
    lines.extend(
        [
            r"\midrule",
            r"Total & "
            + f"{weight.n_slabs:,}".replace(",", r"{,}")
            + r" & 100.00 & "
            + f"{elastic_weight.n_slabs:,}".replace(",", r"{,}")
            + r" & 100.00 \\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\begin{tablenotes}[flushleft]\footnotesize",
            r"\item Percentages use all starting slabs. All pathway counts from 0 to "
            r"32 are shown; zeros indicate that no slabs have that count. Dashes "
            r"indicate pathway counts exceeding the four "
            r"available shear-weight pathways. Percentages may not sum exactly to 100\% "
            r"because of rounding.",
            r"\end{tablenotes}",
            r"\end{threeparttable}",
            r"\end{table}",
        ]
    )
    paths = []
    for directory in directories:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        stem = directory / "successful_pathway_distribution"
        csv, tex = stem.with_suffix(".csv"), stem.with_suffix(".tex")
        full.to_csv(csv, float_format="%.6f")
        tex.write_text("\n".join(lines) + "\n", encoding="utf-8")
        paths.extend([csv, tex, write_successful_pathway_preview(tex)])
    return paths


LOSS_COLORS = {
    "surviving": "#D9DDDF",
    "missing_only": "#4C9085",
    "validity_only": "#BE7655",
    "mixed": "#4C9085",
    "other": "#222222",
}
LOSS_LABELS = {
    "surviving": "Surviving slabs",
    "missing_only": "Missing observations only",
    "validity_only": "Validity limits only",
    "mixed": "Missing observations + validity limits",
    "other": "Other errors",
}


def _loss_style(category: str) -> dict:
    return {
        "facecolor": LOSS_COLORS[category],
        "edgecolor": LOSS_COLORS["validity_only"] if category == "mixed" else "#30383B",
        "linewidth": 0.35,
        "hatch": "////" if category == "mixed" else None,
    }


def _figure_label(text: str) -> str:
    """Use a math arrow: the paper's Helvetica text font lacks U+2192."""
    return text.replace("→", r"$\rightarrow$")


DENSITY_ORDER = [
    "data_flow",
    "geldsetzer",
    "kim_jamieson_table2",
    "kim_jamieson_table6",
]
EMOD_ORDER = ["bergfeld", "kochle", "wautier", "schottner"]
NU_ORDER = ["kochle", "srivastava"]


def _stepwise_title(result: LossAnalysis, pathway: str) -> str:
    methods = result.coverage.set_index("pathway").loc[pathway]
    labels = []
    for column, symbol in [
        ("density_method", r"$\rho$"),
        ("emod_method", "$E$"),
        ("nu_method", r"$\nu$"),
    ]:
        method = methods[column]
        if method:
            labels.append(f"{METHOD_LABELS[method]} ({symbol})")
    return TARGET_LABELS[result.target] + "\n" + r" $\rightarrow$ ".join(labels)


def plot_stepwise_losses(
    result: LossAnalysis,
    pathway: str | None = None,
    *,
    ax=None,
    final_step: int | None = None,
    compact: bool = False,
):
    """Stack survivors and exclusive newly lost categories for one pathway.

    Each bar's total is the population entering that step. This is a reporting
    funnel, not a stacking of the overlapping all-cause detail counts.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter

    if pathway is None:
        pathway = result.coverage.iloc[0].pathway
    stages = result.stages[result.stages.pathway == pathway].sort_values("step")
    if stages.empty:
        raise ValueError(f"Unknown pathway: {pathway}")
    categories = ["surviving", "missing_only", "validity_only", "mixed"]
    if stages.other.any():
        categories.append("other")
    parameters = [p for p, _ in STEPS[result.target]]
    requirements = []
    for parameter, label in zip(parameters, stages.requirement):
        label = PARAMETER_LABELS.get(parameter, label)
        if parameter == "slab_weight_shear":
            label += (
                "\n"
                + r"(Join: layer thickness, $h_n$;"
                + "\n"
                + r"slope angle, $\psi$)"
            )
        elif parameter == "geometry":
            label += "\n(Join: layer depths and thicknesses)"
        requirements.append(label)
    final_count = int(stages.iloc[-1].surviving)
    show_final = result.target != "slab_weight_shear"
    target_label = PARAMETER_LABELS[result.target]
    if result.target == "slab_weight_shear_with_elasticity":
        target_label = (
            "Shear weight with elasticity\n"
            + r"(Join: $W_{\mathrm{shear}}$, $E$, $\nu$)"
        )
    else:
        target_label += "\n(Final target)"
    if show_final:
        requirements.append(target_label)
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(
            figsize=(7, 2.0 + 0.60 * (len(stages) + 1 + int(show_final)))
        )
    else:
        fig = ax.figure
    font_size = 6.5 if compact else 7.5
    value_size = 6 if compact else 7
    label_threshold = 0.20 if compact else 0.07
    ax.barh(0, result.n_slabs, height=0.65, **_loss_style("surviving"))
    ax.text(
        result.n_slabs / 2,
        0,
        f"{result.n_slabs:,}",
        ha="center",
        va="center",
        fontsize=font_size,
    )
    for y, row in enumerate(stages.itertuples(), start=1):
        left = 0
        for category in categories:
            value = int(getattr(row, category))
            ax.barh(y, value, left=left, height=0.65, **_loss_style(category))
            if value >= label_threshold * result.n_slabs:
                ax.text(
                    left + value / 2,
                    y,
                    f"{value:,}",
                    ha="center",
                    va="center",
                    fontsize=value_size,
                    color="white" if category == "other" else "black",
                )
            left += value
        ax.text(
            1.025,
            y,
            f"{row.surviving:,} survive\n"
            f"{row.newly_lost:,} lost ({100 * row.newly_lost / result.n_slabs:.1f}%)",
            transform=ax.get_yaxis_transform(),
            va="center",
            fontsize=font_size,
        )
    final_y = len(stages) + 1 if final_step is None else final_step
    if show_final:
        ax.barh(final_y, final_count, height=0.65, **_loss_style("surviving"))
        ax.text(
            1.025,
            final_y,
            f"{final_count:,}\n0 lost (0.0%)",
            transform=ax.get_yaxis_transform(),
            va="center",
            fontsize=font_size,
        )
    ax.text(
        1.025,
        0,
        "Starting cohort",
        transform=ax.get_yaxis_transform(),
        va="center",
        fontsize=font_size,
    )
    ax.set(
        yticks=[*range(len(stages) + 1), *([final_y] if show_final else [])],
        yticklabels=["Starting cohort\n(All ECTP slabs)", *requirements],
        xlabel="ECTP slabs entering each requirement",
        xlim=(0, result.n_slabs),
    )
    last_row = final_y if show_final or final_step is not None else len(stages)
    ax.set_ylim(last_row + 0.65, -0.65)
    if standalone:
        fig.suptitle(_stepwise_title(result, pathway), fontsize=9, y=0.98)
    ax.tick_params(labelsize=font_size)
    ax.xaxis.label.set_fontsize(font_size)
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.set_xticks(
        [
            t
            for t in MaxNLocator(nbins=4, integer=True).tick_values(0, result.n_slabs)
            if 0 <= t <= result.n_slabs
        ]
    )
    ax.grid(axis="x", alpha=0.2, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    if standalone:
        handles = [Patch(label=LOSS_LABELS[c], **_loss_style(c)) for c in categories]
        fig.legend(
            handles=handles,
            title=f"Loss percentages use all {result.n_slabs:,} starting slabs",
            title_fontsize=6.5,
            loc="lower center",
            ncol=2,
            fontsize=7,
            frameon=False,
            bbox_to_anchor=(0.5, 0.015),
        )
        fig.subplots_adjust(left=0.31, right=0.80, top=0.88, bottom=0.22)
    return fig


def plot_stepwise_comparison(
    weight: LossAnalysis,
    elastic_weight: LossAnalysis,
    weight_pathway: str | None = None,
    elasticity_pathway: str | None = None,
):
    """Compare selected targets with shared count and row scales and one legend."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    if weight.n_slabs != elastic_weight.n_slabs:
        raise ValueError("Both panels must use the same slab cohort")
    weight_pathway = weight_pathway or weight.coverage.iloc[0].pathway
    elasticity_pathway = elasticity_pathway or elastic_weight.coverage.iloc[0].pathway
    final_step = max(len(STEPS[r.target]) for r in [weight, elastic_weight]) + 1
    fig = plt.figure(figsize=(7, 5.2))
    left = fig.add_axes([0.19, 0.20, 0.20, 0.63])
    right = fig.add_axes([0.70, 0.20, 0.20, 0.63], sharex=left)
    selected = [(weight, weight_pathway), (elastic_weight, elasticity_pathway)]
    for panel, (ax, (result, pathway)) in enumerate(zip([left, right], selected)):
        plot_stepwise_losses(
            result, pathway, ax=ax, final_step=final_step, compact=True
        )
        labels = [tick.get_text() for tick in ax.get_yticklabels()]
        labels = [
            label.replace(
                "Shear weight with elasticity", "Shear weight with\nelasticity"
            )
            for label in labels
        ]
        ax.set_yticks(ax.get_yticks(), labels=labels)
        ax.set_xlabel("ECTP slabs", fontsize=7)
        fig.text(
            0.25 + 0.51 * panel,
            0.97,
            f"({chr(97 + panel)}) {_stepwise_title(result, pathway)}",
            ha="center",
            va="top",
            fontsize=7.5,
        )
    categories = ["surviving", "missing_only", "validity_only", "mixed"]
    if any(r.stages.loc[r.stages.pathway == p, "other"].any() for r, p in selected):
        categories.append("other")
    fig.legend(
        handles=[Patch(label=LOSS_LABELS[c], **_loss_style(c)) for c in categories],
        title=f"Loss percentages use all {weight.n_slabs:,} starting slabs",
        title_fontsize=6.5,
        loc="lower center",
        ncol=2,
        fontsize=7,
        frameon=False,
        bbox_to_anchor=(0.5, 0.015),
    )
    return fig


def plot_loss_heatmap(result: LossAnalysis):
    """Compare newly lost fractions using the original cohort denominator.

    Elasticity targets are faceted by density method, with all E/nu combinations.
    No conditional step percentages or summed overlapping causes are used.
    """
    import matplotlib.pyplot as plt

    steps = result.stages.requirement.drop_duplicates().tolist()
    losses = result.stages.pivot(
        index="pathway", columns="requirement", values="newly_lost"
    )
    losses = 100 * losses.reindex(columns=steps) / result.n_slabs
    if result.target != "slab_weight_shear":
        fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
        panels = axes.ravel()
        short_steps = (
            [r"Density, $\rho$", "$E$", r"$\nu$", "Layer geometry", "$D_{11}$"]
            if result.target == "D11"
            else [r"Density, $\rho$", r"$W_{\mathrm{shear}}$", "$E$", r"$\nu$"]
        )
    else:
        fig, ax = plt.subplots(figsize=(7.5, 3.8), constrained_layout=True)
        panels = [ax]
        short_steps = [r"Density, $\rho$", r"Shear weight, $W_{\mathrm{shear}}$"]
    for index, ax in enumerate(panels):
        if result.target != "slab_weight_shear":
            density_method = DENSITY_ORDER[index]
            selected = result.coverage[
                result.coverage.density_method == density_method
            ].copy()
            selected["emod_order"] = selected.emod_method.map(
                {m: i for i, m in enumerate(EMOD_ORDER)}
            )
            selected["nu_order"] = selected.nu_method.map(
                {m: i for i, m in enumerate(NU_ORDER)}
            )
            selected = selected.sort_values(["emod_order", "nu_order"])
            labels = [
                _figure_label(f"{METHOD_LABELS[e]} → {METHOD_LABELS[n]}")
                for e, n in zip(selected.emod_method, selected.nu_method)
            ]
            ax.set_title(
                f"Density method: {METHOD_LABELS[density_method]}", fontsize=12, pad=10
            )
        else:
            selected = (
                result.coverage.set_index("density_method")
                .loc[DENSITY_ORDER]
                .reset_index()
            )
            labels = selected.pathway.tolist()
            ax.set_title("Shear weight: newly lost slabs", fontsize=12, pad=10)
        values = losses.loc[selected.pathway].to_numpy()
        heatmap = ax.imshow(values, cmap="YlOrRd", vmin=0, vmax=100, aspect="auto")
        ax.set(
            xticks=range(len(steps)),
            xticklabels=short_steps,
            yticks=range(len(labels)),
            yticklabels=labels,
        )
        ax.tick_params(axis="both", labelsize=9)
        for y in range(len(labels)):
            for x in range(len(steps)):
                value = values[y, x]
                label = "<0.1" if 0 < value < 0.1 else f"{value:.1f}"
                ax.text(
                    x,
                    y,
                    label,
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white" if value >= 60 else "black",
                )
        ax.set_xticks(np.arange(-0.5, len(steps)), minor=True)
        ax.set_yticks(np.arange(-0.5, len(labels)), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.5)
        ax.tick_params(which="minor", bottom=False, left=False)
    colorbar = fig.colorbar(heatmap, ax=panels, shrink=0.85, pad=0.025)
    colorbar.set_label(f"Newly lost slabs (% of all {result.n_slabs:,} starting slabs)")
    if result.target != "slab_weight_shear":
        fig.suptitle(
            f"{TARGET_LABELS[result.target]}: losses across all 32 pathways\n"
            r"Rows: Young's modulus, $E$ $\rightarrow$ Poisson's ratio, $\nu$",
            fontsize=14,
        )
    return fig


def _cause_label(row) -> str:
    """Keep raw grain codes, method resolution, and numerical bounds visible."""
    grain = row.grain_form or "No primary grain form"
    if row.resolved_grain_form and row.resolved_grain_form != row.grain_form:
        grain += f" → {row.resolved_grain_form}"
    if row.reason == "unsupported grain form":
        cause = "unsupported primary grain form"
    elif row.reason in {"below lower bound", "above upper bound"}:
        field = FIELD_LABELS.get(row.field, row.field.replace("_", " "))
        field = field[0].upper() + field[1:]
        operator = (
            ">"
            if row.reason == "above upper bound"
            else ("≤" if row.interval.startswith("(") else "<")
        )
        bound = row.upper if row.reason == "above upper bound" else row.lower
        unit = r"kg m$^{-3}$" if row.unit == "kg/m³" else row.unit
        cause = f"{field} {operator} {bound:g}" + (
            f" {unit}" if unit != "index" else ""
        )
    else:
        reason = {
            "absent observation": "Missing observation",
            "missing observation": "Missing observation",
            "nonfinite observation": "Nonfinite observation",
        }.get(row.reason, row.reason)
        cause = f"{reason}: {FIELD_LABELS.get(row.field, row.field.replace('_', ' '))}"
    if row.grain_form or row.field == "grain_form":
        cause = f"{grain} · {cause}"
    if row.density_context:
        cause += f"\nDensity method: {METHOD_LABELS[row.density_context]}"
    return _figure_label(cause)


def plot_method_causes(
    result: LossAnalysis,
    parameter: str,
    method: str,
    density_context: str | None = None,
    top_n: int = 12,
):
    """Separate bars for overlapping causes, with no aggregate 'other' bin.

    Show the largest ``top_n`` detailed rows per category. Missing hand hardness
    is counted once per affected slab across grain forms. Other causes keep
    their original grain code and upstream context; counts are never summed
    across contexts. Full counts remain available in reasons.
    Blocked computations and other errors remain in the notebook's tables.
    """
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter

    if top_n < 1:
        raise ValueError("top_n must be positive")
    frame = result.reasons[
        (result.reasons.parameter == parameter) & (result.reasons.method == method)
    ]
    if density_context is not None:
        frame = frame[frame.density_context == density_context]
    panels = []
    for category, label, color in [
        ("missing", "Missing observations", LOSS_COLORS["missing_only"]),
        ("validity", "Method validity limits", LOSS_COLORS["validity_only"]),
    ]:
        selected = frame[frame.category == category].sort_values(
            ["slabs", "field", "reason", "grain_form", "density_context"],
            ascending=[False, True, True, True, True],
        )
        if not selected.empty:
            panels.append((label, color, selected.head(top_n), len(selected)))
    if not panels:
        fig, ax = plt.subplots(figsize=(7, 2.5))
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "No missing-observation or validity-limit causes\nfor this method and density context.",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        return fig
    # Context labels have two lines. Allow room for both labels and count text.
    heights = [2.0 + 0.62 * len(p[2]) for p in panels]
    fig, axes = plt.subplots(
        len(panels),
        1,
        figsize=(11, sum(heights) + 0.5),
        squeeze=False,
        gridspec_kw={"height_ratios": heights},
    )
    for ax, (label, color, selected, total) in zip(axes.ravel(), panels):
        rows = list(selected.itertuples())
        maximum = int(selected.slabs.max())
        ax.barh(range(len(rows)), selected.slabs, color=color, height=0.65)
        for y, row in enumerate(rows):
            ax.text(
                row.slabs + max(0.015 * maximum, 0.05),
                y,
                f"{row.slabs:,}",
                va="center",
                fontsize=9,
            )
        ax.set(
            yticks=range(len(rows)),
            yticklabels=[_cause_label(r) for r in rows],
            xlabel="Affected slabs (overlapping causes)",
            xlim=(0, max(1.2 * maximum, 1.5)),
            title=f"{label}: {len(rows)} of {total} causes shown",
        )
        ax.invert_yaxis()
        ax.tick_params(axis="y", labelsize=9)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(axis="x", alpha=0.2)
        ax.set_axisbelow(True)
    title = f"{PARAMETER_LABELS[parameter]}: {METHOD_LABELS.get(method, method)}"
    if density_context is not None:
        title += f"\nDensity method: {METHOD_LABELS[density_context]}"
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return fig
