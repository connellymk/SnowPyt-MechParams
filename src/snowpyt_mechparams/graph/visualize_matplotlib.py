"""
Publication-quality matplotlib figures for the parameter dependency graph.

Generates high-DPI PNG figures suitable for the HESS paper, following the
project figure standards:
- Font: DejaVu Sans (sans-serif via rcParams)
- Colors: Wong (2011) colorblind-safe palette for group fills
- Single column = 3.35 in; Double column = 7.0 in; DPI = 300
- No embedded titles (captions go in .tex)

Four figures are produced:

overview
    Top-level flow showing the five conceptual parameter groups as boxes
    with simple arrows between them.  No merge nodes, no method names.

layer
    Detailed flowchart for layer parameter calculation paths:
    measured inputs → density / E / ν / G, with method names.

slab
    Detailed flowchart for slab stiffness assembly:
    layer params → A11 / B11 / D11 / A55, with merge nodes.

stability
    Detailed flowchart for slab weight pathways:
    density + thickness → W, W + slope → W_s, W_s + E + ν.

Functions
---------
generate_matplotlib_overview
generate_matplotlib_layer_detail
generate_matplotlib_slab_detail
generate_matplotlib_stability_detail
save_matplotlib_diagrams
    Convenience function that saves all four figures to a directory.

Notes
-----
Layouts are manually specified (x, y in figure-normalised coordinates) to
produce clean, publication-ready results.  This avoids the inconsistency of
automatic graph-layout algorithms for this relatively small graph.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

import matplotlib as mpl
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from snowpyt_mechparams.graph.structures import Graph


# ---------------------------------------------------------------------------
# Project-wide style constants
# ---------------------------------------------------------------------------

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 7,
})

# Wong (2011) palette — group fill colours (lightened for readability)
_COLORS = {
    "input":     "#FFF9C4",   # pale yellow
    "layer":     "#C8E6C9",   # pale green
    "slab":      "#FFCCBC",   # pale orange
    "weak_layer":"#FFF3E0",   # pale amber
    "stability": "#FCE4EC",   # pale pink
    "merge":     "#F3E5F5",   # pale purple
    "root":      "#E1F5FF",   # pale blue
}

_EDGE_COLORS = {
    "input":     "#F57F17",
    "layer":     "#388E3C",
    "slab":      "#D84315",
    "weak_layer":"#E65100",
    "stability": "#880E4F",
    "merge":     "#7B1FA2",
    "root":      "#0288D1",
}

_SINGLE_COL = 3.35   # inches
_DOUBLE_COL = 7.0    # inches
_DPI = 300


# ---------------------------------------------------------------------------
# Low-level drawing helpers
# ---------------------------------------------------------------------------

class _Box(NamedTuple):
    """A labelled rectangle in axes-fraction coordinates."""
    label: str
    x: float       # centre x  (axes fraction)
    y: float       # centre y  (axes fraction)
    w: float       # full width
    h: float       # full height
    color: str
    edge_color: str
    fontsize: float = 7.0
    bold: bool = False


def _draw_box(ax: plt.Axes, box: _Box, radius: float = 0.02) -> Tuple[float, float]:
    """Draw a rounded rectangle and centred text; return (cx, cy) in axes coords."""
    x0 = box.x - box.w / 2
    y0 = box.y - box.h / 2
    patch = FancyBboxPatch(
        (x0, y0), box.w, box.h,
        boxstyle=f"round,pad=0",
        facecolor=box.color,
        edgecolor=box.edge_color,
        linewidth=1.0,
        transform=ax.transAxes,
        clip_on=False,
        zorder=2,
    )
    ax.add_patch(patch)
    weight = "bold" if box.bold else "normal"
    ax.text(
        box.x, box.y, box.label,
        ha="center", va="center",
        fontsize=box.fontsize,
        fontweight=weight,
        transform=ax.transAxes,
        zorder=3,
        wrap=False,
    )
    return box.x, box.y


def _draw_arrow(
    ax: plt.Axes,
    x0: float, y0: float,
    x1: float, y1: float,
    label: str = "",
    color: str = "#555555",
    fontsize: float = 6.0,
    connectionstyle: str = "arc3,rad=0.0",
) -> None:
    """Draw an arrow in axes-fraction coordinates with optional edge label."""
    ax.annotate(
        "",
        xy=(x1, y1), xycoords="axes fraction",
        xytext=(x0, y0), textcoords="axes fraction",
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=0.8,
            connectionstyle=connectionstyle,
        ),
        zorder=1,
    )
    if label:
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2
        ax.text(
            mx, my, label,
            ha="center", va="center",
            fontsize=fontsize,
            color=color,
            transform=ax.transAxes,
            zorder=4,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.5),
        )


def _new_fig(width: float, height: float) -> Tuple[Figure, plt.Axes]:
    """Create a blank figure with a single invisible axes filling it."""
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


# ---------------------------------------------------------------------------
# Figure 1 — Overview
# ---------------------------------------------------------------------------

def generate_matplotlib_overview(graph: Graph) -> Figure:  # noqa: ARG001
    """
    Generate the big-picture overview figure.

    Five group boxes arranged left-to-right, connected by simple arrows.
    No merge nodes, no method names.  Width = 7.0 in (double column).

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph (used only for type-checking).

    Returns
    -------
    Figure
    """
    fig, ax = _new_fig(_DOUBLE_COL, 2.4)

    BW, BH = 0.16, 0.54   # box width/height (axes fraction)
    Y = 0.54               # vertical centre for all main boxes

    boxes = [
        _Box("Snow Pit\nObservations",  0.08, Y, BW, BH, _COLORS["input"],     _EDGE_COLORS["input"],     bold=True),
        _Box("Layer\nParameters",       0.30, Y, BW, BH, _COLORS["layer"],     _EDGE_COLORS["layer"],     bold=True),
        _Box("Slab\nStiffnesses",       0.52, Y, BW, BH, _COLORS["slab"],      _EDGE_COLORS["slab"],      bold=True),
        _Box("Slab Weight\nPathways",   0.74, Y, BW, BH, _COLORS["stability"], _EDGE_COLORS["stability"], bold=True),
    ]

    for box in boxes:
        _draw_box(ax, box)

    # Arrows between groups
    arrow_color = "#444444"
    # Observations → Layer
    _draw_arrow(ax, 0.08 + BW/2, Y, 0.30 - BW/2, Y, color=arrow_color)
    # Layer → Slab
    _draw_arrow(ax, 0.30 + BW/2, Y, 0.52 - BW/2, Y, color=arrow_color)
    # Layer → Slab weight pathways
    _draw_arrow(ax, 0.30 + BW/2, Y - 0.06, 0.74 - BW/2, Y - 0.06,
                color=arrow_color, connectionstyle="arc3,rad=-0.15")
    # Observations → Slab weight pathways
    _draw_arrow(ax, 0.08 + BW/2, Y + 0.06, 0.74 - BW/2, Y + 0.06,
                color=arrow_color, connectionstyle="arc3,rad=0.15")

    # Sub-labels listing individual parameters
    param_labels = {
        0.08:  "ρ_meas, HH,\ngrain form,\ngrain size,\nthickness,\nslope",
        0.30:  "ρ, E, ν, G",
        0.52:  "A₁₁, B₁₁,\nD₁₁, A₅₅",
        0.74:  "W, W_s,\nW_s + E + ν",
    }
    for xc, lbl in param_labels.items():
        ax.text(xc, Y - BH/2 - 0.07, lbl,
                ha="center", va="top", fontsize=5.5,
                transform=ax.transAxes, color="#444444")

    fig.tight_layout(pad=0.1)
    return fig


# ---------------------------------------------------------------------------
# Figure 2 — Layer parameters (detail)
# ---------------------------------------------------------------------------

def generate_matplotlib_layer_detail(graph: Graph) -> Figure:  # noqa: ARG001
    """
    Generate the layer parameters detail figure.

    Shows measured inputs → merge nodes → ρ / E / ν / G with method names.
    Width = 7.0 in (double column).

    Parameters
    ----------
    graph : Graph
        Unused (layout is static); kept for API consistency.

    Returns
    -------
    Figure
    """
    fig, ax = _new_fig(_DOUBLE_COL, 4.0)

    BW, BH = 0.14, 0.10
    MW, MH = 0.18, 0.10   # merge box dimensions

    # Column x-centres
    C0, C1, C2, C3 = 0.08, 0.30, 0.57, 0.86

    # --- Input nodes (col 0) ---
    inputs: Dict[str, _Box] = {
        "meas_density": _Box("ρ (measured)",     C0, 0.85, BW, BH, _COLORS["input"], _EDGE_COLORS["input"]),
        "meas_hh":      _Box("hand hardness",    C0, 0.65, BW, BH, _COLORS["input"], _EDGE_COLORS["input"]),
        "meas_gf":      _Box("grain form",       C0, 0.45, BW, BH, _COLORS["input"], _EDGE_COLORS["input"]),
        "meas_gs":      _Box("grain size",       C0, 0.25, BW, BH, _COLORS["input"], _EDGE_COLORS["input"]),
    }

    # --- Merge nodes (col 1) ---
    merges: Dict[str, _Box] = {
        "m_hh_gf":    _Box("HH + grain form",         C1, 0.65, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
        "m_hh_gf_gs": _Box("HH + grain form + size",  C1, 0.38, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
        "m_d_gf":     _Box("ρ + grain form",           C1, 0.11, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
        "m_E_nu_G":   _Box("E + ν",                    C2, 0.32, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
    }

    # --- Density node (col 2, mid height) ---
    density_box = _Box("ρ\n(density)", C2, 0.55, BW, BH*1.2, _COLORS["layer"], _EDGE_COLORS["layer"])

    # --- Layer output nodes (col 3) ---
    outputs: Dict[str, _Box] = {
        "E":  _Box("E\n(elastic modulus)",   C3, 0.78, BW, BH*1.2, _COLORS["layer"], _EDGE_COLORS["layer"]),
        "nu": _Box("ν\n(Poisson's ratio)",   C3, 0.55, BW, BH*1.2, _COLORS["layer"], _EDGE_COLORS["layer"]),
        "G":  _Box("G\n(shear modulus)",     C3, 0.32, BW, BH*1.2, _COLORS["layer"], _EDGE_COLORS["layer"]),
        "rho_out": _Box("ρ\n(density out)",  C3, 0.10, BW, BH*1.2, _COLORS["layer"], _EDGE_COLORS["layer"]),
    }

    all_boxes = {**inputs, **merges, "density": density_box, **outputs}
    for box in all_boxes.values():
        _draw_box(ax, box)

    ac = "#555555"

    # Input → merge
    _draw_arrow(ax, inputs["meas_hh"].x + BW/2,    inputs["meas_hh"].y,
                    merges["m_hh_gf"].x - MW/2,    merges["m_hh_gf"].y, color=ac)
    _draw_arrow(ax, inputs["meas_gf"].x + BW/2,    inputs["meas_gf"].y,
                    merges["m_hh_gf"].x - MW/2,    merges["m_hh_gf"].y, color=ac)
    _draw_arrow(ax, merges["m_hh_gf"].x + MW/2,    merges["m_hh_gf"].y,
                    merges["m_hh_gf_gs"].x - MW/2, merges["m_hh_gf_gs"].y, color=ac)
    _draw_arrow(ax, inputs["meas_gs"].x + BW/2,    inputs["meas_gs"].y,
                    merges["m_hh_gf_gs"].x - MW/2, merges["m_hh_gf_gs"].y, color=ac)

    # Merge → density
    _draw_arrow(ax, inputs["meas_density"].x + BW/2, inputs["meas_density"].y,
                    density_box.x - BW/2,            density_box.y, color=ac)
    _draw_arrow(ax, merges["m_hh_gf"].x + MW/2,    merges["m_hh_gf"].y,
                    density_box.x - BW/2,            density_box.y,
                    label="geldsetzer\nkim_j_t2", color=_EDGE_COLORS["layer"], fontsize=5.5)
    _draw_arrow(ax, merges["m_hh_gf_gs"].x + MW/2, merges["m_hh_gf_gs"].y,
                    density_box.x - BW/2,            density_box.y,
                    label="kim_j_t5", color=_EDGE_COLORS["layer"], fontsize=5.5)

    # Density + grain_form → m_d_gf
    _draw_arrow(ax, density_box.x,               density_box.y - BH*0.6,
                    merges["m_d_gf"].x - MW/2,   merges["m_d_gf"].y,
                    color=ac, connectionstyle="arc3,rad=0.2")
    _draw_arrow(ax, inputs["meas_gf"].x + BW/2,  inputs["meas_gf"].y,
                    merges["m_d_gf"].x - MW/2,   merges["m_d_gf"].y, color=ac)

    # m_d_gf → E
    _draw_arrow(ax, merges["m_d_gf"].x + MW/2,  merges["m_d_gf"].y,
                    outputs["E"].x - BW/2,       outputs["E"].y,
                    label="bergfeld\nkochle\nwautier\nschottner",
                    color=_EDGE_COLORS["layer"], fontsize=5.0)

    # grain_form → ν (kochle)
    _draw_arrow(ax, inputs["meas_gf"].x + BW/2,  inputs["meas_gf"].y,
                    outputs["nu"].x - BW/2,       outputs["nu"].y,
                    label="kochle", color=_EDGE_COLORS["layer"], fontsize=5.5)

    # m_d_gf → ν (srivastava)
    _draw_arrow(ax, merges["m_d_gf"].x + MW/2,  merges["m_d_gf"].y,
                    outputs["nu"].x - BW/2,       outputs["nu"].y,
                    label="srivastava", color=_EDGE_COLORS["layer"], fontsize=5.5,
                    connectionstyle="arc3,rad=-0.1")

    # E + ν → G
    _draw_arrow(ax, outputs["E"].x,               outputs["E"].y - BH*0.7,
                    merges["m_E_nu_G"].x + MW*0.1, merges["m_E_nu_G"].y + MH*0.45,
                    color=ac, connectionstyle="arc3,rad=0.1")
    _draw_arrow(ax, outputs["nu"].x + BW*0.15,    outputs["nu"].y - BH*0.7,
                    merges["m_E_nu_G"].x - MW*0.1, merges["m_E_nu_G"].y + MH*0.45,
                    color=ac, connectionstyle="arc3,rad=-0.1")
    _draw_arrow(ax, merges["m_E_nu_G"].x + MW/2, merges["m_E_nu_G"].y,
                    outputs["G"].x - BW/2,        outputs["G"].y,
                    label="lame_relationship", color=_EDGE_COLORS["layer"], fontsize=5.0)

    # density → output (data flow)
    _draw_arrow(ax, density_box.x + BW/2, density_box.y,
                    outputs["rho_out"].x - BW/2, outputs["rho_out"].y, color=ac)

    fig.tight_layout(pad=0.1)
    return fig


# ---------------------------------------------------------------------------
# Figure 3 — Slab stiffnesses (detail)
# ---------------------------------------------------------------------------

def generate_matplotlib_slab_detail(graph: Graph) -> Figure:  # noqa: ARG001
    """
    Generate the slab stiffness assembly detail figure.

    Shows layer parameters → slab merge nodes → A11 / B11 / D11 / A55.
    Width = 7.0 in (double column).

    Parameters
    ----------
    graph : Graph
        Unused.

    Returns
    -------
    Figure
    """
    fig, ax = _new_fig(_DOUBLE_COL, 3.2)

    BW, BH = 0.13, 0.12
    MW, MH = 0.17, 0.12

    C0, C1, C2, C3 = 0.10, 0.33, 0.60, 0.86

    layer_boxes: Dict[str, _Box] = {
        "thick": _Box("layer\nthickness",   C0, 0.78, BW, BH, _COLORS["input"],  _EDGE_COLORS["input"]),
        "E":     _Box("E",                  C0, 0.58, BW, BH, _COLORS["layer"],  _EDGE_COLORS["layer"]),
        "nu":    _Box("ν",                  C0, 0.40, BW, BH, _COLORS["layer"],  _EDGE_COLORS["layer"]),
        "G":     _Box("G",                  C0, 0.22, BW, BH, _COLORS["layer"],  _EDGE_COLORS["layer"]),
    }

    merge_boxes: Dict[str, _Box] = {
        "m_E_nu":      _Box("E + ν\n(all layers)",      C1, 0.56, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
        "m_hi_G":      _Box("h_i + G",                  C2, 0.38, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
        "m_hi_E_nu":   _Box("h_i + E + ν",              C2, 0.58, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
    }

    output_boxes: Dict[str, _Box] = {
        "D11": _Box("D₁₁\nbending stiffness",         C3, 0.80, BW, BH*1.3, _COLORS["slab"], _EDGE_COLORS["slab"]),
        "A55": _Box("A₅₅\nshear stiffness",           C3, 0.36, BW, BH*1.3, _COLORS["slab"], _EDGE_COLORS["slab"]),
        "A11": _Box("A₁₁\nextensional stiffness",     C3, 0.58, BW, BH*1.3, _COLORS["slab"], _EDGE_COLORS["slab"]),
        "B11": _Box("B₁₁\nbending-ext. coupling",     C3, 0.14, BW, BH*1.3, _COLORS["slab"], _EDGE_COLORS["slab"]),
    }

    for box in {**layer_boxes, **merge_boxes, **output_boxes}.values():
        _draw_box(ax, box)

    ac = "#555555"
    mc = _EDGE_COLORS["merge"]
    sc = _EDGE_COLORS["slab"]

    # E, nu → m_E_nu
    _draw_arrow(ax, layer_boxes["E"].x + BW/2,   layer_boxes["E"].y,
                    merge_boxes["m_E_nu"].x - MW/2, merge_boxes["m_E_nu"].y, color=ac)
    _draw_arrow(ax, layer_boxes["nu"].x + BW/2,  layer_boxes["nu"].y,
                    merge_boxes["m_E_nu"].x - MW/2, merge_boxes["m_E_nu"].y, color=ac)
    # thickness + G → m_hi_G
    _draw_arrow(ax, layer_boxes["thick"].x + BW/2,  layer_boxes["thick"].y,
                    merge_boxes["m_hi_G"].x - MW/2, merge_boxes["m_hi_G"].y,
                    color=ac, connectionstyle="arc3,rad=0.2")
    _draw_arrow(ax, layer_boxes["G"].x + BW/2,   layer_boxes["G"].y,
                    merge_boxes["m_hi_G"].x - MW/2, merge_boxes["m_hi_G"].y, color=ac)
    # thickness + m_E_nu → m_hi_E_nu
    _draw_arrow(ax, layer_boxes["thick"].x + BW/2, layer_boxes["thick"].y,
                    merge_boxes["m_hi_E_nu"].x - MW/2, merge_boxes["m_hi_E_nu"].y,
                    color=ac, connectionstyle="arc3,rad=0.25")
    _draw_arrow(ax, merge_boxes["m_E_nu"].x + MW/2, merge_boxes["m_E_nu"].y,
                    merge_boxes["m_hi_E_nu"].x - MW/2, merge_boxes["m_hi_E_nu"].y, color=mc)
    # merges → outputs (weissgraeber_rosendahl)
    wlbl = "W&R (2023)"
    _draw_arrow(ax, merge_boxes["m_hi_E_nu"].x + MW/2,  merge_boxes["m_hi_E_nu"].y,
                    output_boxes["D11"].x - BW/2,        output_boxes["D11"].y,
                    label=wlbl, color=sc, fontsize=5.5,
                    connectionstyle="arc3,rad=0.15")
    _draw_arrow(ax, merge_boxes["m_hi_E_nu"].x + MW/2,  merge_boxes["m_hi_E_nu"].y,
                    output_boxes["A11"].x - BW/2,        output_boxes["A11"].y,
                    label=wlbl, color=sc, fontsize=5.5)
    _draw_arrow(ax, merge_boxes["m_hi_G"].x + MW/2,     merge_boxes["m_hi_G"].y,
                    output_boxes["A55"].x - BW/2,        output_boxes["A55"].y,
                    label=wlbl, color=sc, fontsize=5.5)
    _draw_arrow(ax, merge_boxes["m_hi_E_nu"].x + MW/2,  merge_boxes["m_hi_E_nu"].y,
                    output_boxes["B11"].x - BW/2,        output_boxes["B11"].y,
                    label=wlbl, color=sc, fontsize=5.5,
                    connectionstyle="arc3,rad=0.1")

    fig.tight_layout(pad=0.1)
    return fig


# ---------------------------------------------------------------------------
# Figure 4 — Slab weight pathways (detail)
# ---------------------------------------------------------------------------

def generate_matplotlib_stability_detail(graph: Graph) -> Figure:  # noqa: ARG001
    """
    Generate the slab weight pathway detail figure.

    Shows density + thickness → W, W + slope angle → W_s, and
    W_s + E + ν → slab weight_shear with elasticity. Width = 7.0 in
    (double column).

    Parameters
    ----------
    graph : Graph
        Unused.

    Returns
    -------
    Figure
    """
    fig, ax = _new_fig(_DOUBLE_COL, 3.2)

    BW, BH = 0.13, 0.10
    MW, MH = 0.18, 0.10

    C0, C1, C2, C3, C4 = 0.08, 0.27, 0.48, 0.70, 0.90

    inp: Dict[str, _Box] = {
        "thick": _Box("layer\nthickness", C0, 0.70, BW, BH, _COLORS["input"], _EDGE_COLORS["input"]),
        "angle": _Box("slope\nangle", C0, 0.42, BW, BH, _COLORS["input"], _EDGE_COLORS["input"]),
    }

    layer_params: Dict[str, _Box] = {
        "rho": _Box("ρ (density)", C1, 0.76, BW, BH, _COLORS["layer"], _EDGE_COLORS["layer"]),
        "E": _Box("E", C1, 0.54, BW, BH, _COLORS["layer"], _EDGE_COLORS["layer"]),
        "nu": _Box("ν", C1, 0.34, BW, BH, _COLORS["layer"], _EDGE_COLORS["layer"]),
    }

    merges: Dict[str, _Box] = {
        "m_weight": _Box("ρ + h_i", C2, 0.72, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
        "m_shear": _Box("W + slope", C2, 0.44, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
        "m_elastic": _Box("W_s + E + ν", C3, 0.44, MW, MH, _COLORS["merge"], _EDGE_COLORS["merge"]),
    }

    outputs: Dict[str, _Box] = {
        "W": _Box("slab weight\n(W)", C3, 0.72, BW, BH*1.25, _COLORS["slab"], _EDGE_COLORS["slab"], bold=True),
        "Ws": _Box("slab weight_shear\n(W_s)", C3, 0.22, BW*1.25, BH*1.25, _COLORS["slab"], _EDGE_COLORS["slab"], fontsize=6.4, bold=True),
        "Wse": _Box("slab weight_shear\nwith elasticity", C4, 0.44, BW*1.35, BH*1.35, _COLORS["slab"], _EDGE_COLORS["slab"], fontsize=6.4, bold=True),
    }

    all_boxes = {**inp, **layer_params, **merges, **outputs}
    for box in all_boxes.values():
        _draw_box(ax, box)

    ac = "#555555"
    mc = _EDGE_COLORS["merge"]

    _draw_arrow(ax, layer_params["rho"].x + BW/2, layer_params["rho"].y,
                merges["m_weight"].x - MW/2, merges["m_weight"].y, color=mc)
    _draw_arrow(ax, inp["thick"].x + BW/2, inp["thick"].y,
                merges["m_weight"].x - MW/2, merges["m_weight"].y,
                color=mc, connectionstyle="arc3,rad=-0.12")
    _draw_arrow(ax, merges["m_weight"].x + MW/2, merges["m_weight"].y,
                outputs["W"].x - BW/2, outputs["W"].y,
                label="W", color=ac, fontsize=5.0)

    _draw_arrow(ax, outputs["W"].x, outputs["W"].y - BH*0.63,
                merges["m_shear"].x + MW*0.15, merges["m_shear"].y + MH/2,
                color=mc, connectionstyle="arc3,rad=-0.20")
    _draw_arrow(ax, inp["angle"].x + BW/2, inp["angle"].y,
                merges["m_shear"].x - MW/2, merges["m_shear"].y,
                color=mc)
    _draw_arrow(ax, merges["m_shear"].x + MW/2, merges["m_shear"].y,
                outputs["Ws"].x - BW/2, outputs["Ws"].y,
                label="W_s", color=ac, fontsize=5.0,
                connectionstyle="arc3,rad=-0.22")

    _draw_arrow(ax, outputs["Ws"].x + BW*0.63, outputs["Ws"].y,
                merges["m_elastic"].x - MW/2, merges["m_elastic"].y,
                color=mc, connectionstyle="arc3,rad=0.16")
    _draw_arrow(ax, layer_params["E"].x + BW/2, layer_params["E"].y,
                merges["m_elastic"].x - MW/2, merges["m_elastic"].y,
                color=mc, connectionstyle="arc3,rad=-0.10")
    _draw_arrow(ax, layer_params["nu"].x + BW/2, layer_params["nu"].y,
                merges["m_elastic"].x - MW/2, merges["m_elastic"].y,
                color=mc, connectionstyle="arc3,rad=0.12")
    _draw_arrow(ax, merges["m_elastic"].x + MW/2, merges["m_elastic"].y,
                outputs["Wse"].x - BW*0.68, outputs["Wse"].y,
                label="W_s+Eν", color=ac, fontsize=4.8)

    fig.tight_layout(pad=0.1)
    return fig


# ---------------------------------------------------------------------------
# Figure 5 — Full detail (all 35 nodes, bifurcating layout)
# ---------------------------------------------------------------------------

# Short method abbreviations (mirrors _METHOD_ABBREV in visualize.py).
_METHOD_ABBREV = {
    "geldsetzer":             "G09",
    "kim_jamieson_table2":    "KJ-t2",
    "kim_jamieson_table5":    "KJ-t5",
    "bergfeld":               "B23",
    "kochle":                 "K14",
    "wautier":                "W15",
    "schottner":              "S26",
    "srivastava":             "Sr16",
    "lame_relationship":      "Lam",
    "weissgraeber_rosendahl": "W&R",
    "sum_layer_weight":       "W",
    "slope_parallel_component": "W_s",
    "combine_shear_weight_and_elasticity": "W_s+Eν",
}

# Node labels with Greek symbols — mirrors _NODE_LABELS in visualize.py but
# omits (measured) suffixes (they're conveyed by colour).
_FULL_LABELS = {
    "snow_pit":                                    "snow pit",
    "measured_density":                            "ρ (meas.)",
    "measured_hand_hardness":                      "hand\nhardness",
    "measured_grain_form":                         "grain\nform",
    "measured_grain_size":                         "grain\nsize",
    "measured_layer_thickness":                    "layer\nthickness",
    "measured_slope_angle":                        "slope\nangle",
    "merge_hand_hardness_grain_form":              "HH+GF",
    "merge_hand_hardness_grain_form_grain_size":   "HH+GF\n+GS",
    "merge_density_grain_form":                    "ρ+GF",
    "merge_elastic_modulus_poissons_ratio":        "E+ν\n(layer)",
    "density":                                     "ρ",
    "elastic_modulus":                             "E",
    "poissons_ratio":                              "ν",
    "shear_modulus":                               "G",
    "merge_E_nu":                                  "E+ν",
    "merge_hi_G":                                  "h_i+G",
    "merge_hi_E_nu":                               "h_i+E+ν",
    "A11":                                         "A₁₁",
    "B11":                                         "B₁₁",
    "D11":                                         "D₁₁",
    "A55":                                         "A₅₅",
    "merge_slab_weight_inputs":                    "ρ+h_i",
    "slab_weight":                                 "W",
    "merge_slab_weight_slope_angle":               "W+slope",
    "slab_weight_shear":                           "W_s",
    "merge_slab_weight_shear_elasticity":          "W_s+E+ν",
    "slab_weight_shear_with_elasticity":          "W_s\n+E+ν",
}

# Colour for each node (by parameter name) — matches category colours.
_FULL_COLORS = {
    "snow_pit":                                  (_COLORS["root"],       _EDGE_COLORS["root"]),
    "measured_density":                          (_COLORS["input"],      _EDGE_COLORS["input"]),
    "measured_hand_hardness":                    (_COLORS["input"],      _EDGE_COLORS["input"]),
    "measured_grain_form":                       (_COLORS["input"],      _EDGE_COLORS["input"]),
    "measured_grain_size":                       (_COLORS["input"],      _EDGE_COLORS["input"]),
    "measured_layer_thickness":                  (_COLORS["input"],      _EDGE_COLORS["input"]),
    "measured_slope_angle":                      (_COLORS["input"],      _EDGE_COLORS["input"]),
    "merge_hand_hardness_grain_form":            (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "merge_hand_hardness_grain_form_grain_size": (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "merge_density_grain_form":                  (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "merge_elastic_modulus_poissons_ratio":      (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "density":                                   (_COLORS["layer"],      _EDGE_COLORS["layer"]),
    "elastic_modulus":                           (_COLORS["layer"],      _EDGE_COLORS["layer"]),
    "poissons_ratio":                            (_COLORS["layer"],      _EDGE_COLORS["layer"]),
    "shear_modulus":                             (_COLORS["layer"],      _EDGE_COLORS["layer"]),
    "merge_E_nu":                                (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "merge_hi_G":                                (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "merge_hi_E_nu":                             (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "A11":                                       (_COLORS["slab"],       _EDGE_COLORS["slab"]),
    "B11":                                       (_COLORS["slab"],       _EDGE_COLORS["slab"]),
    "D11":                                       (_COLORS["slab"],       _EDGE_COLORS["slab"]),
    "A55":                                       (_COLORS["slab"],       _EDGE_COLORS["slab"]),
    "merge_slab_weight_inputs":                  (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "slab_weight":                               (_COLORS["slab"],       _EDGE_COLORS["slab"]),
    "merge_slab_weight_slope_angle":             (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "slab_weight_shear":                         (_COLORS["slab"],       _EDGE_COLORS["slab"]),
    "merge_slab_weight_shear_elasticity":        (_COLORS["merge"],      _EDGE_COLORS["merge"]),
    "slab_weight_shear_with_elasticity":         (_COLORS["slab"],       _EDGE_COLORS["slab"]),
}

# Manual (x, y) positions for every node.
# Layout: strict top-to-bottom topological order so every arrow descends in y.
#   Slab pipeline on the LEFT  (x ≤ 0.50)
#   Stability pipeline on the RIGHT (x > 0.50)
# y=1 is top, y=0 is bottom (matplotlib axes fraction).
#
# Row summary (y values):
#   0.91  snow_pit
#   0.82  measured inputs
#   0.73  merge_HH_GF, merge_HH_GF_GS
#   0.64  density
#   0.55  merge_density_grain_form
#   0.46  elastic_modulus, poissons_ratio
#   0.37  merge_elastic_modulus_poissons_ratio (layer E+ν→G), merge_E_nu
#   0.28  shear_modulus, merge_hi_E_nu, merge_slab_weight_inputs, slab_weight
#   0.19  merge_hi_G, merge_slab_weight_slope_angle, slab_weight_shear
#   0.10  D11, A11, B11, A55, merge_slab_weight_shear_elasticity,
#         slab_weight_shear_with_elasticity
_FULL_POSITIONS: Dict[str, Tuple[float, float]] = {
    # ── Root ──────────────────────────────────────────────────────────────
    "snow_pit":                                  (0.50, 0.91),

    # ── Measured inputs ───────────────────────────────────────────────────
    "measured_density":                          (0.10, 0.82),
    "measured_hand_hardness":                    (0.25, 0.82),
    "measured_grain_form":                       (0.50, 0.82),
    "measured_grain_size":                       (0.64, 0.82),
    "measured_layer_thickness":                  (0.80, 0.82),
    "measured_slope_angle":                      (0.93, 0.82),

    # ── Density merge nodes ───────────────────────────────────────────────
    "merge_hand_hardness_grain_form":            (0.22, 0.73),
    "merge_hand_hardness_grain_form_grain_size": (0.35, 0.73),

    # ── Density ───────────────────────────────────────────────────────────
    "density":                                   (0.10, 0.64),

    # ── Density + grain_form merge ────────────────────────────────────────
    "merge_density_grain_form":                  (0.24, 0.55),

    # ── Elastic modulus and Poisson's ratio ───────────────────────────────
    "elastic_modulus":                           (0.13, 0.46),
    "poissons_ratio":                            (0.25, 0.46),

    # ── Row y=0.37: three merge nodes feeding the slab/stability pipelines ─
    # Layer E+ν merge → shear modulus G
    "merge_elastic_modulus_poissons_ratio":      (0.19, 0.37),
    # Slab E+ν merge → merge_hi_E_nu → A11/B11/D11
    "merge_E_nu":                                (0.36, 0.37),

    # ── Row y=0.28: shear modulus, slab h+E+ν merge, slab weight ─
    "shear_modulus":                             (0.12, 0.28),
    "merge_hi_E_nu":                             (0.28, 0.28),
    "merge_slab_weight_inputs":                  (0.66, 0.55),
    "slab_weight":                               (0.66, 0.43),

    # ── Row y=0.19: slab h+G merge and slope-parallel weight ─────────────
    "merge_hi_G":                                (0.42, 0.19),
    "merge_slab_weight_slope_angle":             (0.78, 0.31),
    "slab_weight_shear":                         (0.78, 0.19),
    "merge_slab_weight_shear_elasticity":        (0.78, 0.10),

    # ── Row y=0.10: all outputs ───────────────────────────────────────────
    "D11":                                       (0.06, 0.10),
    "A11":                                       (0.18, 0.10),
    "B11":                                       (0.30, 0.10),
    "A55":                                       (0.42, 0.10),
    "slab_weight_shear_with_elasticity":          (0.93, 0.10),
}


def _draw_full_box(ax: plt.Axes, param: str, BW: float = 0.075, BH: float = 0.060) -> None:
    """Draw a single node box for the full-detail figure."""
    x, y = _FULL_POSITIONS[param]
    fill, edge = _FULL_COLORS.get(param, ("#ffffff", "#888888"))
    label = _FULL_LABELS.get(param, param)
    x0, y0 = x - BW / 2, y - BH / 2
    patch = FancyBboxPatch(
        (x0, y0), BW, BH,
        boxstyle="round,pad=0",
        facecolor=fill,
        edgecolor=edge,
        linewidth=0.8,
        transform=ax.transAxes,
        clip_on=False,
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(
        x, y, label,
        ha="center", va="center",
        fontsize=5.5, transform=ax.transAxes,
        zorder=3,
    )


def _draw_full_arrow(
    ax: plt.Axes,
    start_param: str,
    end_param: str,
    label: str = "",
    BW: float = 0.075,
    BH: float = 0.060,
    connectionstyle: str = "arc3,rad=0.0",
) -> None:
    """Draw an arrow between two named nodes in the full-detail figure."""
    x0, y0 = _FULL_POSITIONS[start_param]
    x1, y1 = _FULL_POSITIONS[end_param]

    # All arrows exit from the bottom-centre of the source node and
    # enter the top-centre of the destination node, so the diagram reads
    # top-to-bottom consistently.
    y0 -= BH / 2
    y1 += BH / 2

    # Edge colour: use destination node's edge colour
    _, ec = _FULL_COLORS.get(end_param, ("#888888", "#555555"))

    ax.annotate(
        "",
        xy=(x1, y1), xycoords="axes fraction",
        xytext=(x0, y0), textcoords="axes fraction",
        arrowprops=dict(
            arrowstyle="-|>",
            color=ec,
            lw=0.6,
            connectionstyle=connectionstyle,
        ),
        zorder=1,
    )

    if label:
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2
        ax.text(
            mx, my, label,
            ha="center", va="center",
            fontsize=4.5, color=ec,
            transform=ax.transAxes,
            zorder=4,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.3),
        )


def generate_matplotlib_full_detail(graph: Graph) -> Figure:
    """
    Generate a full-detail figure showing every node in the parameter graph.

    All nodes are drawn including all merge nodes.  Greek symbols are used
    for parameter labels.  Method names are abbreviated on edges.  A bifurcating
    layout separates the stiffness pipeline (left) from the slab-weight
    pipeline (right), with shared measured inputs at the top centre.

    Width = 7.0 in (double column), Height = 9.5 in.  DPI = 300.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.

    Returns
    -------
    Figure
    """
    fig, ax = _new_fig(_DOUBLE_COL, 9.5)

    # Draw all boxes
    for param in _FULL_POSITIONS:
        _draw_full_box(ax, param)

    # Draw group background rectangles (subtle shading to help the eye).
    # Each group is a semi-transparent filled rectangle behind its nodes.
    _group_rects = [
        # (x_centre, y_centre, width, height, colour, label)
        #
        # Snow Pit Observations: snow_pit(0.50,0.91) + measured inputs(y=0.82).
        # Top of rect = 0.985, label at 0.973 — above snow_pit box top (0.94).
        (0.50,  0.885, 0.98, 0.20,  "#FFFDE7", "Snow Pit Observations"),
        #
        # Layer Parameters: HH merges(0.73), density(0.64), merge_d_gf(0.55),
        # E/ν(0.46), merge_E_nu_layer(0.37), G(0.28).
        # x: 0.04–0.34, y: 0.24–0.77
        (0.19,  0.505, 0.32, 0.56,  "#E8F5E9", "Layer Parameters"),
        #
        # Slab Stiffnesses: D11(0.06), A11(0.18), B11(0.30), A55(0.42) at y=0.10.
        # Merge nodes are not boxed separately.
        (0.24,  0.10,  0.48, 0.12,  "#FFE0B2", "Slab Stiffnesses"),
        #
        # Slab Weight Pathways: W, W_s, and W_s+E+ν.
        (0.77,  0.31,  0.42, 0.56,  "#FCE4EC", "Slab Weight Pathways"),
    ]
    for gx, gy, gw, gh, gc, glbl in _group_rects:
        x0, y0 = gx - gw / 2, gy - gh / 2
        bg = FancyBboxPatch(
            (x0, y0), gw, gh,
            boxstyle="round,pad=0.005",
            facecolor=gc, edgecolor="#cccccc",
            linewidth=0.5, alpha=0.5,
            transform=ax.transAxes, clip_on=False,
            zorder=0,
        )
        ax.add_patch(bg)
        ax.text(
            gx, y0 + gh - 0.012, glbl,
            ha="center", va="top",
            fontsize=5.0, color="#666666",
            fontstyle="italic",
            transform=ax.transAxes, zorder=0,
        )

    # Draw all edges extracted from the graph
    for edge in graph.edges:
        sp = edge.start.parameter
        ep = edge.end.parameter
        if sp not in _FULL_POSITIONS or ep not in _FULL_POSITIONS:
            continue
        lbl = ""
        if edge.method_name:
            lbl = _METHOD_ABBREV.get(edge.method_name, edge.method_name)

        # Choose curved arrows for edges that would otherwise cross other nodes.
        x0, y0 = _FULL_POSITIONS[sp]
        x1, y1 = _FULL_POSITIONS[ep]
        dx, dy = x1 - x0, y1 - y0

        # Curvature overrides.  With all arrows exiting the bottom of the source
        # and entering the top of the destination, most short-range connections
        # stay straight (rad=0.0).  Overrides are needed only for long
        # cross-pipeline arrows that would otherwise overlap other nodes.
        cs = "arc3,rad=0.0"

        # layer_thickness → merge_hi_E_nu / merge_hi_G: long leftward diagonals;
        # arc inward (negative = clockwise for a mostly-downward path) to keep
        # them away from the slab merge nodes in the centre.
        if sp == "measured_layer_thickness" and ep in ("merge_hi_E_nu", "merge_hi_G"):
            cs = "arc3,rad=-0.20"
        # layer_thickness → slab weight: long rightward cross-pipeline arrow.
        elif sp == "measured_layer_thickness" and ep == "merge_slab_weight_inputs":
            cs = "arc3,rad=-0.15"
        # density → slab weight: long rightward cross-pipeline arrow.
        elif sp == "density" and ep == "merge_slab_weight_inputs":
            cs = "arc3,rad=0.25"
        elif sp == "measured_slope_angle" and ep == "merge_slab_weight_slope_angle":
            cs = "arc3,rad=-0.20"
        elif sp in ("elastic_modulus", "poissons_ratio") and ep == "merge_slab_weight_shear_elasticity":
            cs = "arc3,rad=-0.25"
        elif sp == "slab_weight_shear" and ep == "merge_slab_weight_shear_elasticity":
            cs = "arc3,rad=0.0"

        _draw_full_arrow(ax, sp, ep, label=lbl, connectionstyle=cs)

    # Legend (bottom-right corner)
    legend_items = [
        (_COLORS["root"],       _EDGE_COLORS["root"],       "Root"),
        (_COLORS["input"],      _EDGE_COLORS["input"],      "Measured input"),
        (_COLORS["merge"],      _EDGE_COLORS["merge"],      "Merge node"),
        (_COLORS["layer"],      _EDGE_COLORS["layer"],      "Layer parameter"),
        (_COLORS["slab"],       _EDGE_COLORS["slab"],       "Slab parameter"),
    ]
    lx, ly = 0.57, 0.08
    row_h = 0.013
    for i, (fc, ec, lbl) in enumerate(legend_items):
        cy = ly - i * row_h
        patch = FancyBboxPatch(
            (lx, cy - 0.004), 0.025, 0.009,
            boxstyle="round,pad=0",
            facecolor=fc, edgecolor=ec,
            linewidth=0.6,
            transform=ax.transAxes, clip_on=False,
            zorder=5,
        )
        ax.add_patch(patch)
        ax.text(
            lx + 0.030, cy, lbl,
            ha="left", va="center",
            fontsize=5.0,
            transform=ax.transAxes, zorder=5,
        )

    fig.tight_layout(pad=0.1)
    return fig


# ---------------------------------------------------------------------------
# Convenience save function
# ---------------------------------------------------------------------------

def save_matplotlib_diagrams(graph: Graph, output_dir: str, dpi: int = _DPI) -> None:
    """
    Generate and save all five matplotlib figures to *output_dir*.

    Files written:
    - ``overview.png``
    - ``layer_params.png``
    - ``slab_params.png``
    - ``stability.png``
    - ``full.png``

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.
    output_dir : str
        Directory path.  Created if it does not exist.
    dpi : int, optional
        Output resolution (default 300).
    """
    os.makedirs(output_dir, exist_ok=True)

    tasks = [
        ("overview.png",    generate_matplotlib_overview),
        ("layer_params.png", generate_matplotlib_layer_detail),
        ("slab_params.png",  generate_matplotlib_slab_detail),
        ("stability.png",    generate_matplotlib_stability_detail),
        ("full.png",         generate_matplotlib_full_detail),
    ]
    for filename, generator in tasks:
        fig = generator(graph)
        path = os.path.join(output_dir, filename)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {path}")
