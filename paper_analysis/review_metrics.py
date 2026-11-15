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


def monte_carlo_tables(records):
    """Summarize every selected pathway, without pooling different slabs.

    The first table compares independent draws with first-order propagation.
    The second compares correlated MC draws with independent MC draws, matching
    each case/pathway before aggregation. Boundary controls remain in the raw
    results and are described separately in the response.
    """
    independent = records[records.correlation.eq(0)].copy()
    independent["sd_ratio"] = (
        independent.conditional_std / independent.first_order_sigma
    ).replace([np.inf, -np.inf], np.nan)
    independent["mean_ratio"] = (
        independent.conditional_mean / independent.first_order_nominal
    ).replace([np.inf, -np.inf], np.nan)
    comparison = (
        independent[independent.case_type.ne("boundary")]
        .groupby(["case_type", "case", "n_layers"], as_index=False, sort=True)
        .agg(
            pathways=("pathway", "size"),
            estimable_sd_ratios=("sd_ratio", "count"),
            sd_ratio_min=("sd_ratio", "min"),
            sd_ratio_median=("sd_ratio", "median"),
            sd_ratio_max=("sd_ratio", "max"),
            mean_ratio_min=("mean_ratio", "min"),
            mean_ratio_max=("mean_ratio", "max"),
            success_min=("success_fraction", "min"),
            success_max=("success_fraction", "max"),
        )
    )
    multilayer = records[records.target.eq("D11") & records.n_layers.gt(1)]
    reference = multilayer[multilayer.correlation.eq(0)][
        ["case", "pathway", "conditional_std", "success_fraction"]
    ].rename(
        columns={
            "conditional_std": "independent_std",
            "success_fraction": "independent_success",
        }
    )
    paired = multilayer[multilayer.correlation.gt(0)].merge(
        reference, on=["case", "pathway"], validate="many_to_one"
    )
    paired["sd_ratio"] = (paired.conditional_std / paired.independent_std).replace(
        [np.inf, -np.inf], np.nan
    )
    correlation = paired.groupby(
        ["case_type", "case", "n_layers", "correlation"], as_index=False, sort=True
    ).agg(
        pathways=("pathway", "size"),
        estimable_sd_ratios=("sd_ratio", "count"),
        sd_ratio_min=("sd_ratio", "min"),
        sd_ratio_median=("sd_ratio", "median"),
        sd_ratio_max=("sd_ratio", "max"),
        independent_success_min=("independent_success", "min"),
        independent_success_max=("independent_success", "max"),
        success_min=("success_fraction", "min"),
        success_max=("success_fraction", "max"),
    )
    return comparison, correlation


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
    for q in [0.3, 0.6, 0.9]:
        if not stats.empty:
            target = stats.spread_ratio.quantile(q)
            chosen = (
                stats.assign(distance=(stats.spread_ratio - target).abs())
                .sort_values(["distance", "slab_id"])
                .iloc[0]
            )
            selected.append(
                {
                    "quantile": q,
                    "slab_id": chosen.slab_id,
                    "spread_ratio": chosen.spread_ratio,
                }
            )
    summary["illustrations"] = selected
    return summary, stats, good
