"""Reproduce the response evidence without overwriting manuscript notebooks.

Run from the repository with its locked environment; see reviewer_response_README.md.
The density-matching alternative is an analysis-only sensitivity, not a parser change.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import warnings

import numpy as np
import pandas as pd
from uncertainties import ufloat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))
from notebook_utils import create_ectp_slabs, extract_d11, pathway_key  # noqa: E402
from loss_analysis_utils import analyze_losses, diagnose_layer, nominal  # noqa: E402
from snowpyt_mechparams.execution import ExecutionConfig, ExecutionEngine  # noqa: E402
from snowpyt_mechparams.graph import default_graph  # noqa: E402
from snowpyt_mechparams.models import Pit  # noqa: E402
from snowpyt_mechparams.pathway import find_parameterizations  # noqa: E402
from snowpyt_mechparams.snowpilot import parse_caaml_file  # noqa: E402


def dump(path, value):
    def clean(x):
        if isinstance(x, dict):
            return {str(k): clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [clean(v) for v in x]
        if isinstance(x, (float, np.floating)) and not math.isfinite(x):
            return None
        return x

    path.write_text(
        json.dumps(clean(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def finite(value):
    return math.isfinite(nominal(value))


def measurement(value, unit):
    """Require explicit matching units; do not silently convert field records."""
    if not isinstance(value, (list, tuple)) or len(value) != 2 or value[1] != unit:
        return math.nan
    return nominal(value[0])


def contained_density(layer, observations):
    """Thickness-weighted contained samples, with exact matches taking priority.

    Discard nonpositive/nonfinite or non-cm/kgm-3 records and boundary crossers.
    Reject an ambiguous set of overlapping contained samples. No minimum sampled
    fraction is assumed; that fraction is exported to expose representativeness.
    """
    top = measurement(layer.depth_top, "cm")
    h = measurement(layer.thickness, "cm")
    if not math.isfinite(top + h) or h <= 0:
        return None, "invalid_layer_geometry", 0.0
    candidates = []
    for obs in observations or []:
        a = measurement(obs.depth_top, "cm")
        b = measurement(obs.thickness, "cm")
        rho = measurement(obs.density, "kgm-3")
        if not math.isfinite(a + b + rho) or b <= 0 or rho <= 0:
            continue
        if obs.depth_top == layer.depth_top and obs.thickness == layer.thickness:
            return rho, "exact", 1.0
        if top <= a and a + b <= top + h:
            candidates.append((a, b, rho))
    if not candidates:
        return None, "no_contained_sample", 0.0
    candidates.sort()
    if any(a + h > b for (a, h, _), (b, _, _) in zip(candidates, candidates[1:])):
        return None, "overlapping_contained_samples", 0.0
    sampled = sum(x[1] for x in candidates)
    return sum(x[1] * x[2] for x in candidates) / sampled, "contained", sampled / h


def load_cohort(data_dir, out):
    pits, alternative, manifest, layers, tests = [], [], [], [], []
    qc = Counter()
    dates, pit_ids, wetness = [], [], Counter()
    for index, path in enumerate(sorted(data_dir.glob("*.xml"))):
        content = path.read_bytes()
        row = {"file": path.name, "sha256": hashlib.sha256(content).hexdigest()}
        try:
            raw = parse_caaml_file(str(path))
            pit = Pit.from_snow_pit(raw)
        except Exception as exc:
            row.update(parsed=False, error=f"{type(exc).__name__}: {exc}")
            manifest.append(row)
            continue
        date = str(raw.core_info.date)
        row.update(parsed=True, pit_id=pit.pit_id, date=date)
        manifest.append(row)
        dates.append(date)
        pit_ids.append(str(pit.pit_id))
        pits.append(pit)
        raw_layers = raw.snow_profile.layers or []
        qc["records_without_layers"] += not bool(raw_layers)
        obs = raw.snow_profile.density_profile or []
        qc["density_observations"] += len(obs)
        alt_layers = []
        for j, (source, layer) in enumerate(zip(raw_layers, pit.layers)):
            wetness[str(getattr(source, "wetness", None))] += 1
            rho, match, fraction = contained_density(source, obs)
            # Preserve the original exact match, including its existing uncertainty.
            new_density = layer.density_measured
            if new_density is None and rho is not None:
                new_density = ufloat(rho, 0.1 * rho)
            alt_layers.append(replace(layer, density_measured=new_density))
            layers.append(
                {
                    "pit_id": pit.pit_id,
                    "layer_index": j,
                    "exact_density": finite(layer.density_measured),
                    "alternative_density": finite(new_density),
                    "matching_status": match,
                    "sampled_fraction": fraction,
                }
            )
            qc["layers_missing_top"] += not finite(layer.depth_top)
            qc["layers_nonpositive_or_missing_thickness"] += (
                not finite(layer.thickness) or nominal(layer.thickness) <= 0
            )
            if j:
                gap = nominal(layer.depth_top) - nominal(pit.layers[j - 1].depth_bottom)
                qc["layer_gaps"] += math.isfinite(gap) and gap > 1e-8
                qc["layer_overlaps"] += math.isfinite(gap) and gap < -1e-8
        for obs_i in obs:
            rho_observed = measurement(obs_i.density, "kgm-3")
            qc["density_observations_nonpositive_or_nonfinite"] += (
                not math.isfinite(rho_observed) or rho_observed <= 0
            )
            qc["density_observations_exactly_matched"] += any(
                obs_i.depth_top == layer.depth_top
                and obs_i.thickness == layer.thickness
                for layer in raw_layers
            )
            a, b = measurement(obs_i.depth_top, "cm"), measurement(
                obs_i.thickness, "cm"
            )
            qc["density_observations_invalid_geometry"] += (
                not math.isfinite(a + b) or b <= 0
            )
            if math.isfinite(a + b) and b > 0:
                contained = any(
                    measurement(layer.depth_top, "cm") <= a
                    and a + b
                    <= measurement(layer.depth_top, "cm")
                    + measurement(layer.thickness, "cm")
                    for layer in raw_layers
                )
                intersects = any(
                    a
                    < measurement(layer.depth_top, "cm")
                    + measurement(layer.thickness, "cm")
                    and a + b > measurement(layer.depth_top, "cm")
                    for layer in raw_layers
                )
                qc["density_observations_crossing_layer_boundaries"] += (
                    intersects and not contained
                )
        alternative.append(replace(pit, layers=alt_layers))
        matching = pit._get_matching_ect_results()
        made = {s.test_result_index: s for s in pit.create_slabs("ECTP_failure_layer")}
        for j, test in enumerate(matching):
            depth = nominal(test.depth_top[0]) if test.depth_top else math.nan
            wl = next(
                (
                    layer
                    for layer in pit.layers
                    if finite(layer.depth_top)
                    and finite(layer.depth_bottom)
                    and nominal(layer.depth_top) <= depth < nominal(layer.depth_bottom)
                ),
                None,
            )
            reason = (
                "included"
                if j in made
                else (
                    "missing_failure_depth"
                    if not math.isfinite(depth)
                    else "no_matching_layer" if wl is None else "no_overlying_layers"
                )
            )
            tests.append(
                {
                    "pit_id": pit.pit_id,
                    "ectp_index": j,
                    "failure_depth_cm": depth,
                    "score": test.test_score,
                    "status": reason,
                    "slab_id": made[j].slab_id if j in made else "",
                }
            )
            if j in made:
                source_wetness = {
                    id(layer): getattr(source, "wetness", None)
                    for layer, source in zip(pit.layers, raw_layers)
                }
                codes = [source_wetness[id(layer)] for layer in made[j].layers]
                state = (
                    "any_non_dry_code"
                    if any(code not in [None, "D"] for code in codes)
                    else (
                        "all_missing"
                        if all(code is None for code in codes)
                        else (
                            "all_reported_dry"
                            if all(code == "D" for code in codes)
                            else "partly_missing_no_non_dry"
                        )
                    )
                )
                qc["ectp_slab_wetness_" + state] += 1
                tests[-1]["wetness_status"] = state
        if index % 10000 == 0:
            print(f"Parsed {index + 1} files", flush=True)
    mf = pd.DataFrame(manifest)
    mf.to_csv(
        out / "input_manifest.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    ld, td = pd.DataFrame(layers), pd.DataFrame(tests)
    ld.to_csv(
        out / "density_matching.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    td.to_csv(
        out / "ectp_selection.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    counts = Counter(p for p in pit_ids if p not in ["None", ""])
    qc.update(
        {
            "files": len(manifest),
            "parsed_pits": len(pits),
            "layers": len(layers),
            "duplicate_pit_ids": sum(n - 1 for n in counts.values()),
            "records_missing_pit_id": sum(p in ["None", ""] for p in pit_ids),
            "duplicate_file_contents": len(manifest) - mf.sha256.nunique(),
            "layers_exact_density": int(ld.exact_density.sum()),
            "layers_alternative_density": int(ld.alternative_density.sum()),
        }
    )
    valid_dates = [d for d in dates if d != "None"]
    qc["records_missing_date"] = len(dates) - len(valid_dates)
    qc["records_before_stated_start"] = sum(d < "2014-09-01" for d in valid_dates)
    qc["records_after_stated_end"] = sum(d > "2025-08-31" for d in valid_dates)
    return (
        pits,
        alternative,
        {
            "counts": dict(qc),
            "date_min": min(valid_dates),
            "date_max": max(valid_dates),
            "wetness_all_layers": dict(wetness),
            "ectp_selection": td.status.value_counts().to_dict(),
            "density_matching_status": ld.matching_status.value_counts().to_dict(),
            "contained_sample_fraction_quantiles": ld.loc[
                ld.matching_status == "contained", "sampled_fraction"
            ]
            .quantile([0, 0.25, 0.5, 0.75, 1])
            .to_dict(),
        },
    )


def success_summary(frame):
    counts = frame.groupby("slab_index").success.sum()
    coverage = frame.groupby("pathway").success.sum()
    return {
        "successful_attempts": int(frame.success.sum()),
        "union_slabs": int((counts > 0).sum()),
        "best_pathway_slabs": int(coverage.max()),
        "histogram": counts.value_counts().sort_index().to_dict(),
    }


def detailed_funnel(slabs, output):
    """Disjoint reason combinations at the first failed step of one pathway."""
    engine = ExecutionEngine()
    methods = {
        "density": "kim_jamieson_table2",
        "elastic_modulus": "wautier",
        "poissons_ratio": "kochle",
    }
    counts = Counter()
    for slab in slabs:
        result = engine.execute_single(
            slab,
            "slab_weight_shear_with_elasticity",
            methods,
            config=ExecutionConfig(include_method_uncertainty=False),
        )
        traces = {(t.parameter, t.layer_index): t for t in result.computation_trace}
        for parameter in [
            "density",
            "slab_weight_shear",
            "elastic_modulus",
            "poissons_ratio",
        ]:
            issues, ready = [], True
            if parameter == "slab_weight_shear":
                ready = traces[(parameter, None)].success
                if not finite(slab.angle):
                    counts[(parameter, "missing observation")] += 1
                    break
            else:
                for index, layer in enumerate(slab.layers):
                    t = traces[(parameter, index)]
                    ready &= t.success and finite(t.output)
                    issues.extend(
                        diagnose_layer(
                            layer,
                            parameter,
                            methods[parameter],
                            density=traces[("density", index)].output,
                            output=t.output,
                            error=t.error,
                        )
                    )
            if not ready:
                flags = set()
                for issue in issues:
                    if issue.category == "missing":
                        flags.add("missing observation")
                    elif issue.reason == "unsupported grain form":
                        flags.add("unsupported grain form")
                    elif issue.reason in ["below lower bound", "above upper bound"]:
                        flags.add("outside numerical bounds")
                    elif issue.category != "blocked":
                        flags.add("other")
                counts[(parameter, " + ".join(sorted(flags)) or "other")] += 1
                break
        else:
            counts[("complete", "success")] += 1
    frame = pd.DataFrame(
        [
            {
                "first_failed_step": p,
                "reason_combination": r,
                "slabs": n,
                "percent_of_14776": 100 * n / len(slabs),
            }
            for (p, r), n in counts.items()
        ]
    )
    assert frame.slabs.sum() == len(slabs)
    frame.sort_values(["first_failed_step", "reason_combination"]).to_csv(
        output / "detailed_funnel.csv", index=False
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=ROOT / "examples/data")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore", message="Using UFloat objects with std_dev==0.*")
    times, summary = {}, {}
    start = time.perf_counter()
    pits, alt_pits, summary["cohort"] = load_cohort(args.data, out)
    slabs, alt_slabs = create_ectp_slabs(pits), create_ectp_slabs(alt_pits)
    assert [s.slab_id for s in slabs] == [s.slab_id for s in alt_slabs]
    assert (
        len(pits) == 50278 and len(slabs) == 14776
    ), "Review cohort changed; investigate selection."
    times["parse_qc_and_slab_creation_seconds"] = time.perf_counter() - start
    dump(out / "cohort.json", summary["cohort"])
    pit_counts = Counter(s.pit_id for s in slabs)
    summary["cohort"].update(
        slabs=len(slabs),
        unique_pits=len(pit_counts),
        pits_with_multiple_slabs=sum(n > 1 for n in pit_counts.values()),
    )
    pp = {
        i: any((layer.grain_form or "")[:2].upper() == "PP" for layer in s.layers)
        for i, s in enumerate(slabs)
    }
    detailed_funnel(slabs, out)
    availability_attempts = None
    for target in ["slab_weight_shear", "slab_weight_shear_with_elasticity"]:
        start = time.perf_counter()
        result = analyze_losses(slabs, target)
        times[target + "_seconds"] = time.perf_counter() - start
        for name in ["stages", "reasons", "method_summary", "coverage"]:
            getattr(result, name).to_csv(out / f"{target}_{name}.csv", index=False)
        current = success_summary(result.attempts)
        baseline = result.attempts.copy()
        baseline.loc[
            (baseline.emod_method == "wautier") & baseline.slab_index.map(pp), "success"
        ] = False
        summary[target] = {"corrected": current, "original": success_summary(baseline)}
        if target == "slab_weight_shear_with_elasticity":
            availability_attempts = result.attempts.copy()
            availability_attempts["pathway"] = availability_attempts.apply(
                lambda r: " -> ".join([r.density_method, r.emod_method, r.nu_method]),
                axis=1,
            )
        print(target, summary[target], flush=True)
    engine = ExecutionEngine()
    config = ExecutionConfig(include_method_uncertainty=False)
    paths = find_parameterizations(default_graph, default_graph.get_node("D11"))
    rows, alt_rows = [], []
    start = time.perf_counter()
    for i, slab in enumerate(slabs):
        for p in engine.execute_all(
            slab, "D11", config=config, pathways=paths
        ).pathways.values():
            value, sd = extract_d11(p)
            m = p.methods_used
            # Outward-rounded approximate sampled envelopes read from Fig. 7a,
            # Schottner et al. 2026, p. 9. These are sensitivity assumptions,
            # NOT author-defined validity cutoffs or precise digitized endpoints.
            ranges = {
                "DF": (140, 360),
                "RG": (140, 360),
                "FC": (140, 470),
                "DH": (140, 470),
                "SH": (60, 180),
            }
            envelope_ok = True
            if m["elastic_modulus"] == "schottner":
                for t in p.computation_trace:
                    if t.parameter == "density":
                        grain = (slab.layers[t.layer_index].grain_form or "")[:2]
                        lo, hi = ranges.get(grain, (math.inf, -math.inf))
                        envelope_ok &= lo <= nominal(t.output) <= hi
            rows.append(
                {
                    "slab_index": i,
                    "slab_id": slab.slab_id,
                    "pit_id": slab.pit_id,
                    "pathway": pathway_key(m),
                    "density_method": m["density"],
                    "emod_method": m["elastic_modulus"],
                    "nu_method": m["poissons_ratio"],
                    "success": math.isfinite(value) and value > 0,
                    "D11": value,
                    "SD": sd,
                    "n_layers": len(slab.layers),
                    "schottner_envelope_ok": envelope_ok,
                    "grain_parents": ",".join(
                        sorted({(layer.grain_form or "")[:2] for layer in slab.layers})
                    ),
                }
            )
        if i % 4000 == 0:
            print(f"D11 {i}/{len(slabs)}", flush=True)
    times["D11_all_32_pathways_seconds"] = time.perf_counter() - start
    df = pd.DataFrame(rows)
    old = df.copy()
    old.loc[(old.emod_method == "wautier") & old.slab_index.map(pp), "success"] = False
    summary["D11"] = {
        "corrected": success_summary(df),
        "original": success_summary(old),
    }
    df.to_csv(
        out / "D11_attempts.csv.gz",
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    coverage = df.groupby("pathway").success.sum().sort_values(ascending=False)
    ranked = (
        coverage.rename("successful_slabs")
        .reset_index()
        .sort_values(["successful_slabs", "pathway"], ascending=[False, True])
    )
    ranked.to_csv(out / "D11_coverage.csv", index=False)
    top = ranked.head(16).pathway.tolist()
    pivot = df[df.pathway.isin(top)].pivot(
        index="slab_index", columns="pathway", values="success"
    )
    common_ids = pivot.index[pivot.all(axis=1)]
    common = df[df.slab_index.isin(common_ids) & df.pathway.isin(top)].copy()
    common["relative_SD"] = common.SD / common.D11.abs()
    common.to_csv(out / "D11_common_subset.csv", index=False)
    spread = []
    for i, group in common.groupby("slab_index"):
        low, high = group.loc[group.D11.idxmin()], group.loc[group.D11.idxmax()]
        spread.append(
            {
                "slab_index": int(i),
                "slab_id": low.slab_id,
                "pit_id": low.pit_id,
                "n_layers": int(low.n_layers),
                "grain_parents": low.grain_parents,
                "ratio": high.D11 / low.D11,
                "extreme_one_SD_intervals_disjoint": high.D11 - high.SD
                > low.D11 + low.SD,
            }
        )
    sf = pd.DataFrame(spread)
    sf.to_csv(out / "D11_spread.csv", index=False)
    summary["D11"]["common_subset"] = {
        "slabs": len(sf),
        "rows": len(common),
        "single_layer_slabs": int((sf.n_layers == 1).sum()),
        "grain_parent_combinations": sf.grain_parents.value_counts().to_dict(),
        "spread_quantiles": sf.ratio.quantile([0, 0.25, 0.5, 0.75, 0.9, 1]).to_dict(),
        "pooled_relative_SD_quantiles": common.relative_SD.quantile(
            [0.25, 0.5, 0.75]
        ).to_dict(),
        "extreme_one_SD_intervals_disjoint_slabs": int(
            sf.extreme_one_SD_intervals_disjoint.sum()
        ),
        "top_pathways": top,
    }
    from itertools import combinations

    overlaps = []
    for a, b in combinations(["bergfeld", "kochle", "wautier", "schottner"], 2):
        paired = common[common.emod_method == a].merge(
            common[common.emod_method == b],
            on=["slab_index", "density_method", "nu_method"],
            suffixes=("_a", "_b"),
        )
        overlap = (paired.D11_a - paired.SD_a <= paired.D11_b + paired.SD_b) & (
            paired.D11_b - paired.SD_b <= paired.D11_a + paired.SD_a
        )
        overlaps.append(
            {
                "E_a": a,
                "E_b": b,
                "pairs": len(paired),
                "overlap_pairs": int(overlap.sum()),
                "overlap_percent": 100 * overlap.mean(),
            }
        )
    pd.DataFrame(overlaps).to_csv(
        out / "D11_pairwise_interval_overlap.csv", index=False
    )
    # MF is excluded by both current nu methods, so this E assumption cannot
    # affect complete D11/elastic-availability pathways. Quantify rather than infer.
    summary["domain_sensitivity"] = {
        "successful_kochle_E_pathways_with_MF": int(
            (
                df.success
                & (df.emod_method == "kochle")
                & df.grain_parents.str.contains("MF")
            ).sum()
        )
    }
    restricted = df.copy()
    restricted["success"] &= restricted.schottner_envelope_ok
    summary["domain_sensitivity"]["schottner_sample_envelope_D11"] = success_summary(
        restricted
    )
    joined = availability_attempts.merge(
        df[["slab_index", "pathway", "schottner_envelope_ok"]],
        on=["slab_index", "pathway"],
        validate="one_to_one",
    )
    joined["success"] &= joined.schottner_envelope_ok
    summary["domain_sensitivity"]["schottner_sample_envelope_elastic_availability"] = (
        success_summary(joined)
    )
    start = time.perf_counter()
    for i, (slab, alt) in enumerate(zip(slabs, alt_slabs)):
        if not any(
            a.density_measured is not b.density_measured
            for a, b in zip(slab.layers, alt.layers)
        ):
            continue
        for target in ["slab_weight_shear", "slab_weight_shear_with_elasticity", "D11"]:
            for p in engine.execute_all(alt, target, config=config).pathways.values():
                if p.methods_used["density"] != "data_flow":
                    continue
                trace = next(t for t in p.computation_trace if t.parameter == target)
                alt_rows.append(
                    {
                        "slab_index": i,
                        "target": target,
                        "pathway": pathway_key(p.methods_used),
                        "success": trace.success and finite(trace.output),
                        "value": nominal(trace.output),
                    }
                )
    times["density_matching_sensitivity_seconds"] = time.perf_counter() - start
    adf = pd.DataFrame(
        alt_rows, columns=["slab_index", "target", "pathway", "success", "value"]
    )
    adf.to_csv(out / "density_matching_changed_slabs.csv", index=False)
    summary["density_matching_sensitivity"] = {
        "changed_slabs": int(adf.slab_index.nunique()) if len(adf) else 0,
        "successful_changed_slab_pathways_by_target": (
            adf.groupby("target").success.sum().astype(int).to_dict()
            if len(adf)
            else {}
        ),
    }
    summary["timing"] = times
    summary["environment"] = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                ROOT / "src/snowpyt_mechparams/methods/layer/elastic_modulus.py",
                ROOT / "paper_analysis/loss_analysis_utils.py",
                ROOT / "uv.lock",
            ]
        },
    }
    dump(out / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
