"""Shared figure and table helpers for the mech params paper notebooks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from notebook_utils import (
    DENSITY_COLORS,
    DOUBLE_COL,
    DPI,
    PAPER_FIGURES_DIR,
    SINGLE_COL,
)
from snowpyt_mechparams.constants import E_ICE_POLYCRYSTALLINE, RHO_ICE
from snowpyt_mechparams.graph.visualize_matplotlib import generate_matplotlib_full_detail


COLOR_INPUT = "#F8E59A"
COLOR_LAYER = "#BFDDB7"
COLOR_SLAB = "#F5C0A8"
COLOR_MERGE = "#E8D4EF"
COLOR_TARGET = "#EBD8E6"
COLOR_ALERT = "#F8E6BF"
COLOR_BORDER = "#404040"
GRID_COLOR = "#D8D8D8"

RHO_ICE_VALUE = float(getattr(RHO_ICE, "nominal_value", RHO_ICE))
E_ICE_VALUE = float(getattr(E_ICE_POLYCRYSTALLINE, "nominal_value", E_ICE_POLYCRYSTALLINE))

DENSITY_METHOD_ORDER = [
    "kim_jamieson_table2",
    "geldsetzer",
    "kim_jamieson_table5",
    "data_flow",
]

METHOD_LABELS = {
    "data_flow": "Direct matched density",
    "geldsetzer": "Geldsetzer and Jamieson (2000)",
    "kim_jamieson_table2": "Kim and Jamieson Table 2",
    "kim_jamieson_table5": "Kim and Jamieson Table 5",
    "bergfeld": "Bergfeld et al. (2023)",
    "kochle": "Kochle and Schneebeli (2014)",
    "wautier": "Wautier et al. (2015)",
    "schottner": "Schottner et al. (2026)",
    "srivastava": "Srivastava et al. (2016)",
}

METHOD_SHORT_LABELS = {
    "data_flow": "Direct",
    "geldsetzer": "Geldsetzer",
    "kim_jamieson_table2": "Kim T2",
    "kim_jamieson_table5": "Kim T5",
    "bergfeld": "Bergfeld",
    "kochle": "Kochle",
    "wautier": "Wautier",
    "schottner": "Schottner",
    "srivastava": "Srivastava",
}


def paper_figures_dir() -> Path:
    """Return the LaTeX paper figures directory."""
    PAPER_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return PAPER_FIGURES_DIR


def save_paper_figure(fig: plt.Figure, stem: str, close: bool = False) -> dict[str, Path]:
    """Save a figure to the paper figures directory as PDF and PNG."""
    output_dir = paper_figures_dir()
    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, dpi=DPI, bbox_inches="tight")
    fig.savefig(png_path, dpi=DPI, bbox_inches="tight")
    if close:
        plt.close(fig)
    return {"pdf": pdf_path, "png": png_path}


def method_label(method: str, short: bool = False) -> str:
    """Return a paper-friendly method label."""
    lookup = METHOD_SHORT_LABELS if short else METHOD_LABELS
    return lookup.get(method, method.replace("_", " "))


def format_method_path(
    density_method: str,
    emod_method: str | None = None,
    nu_method: str | None = None,
    *,
    short: bool = False,
) -> str:
    """Return a density -> E -> nu path label."""
    labels = [method_label(density_method, short=short)]
    if emod_method is not None:
        labels.append(method_label(emod_method, short=short))
    if nu_method is not None:
        labels.append(method_label(nu_method, short=short))
    return " -> ".join(labels)


def density_legend_handles() -> list[mpatches.Patch]:
    """Build legend handles for density method colors."""
    handles = []
    for method in DENSITY_METHOD_ORDER:
        handles.append(
            mpatches.Patch(
                facecolor=DENSITY_COLORS[method],
                edgecolor=COLOR_BORDER,
                label=method_label(method),
                alpha=0.85,
            )
        )
    return handles


def _setup_publication_axes(ax: plt.Axes, *, x_grid: bool = True, y_grid: bool = False) -> None:
    """Apply a light publication grid and spine cleanup."""
    if x_grid:
        ax.grid(True, axis="x", color=GRID_COLOR, linewidth=0.6)
    if y_grid:
        ax.grid(True, axis="y", color=GRID_COLOR, linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def _add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    *,
    facecolor: str,
    edgecolor: str,
    linewidth: float = 1.5,
    fontsize: float = 9,
    fontweight: str = "normal",
    linestyle: str = "-",
    zorder: int = 2,
) -> None:
    """Add a rounded rectangle with centered text in axes coordinates."""
    rect = mpatches.FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        transform=ax.transAxes,
        zorder=zorder,
    )
    ax.add_patch(rect)
    ax.text(
        x,
        y,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=fontweight,
        transform=ax.transAxes,
        zorder=zorder + 1,
    )


def _add_diamond(
    ax: plt.Axes,
    x: float,
    y: float,
    size: float,
    label: str,
    *,
    facecolor: str = COLOR_MERGE,
    edgecolor: str = COLOR_BORDER,
    fontsize: float = 8,
) -> None:
    """Add a merge diamond."""
    verts = np.array(
        [
            [x, y + size / 2],
            [x + size / 2, y],
            [x, y - size / 2],
            [x - size / 2, y],
        ]
    )
    poly = mpatches.Polygon(
        verts,
        closed=True,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.4,
        transform=ax.transAxes,
        zorder=2,
    )
    ax.add_patch(poly)
    ax.text(x, y, label, ha="center", va="center", fontsize=fontsize, transform=ax.transAxes, zorder=3)


def _add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = COLOR_BORDER,
    linewidth: float = 1.3,
    linestyle: str = "-",
    connectionstyle: str = "arc3,rad=0.0",
    zorder: int = 1,
) -> None:
    """Add an arrow between two axes-fraction points."""
    arrow = mpatches.FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=linewidth,
        linestyle=linestyle,
        color=color,
        connectionstyle=connectionstyle,
        transform=ax.transAxes,
        zorder=zorder,
    )
    ax.add_patch(arrow)


def build_intro_workflow_figure() -> plt.Figure:
    """Create the introduction workflow figure."""
    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 2.75))
    ax.axis("off")

    scope = mpatches.FancyBboxPatch(
        (0.22, 0.17),
        0.62,
        0.63,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        facecolor="#FBF5F6",
        edgecolor="#B34F7B",
        linewidth=2.0,
        transform=ax.transAxes,
        zorder=0,
    )
    ax.add_patch(scope)
    ax.text(
        0.23,
        0.82,
        "Scope of this paper: slab-side input assembly",
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color="#8C3158",
        transform=ax.transAxes,
    )

    _add_box(
        ax,
        0.10,
        0.50,
        0.18,
        0.28,
        "Snowpit\nobservations\n\n density\n hardness\n grain form\n grain size\n thickness",
        facecolor=COLOR_INPUT,
        edgecolor="#C78B00",
        fontsize=8,
        fontweight="bold",
    )
    _add_box(
        ax,
        0.34,
        0.50,
        0.18,
        0.28,
        "Layer\nparameterizations\n\n density\n E\n nu\n G",
        facecolor=COLOR_LAYER,
        edgecolor="#4E8A53",
        fontsize=8,
        fontweight="bold",
    )
    _add_box(
        ax,
        0.56,
        0.50,
        0.18,
        0.28,
        "Slab properties\nand inputs\n\n thickness\n A11, B11\n D11, A55",
        facecolor=COLOR_SLAB,
        edgecolor="#BC6B52",
        fontsize=8,
        fontweight="bold",
    )
    _add_box(
        ax,
        0.80,
        0.62,
        0.16,
        0.18,
        "Roch\nslab-side\ninputs",
        facecolor=COLOR_TARGET,
        edgecolor="#8C3158",
        fontsize=9,
        fontweight="bold",
    )
    _add_box(
        ax,
        0.80,
        0.38,
        0.16,
        0.18,
        "WEAC\nslab-side\ninputs",
        facecolor=COLOR_TARGET,
        edgecolor="#8C3158",
        fontsize=9,
        fontweight="bold",
    )
    _add_box(
        ax,
        0.56,
        0.16,
        0.18,
        0.12,
        "Weak-layer inputs\nkept unresolved here",
        facecolor=COLOR_ALERT,
        edgecolor="#B78423",
        linestyle="--",
        fontsize=8,
    )

    _add_arrow(ax, (0.19, 0.50), (0.25, 0.50))
    _add_arrow(ax, (0.43, 0.50), (0.47, 0.50))
    _add_arrow(ax, (0.65, 0.54), (0.72, 0.60))
    _add_arrow(ax, (0.65, 0.46), (0.72, 0.40))
    _add_arrow(ax, (0.65, 0.18), (0.72, 0.57), linestyle="--", color="#8B8B8B", connectionstyle="arc3,rad=0.25")
    _add_arrow(ax, (0.65, 0.14), (0.72, 0.41), linestyle="--", color="#8B8B8B", connectionstyle="arc3,rad=-0.10")

    ax.text(0.68, 0.70, "full stability models also require", fontsize=7.5, color="#666666", transform=ax.transAxes)

    fig.tight_layout(pad=0.3)
    return fig


def build_snowpylot_data_model_figure() -> plt.Figure:
    """Create a simplified SnowPylot data model figure."""
    fig, ax = plt.subplots(figsize=(SINGLE_COL, 4.0))
    ax.axis("off")

    _add_box(
        ax,
        0.50,
        0.85,
        0.34,
        0.14,
        "SnowPit\n1 CAAML file -> 1 parsed object",
        facecolor="#E7EFFA",
        edgecolor="#3B6AA0",
        fontsize=9,
        fontweight="bold",
    )

    children = [
        (0.20, 0.56, "Metadata\n pit_id\n location\n slope angle"),
        (0.50, 0.56, "Layers\n thickness\n hand hardness\n grain form\n grain size"),
        (0.80, 0.56, "Matched density\n observations\n direct layer density\n aligned depth + thickness"),
        (0.50, 0.22, "Stability tests\n ECT\n CT\n PST"),
    ]
    for x, y, label in children:
        _add_box(
            ax,
            x,
            y,
            0.24,
            0.18 if y > 0.30 else 0.16,
            label,
            facecolor=COLOR_INPUT,
            edgecolor="#C78B00",
            fontsize=8,
        )

    for x, y, _label in children[:3]:
        _add_arrow(ax, (0.50, 0.78), (x, y + 0.10))
    _add_arrow(ax, (0.50, 0.78), (0.50, 0.30))

    note = mpatches.FancyBboxPatch(
        (0.08, 0.02),
        0.84,
        0.10,
        boxstyle="round,pad=0.01,rounding_size=0.018",
        facecolor="#F7F7F7",
        edgecolor="#BDBDBD",
        linewidth=1.0,
        transform=ax.transAxes,
    )
    ax.add_patch(note)
    ax.text(
        0.50,
        0.07,
        "This study uses the SnowPit fields needed to build layer objects,\nmatch direct density to layers, and extract propagating ECT slabs.",
        ha="center",
        va="center",
        fontsize=7.2,
        color="#555555",
        transform=ax.transAxes,
    )

    fig.tight_layout(pad=0.3)
    return fig


def build_mechparams_data_model_figure() -> plt.Figure:
    """Create a simplified Pit-Slab-Layer data model figure."""
    fig, ax = plt.subplots(figsize=(SINGLE_COL, 5.6))
    ax.axis("off")

    _add_box(
        ax,
        0.27,
        0.82,
        0.34,
        0.16,
        "Pit\n\n measured:\n pit_id, slope_angle\n layers, ECT_results\n\n action:\n from_snow_pit(...)",
        facecolor="#E7EFFA",
        edgecolor="#3B6AA0",
        fontsize=8,
        fontweight="bold",
    )
    _add_box(
        ax,
        0.73,
        0.82,
        0.34,
        0.20,
        "Slab\n\n measured:\n angle, weak_layer, layers\n\n calculated:\n A11, B11, D11, A55\n\n action:\n create_slabs(...)",
        facecolor=COLOR_SLAB,
        edgecolor="#BC6B52",
        fontsize=8,
        fontweight="bold",
    )
    _add_box(
        ax,
        0.50,
        0.34,
        0.46,
        0.34,
        "Layer\n\n measured:\n depth_top, thickness, density_measured\n hand_hardness, grain_form, grain_size_avg\n\n calculated:\n density_calculated, elastic_modulus\n poissons_ratio, shear_modulus",
        facecolor=COLOR_LAYER,
        edgecolor="#4E8A53",
        fontsize=8,
        fontweight="bold",
    )

    _add_arrow(ax, (0.44, 0.82), (0.56, 0.82))
    _add_arrow(ax, (0.30, 0.72), (0.43, 0.50), connectionstyle="arc3,rad=-0.12")
    _add_arrow(ax, (0.70, 0.72), (0.57, 0.50), connectionstyle="arc3,rad=0.12")

    ax.text(0.50, 0.86, "Pit.from_snow_pit(...) then Pit.create_slabs(...)", ha="center", fontsize=7.2, color="#555555", transform=ax.transAxes)
    ax.text(0.50, 0.58, "all slab pathways execute through the layer fields above", ha="center", fontsize=7.2, color="#555555", transform=ax.transAxes)

    fig.tight_layout(pad=0.3)
    return fig


HARDNESS_MAPPING = {
    "F-": 0.67,
    "F": 1.0,
    "F+": 1.33,
    "4F-": 1.67,
    "4F": 2.0,
    "4F+": 2.33,
    "1F-": 2.67,
    "1F": 3.0,
    "1F+": 3.33,
    "P-": 3.67,
    "P": 4.0,
    "P+": 4.33,
    "K-": 4.67,
    "K": 5.0,
    "K+": 5.33,
}

GRAIN_FORM_RANGES = [
    ("PP", "Precipitation particles", "F- to P", "F- to P"),
    ("PPgp", "Precipitation particles, graupel", "F- to P", "F- to P"),
    ("DF", "Decomposing and fragmented particles", "F- to P+", "F- to K-"),
    ("RG", "Rounded grains", "F to K+", "F- to K+"),
    ("RGmx", "Rounded grains, mixed forms", "F- to P+", "F- to P+"),
    ("FC", "Faceted crystals", "F- to K-", "F- to K"),
    ("FCmx", "Faceted crystals, mixed forms", "F to K+", "F- to K+"),
    ("DH", "Depth hoar", "F to K", "F to K"),
    ("MFcr", "Melt-freeze crust", "None", "4F to K+"),
]


def _parse_hardness_range(value: str) -> tuple[float | None, float | None]:
    if value.strip().lower() == "none":
        return (None, None)
    low, high = [item.strip() for item in value.split(" to ")]
    return HARDNESS_MAPPING[low], HARDNESS_MAPPING[high]


def build_grain_form_hardness_ranges_figure() -> plt.Figure:
    """Create the grain-form hand-hardness applicability figure."""
    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 3.6))

    gj_color = "#3B78A6"
    kj_color = "#D87745"
    y_positions = np.arange(len(GRAIN_FORM_RANGES))
    half_height = 0.16

    for y, (code, name, gj_range, kj_range) in zip(y_positions, GRAIN_FORM_RANGES, strict=True):
        gj_low, gj_high = _parse_hardness_range(gj_range)
        kj_low, kj_high = _parse_hardness_range(kj_range)

        if gj_low is not None and gj_high is not None:
            ax.barh(
                y - half_height,
                gj_high - gj_low,
                left=gj_low,
                height=0.28,
                color=gj_color,
                alpha=0.85,
                edgecolor="#1F4460",
                linewidth=0.8,
            )
        if kj_low is not None and kj_high is not None:
            ax.barh(
                y + half_height,
                kj_high - kj_low,
                left=kj_low,
                height=0.28,
                color=kj_color,
                alpha=0.80,
                edgecolor="#8B4622",
                linewidth=0.8,
            )

        if gj_low is None and kj_low is not None:
            ax.text(kj_high + 0.06, y + half_height, "Kim only", va="center", ha="left", fontsize=8, color="#8B4622")
        elif gj_low is not None and kj_low is not None and (kj_low < gj_low or kj_high > gj_high):
            ax.text(kj_high + 0.06, y + half_height, "Kim wider", va="center", ha="left", fontsize=8, color="#8B4622")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"{code}  {name}" for code, name, _gj, _kj in GRAIN_FORM_RANGES], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0.45, 5.70)
    ax.set_xticks([1.0, 2.0, 3.0, 4.0, 5.0])
    ax.set_xticklabels(["F", "4F", "1F", "P", "K"])
    ax.set_xlabel("Hand hardness index")
    _setup_publication_axes(ax, x_grid=True, y_grid=False)

    handles = [
        mpatches.Patch(facecolor=gj_color, edgecolor="#1F4460", label="Geldsetzer and Jamieson (2000)", alpha=0.85),
        mpatches.Patch(facecolor=kj_color, edgecolor="#8B4622", label="Kim and Jamieson (2014)", alpha=0.80),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout(pad=0.3)
    return fig


def _bergfeld_curve(rho: np.ndarray) -> np.ndarray:
    return 6.5e3 * (rho / RHO_ICE_VALUE) ** 4.4


def _kochle_low_curve(rho: np.ndarray) -> np.ndarray:
    return 0.0061 * np.exp(0.0396 * rho)


def _kochle_high_curve(rho: np.ndarray) -> np.ndarray:
    return 6.0457 * np.exp(0.011 * rho)


def _wautier_curve(rho: np.ndarray) -> np.ndarray:
    return E_ICE_VALUE * 0.78 * (rho / RHO_ICE_VALUE) ** 2.34


def _schottner_curve(rho: np.ndarray, a: float, n: float) -> np.ndarray:
    return E_ICE_VALUE * a * (rho / RHO_ICE_VALUE) ** n


def build_elastic_modulus_curves_figure() -> plt.Figure:
    """Create the elastic-modulus parameterization figure."""
    rho = np.linspace(100.0, 545.0, 600)

    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 3.25), sharex=True)
    curve_specs = [
        ("Bergfeld", "#0072B2", "-", _bergfeld_curve(rho[(rho >= 110) & (rho <= 363)]), rho[(rho >= 110) & (rho <= 363)], "PP, DF, RG"),
        ("Kochle low", "#A12A6A", "-", _kochle_low_curve(rho[(rho >= 150) & (rho < 250)]), rho[(rho >= 150) & (rho < 250)], "RG, FC, DH, MF"),
        ("Kochle high", "#A12A6A", "--", _kochle_high_curve(rho[(rho >= 250) & (rho <= 450)]), rho[(rho >= 250) & (rho <= 450)], "RG, FC, DH, MF"),
        ("Wautier", "#E69F00", "-", _wautier_curve(rho[(rho >= 103) & (rho <= 544)]), rho[(rho >= 103) & (rho <= 544)], "DF, RG, FC, DH, MF"),
        ("Schottner DF/RG", "#009E73", "-", _schottner_curve(rho, 0.40, 4.6), rho, "DF, RG"),
        ("Schottner FC/DH", "#009E73", "--", _schottner_curve(rho, 1.8, 5.1), rho, "FC, DH"),
        ("Schottner SH", "#009E73", ":", _schottner_curve(rho, 0.011, 1.7), rho, "SH"),
    ]

    for ax in axes:
        for label, color, linestyle, y_values, x_values, grain_forms in curve_specs:
            ax.plot(x_values, y_values, color=color, linestyle=linestyle, linewidth=1.8, label=f"{label} ({grain_forms})")
        ax.set_xlim(100, 550)
        ax.set_xlabel(r"Density, $\rho$ (kg m$^{-3}$)")
        _setup_publication_axes(ax, x_grid=True, y_grid=False)

    axes[0].set_ylabel(r"Elastic modulus, $E$ (MPa)")
    axes[0].set_ylim(0, 950)
    axes[0].text(0.02, 0.96, "(a) Linear scale", transform=axes[0].transAxes, va="top", fontsize=8, fontweight="bold")

    axes[1].set_yscale("log")
    axes[1].set_ylim(0.3, 5000)
    axes[1].text(0.02, 0.96, "(b) Log scale", transform=axes[1].transAxes, va="top", fontsize=8, fontweight="bold")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.50, 1.02), ncol=2, frameon=False, fontsize=7)
    fig.tight_layout(rect=(0, 0, 1, 0.90), pad=0.4)
    return fig


def build_params_graph_figure(graph) -> plt.Figure:
    """Create the full parameter graph figure."""
    fig = generate_matplotlib_full_detail(graph)
    return fig


def build_density_pathways_figure() -> plt.Figure:
    """Create a clean four-path density schematic."""
    fig, axes = plt.subplots(1, 4, figsize=(DOUBLE_COL, 2.25))
    panel_specs = [
        ("Direct matched\ndensity", [("Snow pit", COLOR_INPUT), ("Measured\ndensity", COLOR_INPUT), ("Density", COLOR_LAYER)], []),
        ("Geldsetzer", [("Hand\nhardness", COLOR_INPUT), ("Grain\nform", COLOR_INPUT), ("Density", COLOR_LAYER)], ["merge"]),
        ("Kim and Jamieson\nTable 2", [("Hand\nhardness", COLOR_INPUT), ("Grain\nform", COLOR_INPUT), ("Density", COLOR_LAYER)], ["merge"]),
        ("Kim and Jamieson\nTable 5", [("Hand\nhardness", COLOR_INPUT), ("Grain\nform", COLOR_INPUT), ("Grain\nsize", COLOR_INPUT), ("Density", COLOR_LAYER)], ["merge"]),
    ]

    for ax, (title, boxes, merges) in zip(axes, panel_specs, strict=True):
        ax.axis("off")
        ax.text(0.50, 0.98, title, ha="center", va="top", fontsize=8.2, fontweight="bold", transform=ax.transAxes)

        if title.startswith("Direct"):
            _add_box(ax, 0.18, 0.45, 0.26, 0.16, boxes[0][0], facecolor=boxes[0][1], edgecolor="#C78B00", fontsize=8)
            _add_box(ax, 0.52, 0.45, 0.30, 0.16, boxes[1][0], facecolor=boxes[1][1], edgecolor="#C78B00", fontsize=8)
            _add_box(ax, 0.85, 0.45, 0.22, 0.16, boxes[2][0], facecolor=boxes[2][1], edgecolor="#4E8A53", fontsize=8, fontweight="bold")
            _add_arrow(ax, (0.31, 0.45), (0.37, 0.45))
            _add_arrow(ax, (0.67, 0.45), (0.73, 0.45))
            continue

        x_positions = [0.18, 0.18, 0.18]
        y_positions = [0.62, 0.38, 0.15]
        if len(boxes) == 3:
            for (label, color), y in zip(boxes[:2], y_positions[:2], strict=True):
                _add_box(ax, x_positions[0], y, 0.28, 0.15, label, facecolor=color, edgecolor="#C78B00", fontsize=8)
            _add_diamond(ax, 0.52, 0.50, 0.16, "+", fontsize=10)
            _add_box(ax, 0.84, 0.50, 0.22, 0.16, boxes[2][0], facecolor=boxes[2][1], edgecolor="#4E8A53", fontsize=8, fontweight="bold")
            _add_arrow(ax, (0.32, 0.62), (0.45, 0.54))
            _add_arrow(ax, (0.32, 0.38), (0.45, 0.46))
            _add_arrow(ax, (0.60, 0.50), (0.72, 0.50))
        else:
            for (label, color), y in zip(boxes[:3], y_positions, strict=True):
                _add_box(ax, x_positions[0], y, 0.28, 0.15, label, facecolor=color, edgecolor="#C78B00", fontsize=8)
            _add_diamond(ax, 0.52, 0.39, 0.16, "+", fontsize=10)
            _add_box(ax, 0.84, 0.39, 0.22, 0.16, boxes[3][0], facecolor=boxes[3][1], edgecolor="#4E8A53", fontsize=8, fontweight="bold")
            _add_arrow(ax, (0.32, 0.62), (0.45, 0.45))
            _add_arrow(ax, (0.32, 0.38), (0.45, 0.39))
            _add_arrow(ax, (0.32, 0.15), (0.45, 0.33))
            _add_arrow(ax, (0.60, 0.39), (0.72, 0.39))

    fig.tight_layout(pad=0.4, w_pad=0.7)
    return fig


def build_coverage_comparison_figure(
    roch_cov: pd.DataFrame,
    weac_cov: pd.DataFrame,
    total_slabs: int,
    *,
    top_n: int = 12,
) -> plt.Figure:
    """Create the Roch vs WEAC coverage comparison figure."""
    roch_plot = roch_cov.sort_values("n_all_inputs").copy()
    weac_plot = weac_cov.head(top_n).copy().sort_values("n_all_inputs")
    weac_plot["label"] = [
        format_method_path(dm, em, nu, short=True)
        for dm, em, nu in zip(
            weac_plot["density_method"],
            weac_plot["emod_method"],
            weac_plot["nu_method"],
            strict=True,
        )
    ]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(DOUBLE_COL, 4.4),
        sharex=True,
        gridspec_kw={"width_ratios": [1.0, 1.8]},
    )

    for ax, title in zip(axes, ["(a) Roch slab inputs", "(b) WEAC slab elasticity"], strict=True):
        _setup_publication_axes(ax, x_grid=True, y_grid=False)
        ax.text(0.02, 0.98, title, ha="left", va="top", fontsize=8, fontweight="bold", transform=ax.transAxes)

    roch_widths = roch_plot["n_all_inputs"] / total_slabs * 100.0
    axes[0].barh(
        [method_label(method, short=True) for method in roch_plot["density_method"]],
        roch_widths,
        color=[DENSITY_COLORS[m] for m in roch_plot["density_method"]],
        edgecolor=COLOR_BORDER,
        linewidth=0.7,
        alpha=0.85,
    )
    for y_idx, width in enumerate(roch_widths):
        axes[0].text(width + 0.6, y_idx, f"{width:.1f}%", va="center", ha="left", fontsize=7.5)

    weac_widths = weac_plot["n_all_inputs"] / total_slabs * 100.0
    axes[1].barh(
        weac_plot["label"],
        weac_widths,
        color=[DENSITY_COLORS[m] for m in weac_plot["density_method"]],
        edgecolor=COLOR_BORDER,
        linewidth=0.7,
        alpha=0.85,
    )
    for y_idx, width in enumerate(weac_widths):
        axes[1].text(width + 0.35, y_idx, f"{width:.1f}%", va="center", ha="left", fontsize=7.0)

    axes[0].set_xlabel("Coverage of ECTP slabs (%)")
    axes[1].set_xlabel("Coverage of ECTP slabs (%)")
    axes[0].set_xlim(0, 45)
    axes[0].tick_params(axis="y", labelsize=8)
    axes[1].tick_params(axis="y", labelsize=7.5)
    axes[1].invert_yaxis()
    axes[0].invert_yaxis()

    fig.legend(
        handles=density_legend_handles(),
        loc="upper center",
        bbox_to_anchor=(0.50, 1.02),
        ncol=2,
        frameon=False,
        fontsize=7.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92), pad=0.5)
    return fig


def build_weac_attrition_figure(steps: Sequence[tuple[str, int]], total_slabs: int, pathway_label: str) -> plt.Figure:
    """Create a funnel-style WEAC attrition figure."""
    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 2.8))
    ax.axis("off")

    y_positions = np.linspace(0.80, 0.20, len(steps))
    base_color = DENSITY_COLORS["kim_jamieson_table2"]
    alphas = [0.35, 0.50, 0.68, 0.85]

    for idx, ((label, count), y_pos) in enumerate(zip(steps, y_positions, strict=True)):
        width = 0.18 + 0.60 * (count / total_slabs)
        x0 = 0.50 - width / 2
        rect = mpatches.FancyBboxPatch(
            (x0, y_pos - 0.08),
            width,
            0.12,
            boxstyle="round,pad=0.01,rounding_size=0.016",
            facecolor=base_color,
            edgecolor=COLOR_BORDER,
            linewidth=1.0,
            alpha=alphas[min(idx, len(alphas) - 1)],
            transform=ax.transAxes,
        )
        ax.add_patch(rect)
        ax.text(0.05, y_pos - 0.01, label, ha="left", va="center", fontsize=8.2, transform=ax.transAxes)
        ax.text(
            0.50,
            y_pos - 0.01,
            f"{count:,} slabs ({count / total_slabs:.1%})",
            ha="center",
            va="center",
            fontsize=8.4,
            fontweight="bold",
            transform=ax.transAxes,
        )
        if idx < len(steps) - 1:
            _add_arrow(ax, (0.50, y_pos - 0.09), (0.50, y_positions[idx + 1] + 0.05), color="#6A6A6A")

    info = mpatches.FancyBboxPatch(
        (0.70, 0.77),
        0.24,
        0.15,
        boxstyle="round,pad=0.01,rounding_size=0.016",
        facecolor="#F7F7F7",
        edgecolor="#BDBDBD",
        linewidth=1.0,
        transform=ax.transAxes,
    )
    ax.add_patch(info)
    ax.text(
        0.82,
        0.845,
        "Best-coverage path\n" + pathway_label,
        ha="center",
        va="center",
        fontsize=7.8,
        transform=ax.transAxes,
    )

    fig.tight_layout(pad=0.3)
    return fig


def build_d11_distribution_figure(
    ordered_paths: Sequence[tuple[str, int]],
    pathway_nominal: dict[str, Sequence[float]],
    total_slabs: int,
    *,
    top_n: int = 12,
) -> plt.Figure:
    """Create the D11 top-pathways boxplot figure."""
    selected = list(ordered_paths[:top_n])
    data: list[np.ndarray] = []
    labels: list[str] = []
    colors: list[str] = []

    for pathway, n_success in selected:
        values = np.asarray(pathway_nominal.get(pathway, []), dtype=float)
        values = values[np.isfinite(values) & (values > 0)]
        if values.size == 0:
            continue
        density_method = pathway.split(" -> ")[0]
        colors.append(DENSITY_COLORS.get(density_method, "#888888"))
        data.append(values)
        labels.append(
            f"{format_method_path(*pathway.split(' -> '), short=True)} ({n_success / total_slabs:.1%})"
        )

    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 5.7))
    box = ax.boxplot(
        data,
        vert=False,
        patch_artist=True,
        widths=0.65,
        showfliers=False,
        showmeans=True,
        whis=(5, 95),
        meanprops={"marker": "o", "markerfacecolor": "#222222", "markeredgecolor": "white", "markersize": 4.6},
        medianprops={"color": "#222222", "linewidth": 1.2},
        whiskerprops={"color": "#555555", "linewidth": 1.0},
        capprops={"color": "#555555", "linewidth": 1.0},
    )
    for patch, color in zip(box["boxes"], colors, strict=True):
        patch.set_facecolor(color)
        patch.set_edgecolor(COLOR_BORDER)
        patch.set_alpha(0.72)

    ax.set_xscale("log")
    ax.set_xlabel(r"$D_{11}$ (N m)")
    ax.set_yticks(np.arange(1, len(labels) + 1))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    _setup_publication_axes(ax, x_grid=True, y_grid=False)

    fig.legend(
        handles=density_legend_handles(),
        loc="upper center",
        bbox_to_anchor=(0.50, 1.02),
        ncol=2,
        frameon=False,
        fontsize=7.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92), pad=0.5)
    return fig


def prepare_roch_table(roch_cov: pd.DataFrame, total_slabs: int) -> pd.DataFrame:
    """Create the compact Roch table."""
    table = roch_cov.copy()
    table["Successful slabs"] = table["n_all_inputs"].map(lambda value: f"{int(value):,}")
    table["Coverage (%)"] = table["n_all_inputs"].map(lambda value: f"{100.0 * value / total_slabs:.1f}")
    table["Mean layer density (kg m^-3)"] = table["density_nom"].map(lambda value: f"{value:.1f}")
    table["Mean relative uncertainty (%)"] = table["density_rel_unc"].map(lambda value: f"{100.0 * value:.1f}")
    return table.rename(columns={"density_method": "Density method"})[
        [
            "Density method",
            "Successful slabs",
            "Coverage (%)",
            "Mean layer density (kg m^-3)",
            "Mean relative uncertainty (%)",
        ]
    ].assign(**{"Density method": lambda frame: frame["Density method"].map(method_label)})


def prepare_weac_table(weac_cov: pd.DataFrame, total_slabs: int, *, top_n: int = 8) -> pd.DataFrame:
    """Create the compact WEAC table."""
    table = weac_cov.head(top_n).copy()
    table["Successful slabs"] = table["n_all_inputs"].map(lambda value: f"{int(value):,}")
    table["Coverage (%)"] = table["n_all_inputs"].map(lambda value: f"{100.0 * value / total_slabs:.1f}")
    return table.rename(
        columns={
            "density_method": "Density method",
            "emod_method": "E method",
            "nu_method": "nu method",
        }
    )[
        ["Density method", "E method", "nu method", "Successful slabs", "Coverage (%)"]
    ].assign(
        **{
            "Density method": lambda frame: frame["Density method"].map(method_label),
            "E method": lambda frame: frame["E method"].map(method_label),
            "nu method": lambda frame: frame["nu method"].map(method_label),
        }
    )


def prepare_d11_representative_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    """Select the representative D11 pathways used in the paper table."""
    selected_paths = [
        "geldsetzer -> wautier -> kochle",
        "kim_jamieson_table2 -> wautier -> kochle",
        "geldsetzer -> schottner -> kochle",
        "kim_jamieson_table2 -> schottner -> kochle",
        "geldsetzer -> kochle -> srivastava",
        "data_flow -> wautier -> kochle",
    ]
    table = summary_df.set_index("Pathway").loc[selected_paths].reset_index()
    return pd.DataFrame(
        {
            "Pathway": [
                format_method_path(*pathway.split(" -> "))
                for pathway in table["Pathway"]
            ],
            "Successful slabs": table["Slabs"].astype(str),
            "Coverage (%)": table["Coverage (%)"].astype(str),
            "Mean D11 (N m)": table["Mean D11 (N m)"].astype(str),
            "Mean relative uncertainty (%)": table["Mean relative uncertainty (%)"].astype(str),
        }
    )


def notebook_latex(df: pd.DataFrame) -> str:
    """Return a compact LaTeX string for notebook display."""
    return df.to_latex(index=False, escape=False)

