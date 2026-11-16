"""Descriptive reviewer statistics, independent of method implementations."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def number(value):
    return (
        float(getattr(value, "nominal_value", value)) if value is not None else math.nan
    )


def path_key(methods):
    return " -> ".join(
        methods.get(p, "") for p in ("density", "elastic_modulus", "poissons_ratio")
    ).rstrip(" ->")


def write_json(path, data):
    """Strict JSON: unavailable statistics are null, never JavaScript NaN."""

    def clean(x):
        if isinstance(x, dict):
            return {str(k): clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple, np.ndarray)):
            return [clean(v) for v in x]
        if isinstance(x, (np.integer, np.bool_)):
            return x.item()
        if isinstance(x, (float, np.floating)):
            return float(x) if math.isfinite(x) else None
        return x

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(clean(data), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def describe(values):
    x = pd.Series(values, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "n": len(x),
        "min": x.min(),
        "q25": x.quantile(0.25),
        "median": x.median(),
        "q75": x.quantile(0.75),
        "q90": x.quantile(0.9),
        "max": x.max(),
    }


def coverage_summary(records):
    rows = []
    for target, df in records.groupby("target", sort=True):
        counts = df.groupby("slab_id").success.sum()
        npaths = df.pathway.nunique()
        rows.append(
            {
                "target": target,
                "slabs": len(counts),
                "pathways": npaths,
                "union": int((counts > 0).sum()),
                "union_percent": 100 * (counts > 0).mean(),
                "successful_attempts": int(counts.sum()),
                "histogram": {i: int((counts == i).sum()) for i in range(npaths + 1)},
            }
        )
    coverage = records.groupby(["target", "pathway"], as_index=False).agg(
        successful_slabs=("success", "sum"), attempted_slabs=("success", "size")
    )
    coverage["coverage_percent"] = (
        100 * coverage.successful_slabs / coverage.attempted_slabs
    )
    return rows, coverage.sort_values(
        ["target", "successful_slabs", "pathway"], ascending=[True, False, True]
    )


def d11_comparison(records, paths=None):
    """Compare only complete, positive, finite D11 results; no inferential claims."""
    d = records[records.target == "D11"].copy()
    if paths is None:
        ranking = (
            d.groupby("pathway")
            .success.sum()
            .reset_index()
            .sort_values(["success", "pathway"], ascending=[False, True])
        )
        paths = ranking.pathway.head(16).tolist()
    good = d[d.success & d.pathway.isin(paths)].copy()
    counts = good.groupby("slab_id").pathway.nunique()
    ids = sorted(counts[counts == len(paths)].index)
    good = good[good.slab_id.isin(ids)]
    rows = []
    for slab_id, group in good.groupby("slab_id", sort=True):
        means, sigmas = group.value.to_numpy(), group.sigma.to_numpy()
        lo, hi = means - sigmas, means + sigmas
        pairs = list(itertools.combinations(range(len(means)), 2))
        separated = sum(hi[i] < lo[j] or hi[j] < lo[i] for i, j in pairs)
        width = float(2 * sigmas.max())
        rows.append(
            {
                "slab_id": slab_id,
                "pit_id": group.pit_id.iloc[0],
                "n_layers": group.n_layers.iloc[0],
                "grain_forms": group.grain_forms.iloc[0],
                "spread_ratio": means.max() / means.min(),
                "absolute_range": means.max() - means.min(),
                "largest_full_interval_width": width,
                "range_to_interval_width": (
                    (means.max() - means.min()) / width if width else math.nan
                ),
                "pair_count": len(pairs),
                "nonoverlap_pairs": separated,
                "nonoverlap_fraction": separated / len(pairs) if pairs else math.nan,
                "negative_lower_endpoints": int((lo < 0).sum()),
                "median_relative_uncertainty": float(np.median(sigmas / np.abs(means))),
            }
        )
    stats = pd.DataFrame(
        rows,
        columns=[
            "slab_id",
            "pit_id",
            "n_layers",
            "grain_forms",
            "spread_ratio",
            "absolute_range",
            "largest_full_interval_width",
            "range_to_interval_width",
            "pair_count",
            "nonoverlap_pairs",
            "nonoverlap_fraction",
            "negative_lower_endpoints",
            "median_relative_uncertainty",
        ],
    )
    summary = {
        "pathways": paths,
        "common_slabs": len(ids),
        "common_pits": good.pit_id.nunique(),
        "single_layer_slabs": int((stats.n_layers == 1).sum()),
        "grain_forms": sorted(set(good.grain_forms)),
        "pooled_relative_uncertainty": describe(good.sigma / good.value.abs()),
        **{
            col: describe(stats[col])
            for col in [
                "spread_ratio",
                "range_to_interval_width",
                "nonoverlap_fraction",
                "median_relative_uncertainty",
            ]
        },
        "negative_lower_endpoints": int(stats.negative_lower_endpoints.sum()),
        "slabs_with_any_nonoverlap": int((stats.nonoverlap_pairs > 0).sum()),
    }
    selected = []
    selected_ids = set()
    for q in [0.3, 0.6, 0.9]:
        if len(selected_ids) < len(stats):
            target = stats.spread_ratio.quantile(q)
            chosen = (
                stats.loc[~stats.slab_id.isin(selected_ids)]
                .assign(distance=lambda frame: (frame.spread_ratio - target).abs())
                .sort_values(["distance", "slab_id"])
                .iloc[0]
            )
            selected_ids.add(chosen.slab_id)
            selected.append(
                {
                    "quantile": q,
                    "slab_id": chosen.slab_id,
                    "spread_ratio": chosen.spread_ratio,
                }
            )
    summary["illustrations"] = selected
    return summary, stats, good


def calculate_targets(slabs):
    """Small independent coverage check used by the reviewer notebook."""
    from snowpyt_mechparams.execution import ExecutionEngine, ExecutionConfig

    engine = ExecutionEngine()
    config = ExecutionConfig(include_method_uncertainty=False)
    rows = []
    for slab in slabs:
        for target in ("slab_weight_shear", "slab_weight_shear_with_elasticity", "D11"):
            results = engine.execute_all(slab, target, config=config)
            for result in results.pathways.values():
                output = next(
                    t.output
                    for t in result.computation_trace
                    if t.parameter == target and t.layer_index is None
                )
                value, sigma = number(output), float(getattr(output, "std_dev", 0))
                success = (
                    result.success
                    and math.isfinite(value)
                    and math.isfinite(sigma)
                    and (target != "D11" or value > 0)
                )
                rows.append(
                    dict(
                        target=target,
                        slab_id=slab.slab_id,
                        pit_id=slab.pit_id,
                        pathway=path_key(result.methods_used),
                        success=success,
                        value=value if success else math.nan,
                        sigma=sigma if success else math.nan,
                        n_layers=len(slab.layers),
                        grain_forms=",".join(
                            sorted(
                                {(layer.grain_form or "")[:2] for layer in slab.layers}
                            )
                        ),
                    )
                )
    return pd.DataFrame(rows)
