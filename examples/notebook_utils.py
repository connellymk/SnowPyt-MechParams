"""Shared utilities for SnowPyt-MechParams example notebooks.

Import pattern in notebooks:
    from notebook_utils import (
        load_pits, create_ectp_slabs, build_layer_infos,
        DENSITY_COLORS, rgba,
        hess_rcparams, SINGLE_COL, DOUBLE_COL, DPI,
    )
"""

from __future__ import annotations

import math
import os
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(__file__).resolve().parents[1] / ".matplotlib"),
)

import matplotlib as mpl
import numpy as np

if TYPE_CHECKING:
    from snowpyt_mechparams.models import Pit, Slab

# ── HESS figure standards ─────────────────────────────────────────────────────
SINGLE_COL = 3.35  # inches
DOUBLE_COL = 7.0  # inches
DPI = 300
REPO_ROOT = Path(__file__).resolve().parents[1]
SNOW_ROOT = Path(__file__).resolve().parents[2]
REPO_PAPER_FIGURES_DIR = REPO_ROOT / "paper" / "figures"
EXTERNAL_PAPER_FIGURES_DIR = SNOW_ROOT / "mech_params_paper" / "figures"
PAPER_FIGURES_DIR = REPO_PAPER_FIGURES_DIR
PAPER_FIGURES_DIRS = (REPO_PAPER_FIGURES_DIR, EXTERNAL_PAPER_FIGURES_DIR)


def hess_rcparams() -> None:
    """Apply HESS-compliant matplotlib rcParams (call once per notebook)."""
    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
    mpl.rcParams["figure.dpi"] = DPI
    mpl.rcParams["savefig.dpi"] = DPI
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42


# ── Wong (2011) colorblind-safe palette — density method colours ─────────────
# Consistent across all pathway and stability criteria notebooks.
DENSITY_COLORS: dict[str, str] = {
    "data_flow": "#8F8F8F",  # gray
    "geldsetzer": "#0072B2",  # blue
    "kim_jamieson_table2": "#009E73",  # green
    "kim_jamieson_table6": "#E69F00",  # orange
}


def rgba(hex_color: str, alpha: float = 0.75) -> str:
    """Convert a #RRGGBB hex colour to a Plotly-compatible rgba() string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── Data loading ──────────────────────────────────────────────────────────────


def load_pits(data_dir: str = "data") -> list[Pit]:
    """Parse all CAAML files in *data_dir* and return a list of Pit objects."""
    import warnings
    from snowpyt_mechparams.models import Pit
    from snowpyt_mechparams.snowpilot import parse_caaml_directory

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        snow_pits_raw = parse_caaml_directory(str(Path(data_dir)))
    return [Pit.from_snow_pit(sp) for sp in snow_pits_raw]


def create_ectp_slabs(pits: list[Pit]) -> list[Slab]:
    """Return one Slab per propagating ECTP result across all pits."""
    return [
        slab
        for pit in pits
        for slab in pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    ]


def build_layer_infos(pits: list[Pit]) -> list[tuple]:
    """Return a flat list of (layer, slope_angle_deg, pit_id, layer_idx) tuples.

    Each layer is wrapped as a single-layer slab for layer-level execution.
    Slope angle defaults to 0.0 when missing or non-finite.
    """
    layer_infos = []
    for pit in pits:
        try:
            angle = float(pit.slope_angle)
            if not np.isfinite(angle):
                angle = 0.0
        except (TypeError, ValueError):
            angle = 0.0
        for idx, layer in enumerate(pit.layers):
            layer_infos.append((layer, angle, pit.pit_id, idx))
    return layer_infos


# ── Computation-trace helpers (used in stability_criteria_inputs.ipynb) ───────


def nominal(v) -> float:
    """Extract nominal float value from a UFloat or plain number."""
    if v is None:
        return math.nan
    if hasattr(v, "nominal_value"):
        return float(v.nominal_value)
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


def finite_array(values: Iterable[Any]) -> np.ndarray:
    """Return finite float values from an iterable of plain or uncertain values."""
    arr = np.asarray([nominal(value) for value in values], dtype=float)
    return arr[np.isfinite(arr)]


def finite_positive(value: Any) -> bool:
    """Return True for finite, positive values."""
    value = nominal(value)
    return math.isfinite(value) and value > 0


def finite_percentile(values: Iterable[Any], q: float) -> float:
    """Return percentile *q* from finite values, or NaN when none are available."""
    arr = finite_array(values)
    return float(np.percentile(arr, q)) if arr.size else math.nan


def coefficient_of_variation(values: Iterable[Any]) -> float:
    """Return std / mean, or NaN when the mean is unavailable or zero."""
    arr = finite_array(values)
    if arr.size == 0:
        return math.nan
    mean_value = float(np.mean(arr))
    if mean_value == 0 or not math.isfinite(mean_value):
        return math.nan
    return float(np.std(arr, ddof=0) / abs(mean_value))


def pathway_key(methods: Mapping[str, str]) -> str:
    """Return the density -> E -> nu pathway key used in paper tables."""
    return " -> ".join(
        [
            methods.get("density", "data_flow"),
            methods.get("elastic_modulus", "unknown"),
            methods.get("poissons_ratio", "unknown"),
        ]
    )


def extract_pathway_parameter(pathway_result: Any, param: str) -> tuple[float, float]:
    """Return nominal value and standard deviation from a pathway result trace."""
    for trace in pathway_result.computation_trace:
        if trace.parameter == param and trace.success and trace.output is not None:
            output = trace.output
            return nominal(output), float(getattr(output, "std_dev", 0.0))
    return math.nan, math.nan


def extract_d11(pathway_result: Any) -> tuple[float, float]:
    """Return nominal D11 and standard deviation from a pathway result."""
    return extract_pathway_parameter(pathway_result, "D11")


def slab_attribute_record(
    slab_index: int, slab: Slab
) -> dict[str, float | int | str | None]:
    """Summarize slab geometry and layer attributes used in spread analysis."""
    thicknesses = finite_array(layer.thickness for layer in slab.layers)
    hardness_values = finite_array(layer.hand_hardness_index for layer in slab.layers)
    grain_forms = [
        str(layer.grain_form)
        for layer in slab.layers
        if layer.grain_form is not None
    ]
    grain_form_label = ", ".join(dict.fromkeys(grain_forms)) if grain_forms else None
    weighted_pairs = [
        (nominal(layer.hand_hardness_index), nominal(layer.thickness))
        for layer in slab.layers
    ]
    weighted_pairs = [
        (hardness, thickness)
        for hardness, thickness in weighted_pairs
        if math.isfinite(hardness) and math.isfinite(thickness) and thickness > 0
    ]

    hand_hardness_weighted_mean = math.nan
    if weighted_pairs:
        hardness, weights = np.asarray(weighted_pairs, dtype=float).T
        hand_hardness_weighted_mean = float(np.average(hardness, weights=weights))

    return {
        "slab_index": slab_index,
        "slab_id": slab.slab_id,
        "pit_id": slab.pit_id,
        "n_layers": len(slab.layers),
        "total_thickness_cm": nominal(slab.total_thickness),
        "slope_angle_deg": nominal(slab.angle),
        "grain_form_label": grain_form_label,
        "layer_thickness_mean_cm": (
            float(np.mean(thicknesses)) if thicknesses.size else math.nan
        ),
        "layer_thickness_std_cm": (
            float(np.std(thicknesses, ddof=0)) if thicknesses.size else math.nan
        ),
        "layer_thickness_cv": coefficient_of_variation(thicknesses),
        "layer_thickness_max_cm": (
            float(np.max(thicknesses)) if thicknesses.size else math.nan
        ),
        "hand_hardness_index_mean": (
            float(np.mean(hardness_values)) if hardness_values.size else math.nan
        ),
        "hand_hardness_index_std": (
            float(np.std(hardness_values, ddof=0))
            if hardness_values.size
            else math.nan
        ),
        "hand_hardness_index_range": (
            float(np.ptp(hardness_values)) if hardness_values.size else math.nan
        ),
        "hand_hardness_index_cv": coefficient_of_variation(hardness_values),
        "hand_hardness_index_weighted_mean": hand_hardness_weighted_mean,
    }


def scientific_latex(value: float) -> str:
    """Return a compact LaTeX scientific-notation value."""
    if not math.isfinite(value):
        return ""
    coefficient, exponent = f"{value:.3e}".split("e")
    return rf"${coefficient} \times 10^{{{int(exponent)}}}$"


def prepare_spread_rank_table(
    frame: Any,
    *,
    top_n: int = 8,
    pathway_formatter: Callable[[str], str] = str,
):
    """Format a paired spread ranking table for manuscript copy/paste."""
    import pandas as pd

    return pd.DataFrame(
        {
            "Slab ID": frame["slab_id"].astype(str),
            "Pit ID": frame["pit_id"].astype(str),
            "Layers": frame["n_layers"].astype(int).astype(str),
            "Thickness (cm)": frame["total_thickness_cm"].map(
                lambda value: f"{value:.1f}"
            ),
            "Min pathway": frame["min_pathway"].map(
                lambda value: pathway_formatter(str(value))
            ),
            "Max pathway": frame["max_pathway"].map(
                lambda value: pathway_formatter(str(value))
            ),
            "Max/min ratio": frame["pathway_spread_ratio"].map(
                lambda value: f"{value:.1f}"
            ),
            "log10(max/min)": frame["log10_pathway_spread"].map(
                lambda value: f"{value:.2f}"
            ),
            "D11 range (N·mm)": frame["range_D11"].map(scientific_latex),
        }
    ).head(top_n)


def count_ok(traces, param: str, n_layers: int) -> bool:
    """Return True if all *n_layers* layer-level traces for *param* succeeded."""
    n = sum(
        1
        for t in traces
        if t.parameter == param
        and t.layer_index is not None
        and t.success
        and t.output is not None
    )
    return n == n_layers


def extract_param_stats(traces, param: str) -> tuple[float, float]:
    """Return (nominal_avg, rel_unc_avg) over successful layer traces for *param*.

    Returns (nan, nan) when no traces succeed.
    """
    successful = [
        t
        for t in traces
        if t.parameter == param
        and t.layer_index is not None
        and t.success
        and t.output is not None
    ]
    if not successful:
        return np.nan, np.nan

    noms: list[float] = []
    rel_uncs: list[float] = []
    for t in successful:
        out = t.output
        if hasattr(out, "nominal_value"):
            nom = float(out.nominal_value)
            std = float(out.std_dev)
        else:
            try:
                nom = float(out)
            except (TypeError, ValueError):
                continue
            std = 0.0
        if np.isnan(nom):
            continue
        noms.append(nom)
        if nom != 0:
            rel_uncs.append(std / abs(nom))

    nom_avg = float(np.nanmean(noms)) if noms else np.nan
    rel_unc_avg = float(np.nanmean(rel_uncs)) if rel_uncs else np.nan
    return nom_avg, rel_unc_avg
