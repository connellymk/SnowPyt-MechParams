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
from pathlib import Path

import matplotlib as mpl
import numpy as np

from snowpyt_mechparams.snowpilot import parse_caaml_directory
from snowpyt_mechparams.models import Pit, Slab

# ── HESS figure standards ─────────────────────────────────────────────────────
SINGLE_COL = 3.35   # inches
DOUBLE_COL = 7.0    # inches
DPI = 300


def hess_rcparams() -> None:
    """Apply HESS-compliant matplotlib rcParams (call once per notebook)."""
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']
    mpl.rcParams['figure.dpi'] = DPI


# ── Wong (2011) colorblind-safe palette — density method colours ─────────────
# Consistent across all pathway and stability criteria notebooks.
DENSITY_COLORS: dict[str, str] = {
    'data_flow':           '#CC79A7',   # pink
    'geldsetzer':          '#0072B2',   # blue
    'kim_jamieson_table2': '#009E73',   # green
    'kim_jamieson_table5': '#E69F00',   # orange
}


def rgba(hex_color: str, alpha: float = 0.75) -> str:
    """Convert a #RRGGBB hex colour to a Plotly-compatible rgba() string."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


# ── Data loading ──────────────────────────────────────────────────────────────

def load_pits(data_dir: str = 'data') -> list[Pit]:
    """Parse all CAAML files in *data_dir* and return a list of Pit objects."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        snow_pits_raw = parse_caaml_directory(str(Path(data_dir)))
    return [Pit.from_snow_pit(sp) for sp in snow_pits_raw]


def create_ectp_slabs(pits: list[Pit]) -> list[Slab]:
    """Return one Slab per propagating ECTP result across all pits."""
    return [
        slab
        for pit in pits
        for slab in pit.create_slabs(weak_layer_def='ECTP_failure_layer')
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
    if hasattr(v, 'nominal_value'):
        return float(v.nominal_value)
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


def count_ok(traces, param: str, n_layers: int) -> bool:
    """Return True if all *n_layers* layer-level traces for *param* succeeded."""
    n = sum(
        1 for t in traces
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
        t for t in traces
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
        if hasattr(out, 'nominal_value'):
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
