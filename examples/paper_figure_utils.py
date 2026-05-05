"""Shared figure and table helpers for the mech params paper notebooks."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from notebook_utils import (
    DENSITY_COLORS,
    DOUBLE_COL,
    DPI,
    EXTERNAL_PAPER_FIGURES_DIR,
    PAPER_FIGURES_DIR,
    PAPER_FIGURES_DIRS,
    REPO_PAPER_FIGURES_DIR,
)

COLOR_BORDER = "#404040"
GRID_COLOR = "#D8D8D8"

RHO_ICE_VALUE = 917.0
E_ICE_VALUE = 10000.0

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

FONTTOOLS_LOGGERS = (
    "fontTools.ttLib.tables._h_e_a_d",
    "fontTools.ttLib.tables._p_o_s_t",
)


@contextmanager
def _quiet_fonttools_pdf_metadata_warnings() -> Iterator[None]:
    """Suppress noisy font metadata warnings emitted during Matplotlib PDF export."""
    loggers = [logging.getLogger(name) for name in FONTTOOLS_LOGGERS]
    previous_levels = [logger.level for logger in loggers]
    try:
        for logger in loggers:
            logger.setLevel(logging.ERROR)
        yield
    finally:
        for logger, level in zip(loggers, previous_levels):
            logger.setLevel(level)


def paper_figures_dir() -> Path:
    """Return the repository-local paper figures directory."""
    PAPER_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return PAPER_FIGURES_DIR


def save_paper_figure(
    fig: plt.Figure, stem: str, close: bool = False
) -> dict[str, Path]:
    """Save a paper figure as PDF and PNG in repo and manuscript directories."""
    saved_paths: dict[str, Path] = {}
    for output_dir in PAPER_FIGURES_DIRS:
        output_dir.mkdir(parents=True, exist_ok=True)
        prefix = "repo" if output_dir == REPO_PAPER_FIGURES_DIR else "external"
        pdf_path = output_dir / f"{stem}.pdf"
        png_path = output_dir / f"{stem}.png"
        with _quiet_fonttools_pdf_metadata_warnings():
            fig.savefig(pdf_path, dpi=DPI, bbox_inches="tight")
        fig.savefig(png_path, dpi=DPI, bbox_inches="tight")
        saved_paths[f"{prefix}_pdf"] = pdf_path
        saved_paths[f"{prefix}_png"] = png_path

    saved_paths["pdf"] = saved_paths["repo_pdf"]
    saved_paths["png"] = saved_paths["repo_png"]
    saved_paths["external_dir"] = EXTERNAL_PAPER_FIGURES_DIR
    if close:
        plt.close(fig)
    return saved_paths


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


def _setup_publication_axes(
    ax: plt.Axes, *, x_grid: bool = True, y_grid: bool = False
) -> None:
    """Apply a light publication grid and spine cleanup."""
    if x_grid:
        ax.grid(True, axis="x", color=GRID_COLOR, linewidth=0.6)
    if y_grid:
        ax.grid(True, axis="y", color=GRID_COLOR, linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


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

SUPPORT_GRAIN_FORM_ORDER = [
    "PP",
    "PPgp",
    "MM",
    "DF",
    "RG",
    "RGxf",
    "FC",
    "FCxr",
    "DH",
    "SH",
    "MF",
    "MFcr",
    "IF",
]

DENSITY_SUPPORT_METHODS = [
    "geldsetzer",
    "kim_jamieson_table2",
    "kim_jamieson_table5",
]

ELASTIC_SUPPORT_METHODS = ["bergfeld", "kochle", "wautier", "schottner"]
POISSONS_SUPPORT_METHODS = ["kochle", "srivastava"]

SUPPORT_METHOD_STYLES = {
    "geldsetzer": {"color": "#0072B2", "label": "Geldsetzer"},
    "kim_jamieson_table2": {"color": "#009E73", "label": "Kim T2"},
    "kim_jamieson_table5": {"color": "#E69F00", "label": "Kim T5"},
    "bergfeld": {"color": "#56B4E9", "label": "Bergfeld"},
    "kochle": {"color": "#CC79A7", "label": "Kochle"},
    "wautier": {"color": "#F0E442", "label": "Wautier"},
    "schottner": {"color": "#D55E00", "label": "Schottner"},
    "srivastava": {"color": "#4D4D4D", "label": "Srivastava"},
}

DENSITY_SUPPORT_RANGES = {
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
    "kim_jamieson_table5": {
        "FC": (1.67, 4.00),
        "FCxr": (2.33, 4.33),
        "PP": (0.67, 2.00),
        "PPgp": (1.00, 3.33),
        "DF": (1.00, 3.00),
        "MF": (2.33, 4.33),
    },
}

DENSITY_BOUNDARIES = [103, 110, 150, 200, 363, 450, 544, 580]
DENSITY_X_MIN = 0.0
DENSITY_X_MAX = 600.0

ELASTIC_SUPPORT = {
    "bergfeld": {
        "grain_forms": {"PP", "RG", "DF"},
        "density_ranges": [(110.0, 363.0)],
    },
    "kochle": {
        "grain_forms": {"RG", "FC", "DH", "MF"},
        "density_ranges": [(150.0, 450.0)],
    },
    "wautier": {
        "grain_forms": {"DF", "RG", "FC", "DH", "MF"},
        "density_ranges": [(103.0, 544.0)],
    },
    "schottner": {
        "grain_forms": {"DF", "RG", "FC", "DH", "SH"},
        "density_ranges": [(DENSITY_X_MIN, DENSITY_X_MAX)],
    },
}


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
        (
            "Bergfeld",
            "#0072B2",
            "-",
            _bergfeld_curve(rho[(rho >= 110) & (rho <= 363)]),
            rho[(rho >= 110) & (rho <= 363)],
            "PP, DF, RG",
        ),
        (
            "Kochle low",
            "#A12A6A",
            "-",
            _kochle_low_curve(rho[(rho >= 150) & (rho < 250)]),
            rho[(rho >= 150) & (rho < 250)],
            "RG, FC, DH, MF",
        ),
        (
            "Kochle high",
            "#A12A6A",
            "--",
            _kochle_high_curve(rho[(rho >= 250) & (rho <= 450)]),
            rho[(rho >= 250) & (rho <= 450)],
            "RG, FC, DH, MF",
        ),
        (
            "Wautier",
            "#E69F00",
            "-",
            _wautier_curve(rho[(rho >= 103) & (rho <= 544)]),
            rho[(rho >= 103) & (rho <= 544)],
            "DF, RG, FC, DH, MF",
        ),
        (
            "Schottner DF/RG",
            "#009E73",
            "-",
            _schottner_curve(rho, 0.40, 4.6),
            rho,
            "DF, RG",
        ),
        (
            "Schottner FC/DH",
            "#009E73",
            "--",
            _schottner_curve(rho, 1.8, 5.1),
            rho,
            "FC, DH",
        ),
        ("Schottner SH", "#009E73", ":", _schottner_curve(rho, 0.011, 1.7), rho, "SH"),
    ]

    for ax in axes:
        for label, color, linestyle, y_values, x_values, grain_forms in curve_specs:
            ax.plot(
                x_values,
                y_values,
                color=color,
                linestyle=linestyle,
                linewidth=1.8,
                label=f"{label} ({grain_forms})",
            )
        ax.set_xlim(100, 550)
        ax.set_xlabel(r"Density, $\rho$ (kg m$^{-3}$)")
        _setup_publication_axes(ax, x_grid=True, y_grid=False)

    axes[0].set_ylabel(r"Elastic modulus, $E$ (MPa)")
    axes[0].set_ylim(0, 950)
    axes[0].text(
        0.02,
        0.96,
        "(a) Linear scale",
        transform=axes[0].transAxes,
        va="top",
        fontsize=8,
        fontweight="bold",
    )

    axes[1].set_yscale("log")
    axes[1].set_ylim(0.3, 5000)
    axes[1].text(
        0.02,
        0.96,
        "(b) Log scale",
        transform=axes[1].transAxes,
        va="top",
        fontsize=8,
        fontweight="bold",
    )

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.50, 1.02),
        ncol=2,
        frameon=False,
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90), pad=0.4)
    return fig


def _main_grain_form(grain_form: str) -> str:
    """Return the two-character grain class used by the implementations."""
    return grain_form[:2].upper()


def _density_method_supports(method: str, grain_form: str, hhi: float) -> bool:
    method_ranges = DENSITY_SUPPORT_RANGES[method]
    if grain_form not in method_ranges:
        return False
    low, high = method_ranges[grain_form]
    return low <= hhi <= high


def _elastic_supported_ranges(
    method: str, grain_form: str
) -> list[tuple[float, float]]:
    support = ELASTIC_SUPPORT[method]
    if _main_grain_form(grain_form) not in support["grain_forms"]:
        return []
    return support["density_ranges"]


def _poissons_supported_ranges(
    method: str, grain_form: str
) -> list[tuple[float, float]]:
    main_grain_form = _main_grain_form(grain_form)

    if method == "kochle":
        if main_grain_form in {"RG", "FC", "DH"}:
            return [(DENSITY_X_MIN, DENSITY_X_MAX)]
        return []

    if method == "srivastava":
        if main_grain_form == "RG":
            return [(200.0, 580.0)]
        if main_grain_form in {"PP", "DF", "FC", "DH"}:
            return [(200.0, DENSITY_X_MAX)]
        return []

    raise ValueError(f"Unknown Poisson's-ratio method: {method}")


def _parameter_supported_ranges(
    method: str,
    grain_form: str,
    parameter: str,
) -> list[tuple[float, float]]:
    if parameter == "elastic_modulus":
        return _elastic_supported_ranges(method, grain_form)
    if parameter == "poissons_ratio":
        return _poissons_supported_ranges(method, grain_form)
    raise ValueError(f"Unknown parameter: {parameter}")


def _draw_lane_cell(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    supported_methods: set[str],
    method_lanes: Sequence[str],
) -> None:
    lane_height = 0.88 / len(method_lanes)
    row_bottom = y - 0.44
    for lane_idx, method in enumerate(method_lanes):
        style = SUPPORT_METHOD_STYLES[method]
        facecolor = style["color"] if method in supported_methods else "white"
        ax.add_patch(
            mpatches.Rectangle(
                (x, row_bottom + lane_idx * lane_height),
                width,
                lane_height,
                facecolor=facecolor,
                edgecolor="#D8D8D8",
                linewidth=0.35,
            )
        )


def _draw_density_support_panel(ax: plt.Axes) -> None:
    hardness_items = list(HARDNESS_MAPPING.items())
    for y, grain_form in enumerate(SUPPORT_GRAIN_FORM_ORDER):
        for x_idx, (_hardness_code, hhi) in enumerate(hardness_items):
            supported_methods = {
                method
                for method in DENSITY_SUPPORT_METHODS
                if _density_method_supports(method, grain_form, hhi)
            }
            _draw_lane_cell(
                ax,
                x_idx - 0.5,
                y,
                1.0,
                supported_methods,
                DENSITY_SUPPORT_METHODS,
            )

    ax.vlines(
        np.arange(-0.5, len(hardness_items) + 0.5, 1.0),
        -0.5,
        len(SUPPORT_GRAIN_FORM_ORDER) - 0.5,
        colors="#8F8F8F",
        linewidth=0.45,
        zorder=10,
    )
    ax.hlines(
        np.arange(-0.5, len(SUPPORT_GRAIN_FORM_ORDER) + 0.5, 1.0),
        -0.5,
        len(hardness_items) - 0.5,
        colors="#BDBDBD",
        linewidth=0.45,
        zorder=10,
    )
    ax.set_xlim(-0.5, len(hardness_items) - 0.5)
    ax.set_ylim(len(SUPPORT_GRAIN_FORM_ORDER) - 0.5, -0.5)
    ax.set_xticks(np.arange(len(hardness_items)))
    ax.set_xticklabels(
        [code for code, _hhi in hardness_items],
        rotation=45,
        ha="right",
        rotation_mode="anchor",
    )
    ax.set_xlabel("Hand hardness")


def _draw_density_range_support_panel(ax: plt.Axes, parameter: str) -> None:
    method_lanes = (
        ELASTIC_SUPPORT_METHODS
        if parameter == "elastic_modulus"
        else POISSONS_SUPPORT_METHODS
    )
    for y, grain_form in enumerate(SUPPORT_GRAIN_FORM_ORDER):
        lane_height = 0.88 / len(method_lanes)
        row_bottom = y - 0.44
        for lane_idx, method in enumerate(method_lanes):
            y_bottom = row_bottom + lane_idx * lane_height
            for x_start, x_end in _parameter_supported_ranges(
                method,
                grain_form,
                parameter,
            ):
                ax.add_patch(
                    mpatches.Rectangle(
                        (max(x_start, DENSITY_X_MIN), y_bottom),
                        min(x_end, DENSITY_X_MAX) - max(x_start, DENSITY_X_MIN),
                        lane_height,
                        facecolor=SUPPORT_METHOD_STYLES[method]["color"],
                        edgecolor="#D8D8D8",
                        linewidth=0.35,
                    )
                )

    ax.vlines(
        DENSITY_BOUNDARIES,
        -0.5,
        len(SUPPORT_GRAIN_FORM_ORDER) - 0.5,
        colors="#8F8F8F",
        linewidth=0.45,
        zorder=10,
    )
    ax.hlines(
        np.arange(-0.5, len(SUPPORT_GRAIN_FORM_ORDER) + 0.5, 1.0),
        DENSITY_X_MIN,
        DENSITY_X_MAX,
        colors="#BDBDBD",
        linewidth=0.45,
        zorder=10,
    )
    ax.set_xlim(DENSITY_X_MIN, DENSITY_X_MAX)
    ax.set_ylim(len(SUPPORT_GRAIN_FORM_ORDER) - 0.5, -0.5)
    ax.set_xticks(np.arange(DENSITY_X_MIN, DENSITY_X_MAX + 1, 100))
    ax.set_xticks(DENSITY_BOUNDARIES, minor=True)
    ax.tick_params(axis="x", which="minor", length=2, color="#6F6F6F")
    ax.set_xlabel(r"Density, $\rho$ (kg m$^{-3}$)")


def _style_support_panel(ax: plt.Axes, panel_label: str, title: str) -> None:
    ax.set_yticks(np.arange(len(SUPPORT_GRAIN_FORM_ORDER)))
    ax.set_yticklabels(SUPPORT_GRAIN_FORM_ORDER)
    ax.tick_params(axis="both", length=0, labelsize=6.8)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.set_ylabel("Grain form")
    ax.text(
        0.0,
        1.035,
        f"{panel_label} {title}",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.1,
        fontweight="bold",
    )
    for spine in ax.spines.values():
        spine.set_visible(False)


def build_method_support_matrices_figure() -> plt.Figure:
    """Create stacked support matrices for density, elastic modulus, and nu."""
    fig, axes = plt.subplots(
        nrows=3,
        figsize=(DOUBLE_COL, 8.35),
        gridspec_kw={"height_ratios": [1.08, 1.0, 1.0], "hspace": 0.42},
    )

    _draw_density_support_panel(axes[0])
    _draw_density_range_support_panel(axes[1], "elastic_modulus")
    _draw_density_range_support_panel(axes[2], "poissons_ratio")

    _style_support_panel(
        axes[0],
        "(a)",
        "Density methods: support depends on grain form and hand hardness",
    )
    _style_support_panel(
        axes[1],
        "(b)",
        "Elastic modulus methods: support narrows by density and grain form",
    )
    _style_support_panel(
        axes[2],
        "(c)",
        "Poisson's ratio methods: support is most restrictive",
    )

    handles = [
        mpatches.Patch(
            facecolor=SUPPORT_METHOD_STYLES[method]["color"],
            edgecolor=COLOR_BORDER,
            label=SUPPORT_METHOD_STYLES[method]["label"],
        )
        for method in (
            DENSITY_SUPPORT_METHODS + ELASTIC_SUPPORT_METHODS + ["srivastava"]
        )
    ]
    handles.append(
        mpatches.Patch(
            facecolor="white",
            edgecolor="#8F8F8F",
            label="Unsupported",
        )
    )
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=5,
        frameon=False,
        bbox_to_anchor=(0.55, 0.006),
        fontsize=6.8,
        columnspacing=0.95,
        handlelength=1.4,
    )
    fig.subplots_adjust(left=0.075, right=0.99, top=0.965, bottom=0.095)
    return fig


def build_slab_weight_coverage_comparison_figure(
    shear_cov: pd.DataFrame,
    elasticity_cov: pd.DataFrame,
    total_slabs: int,
    *,
    top_n: int = 10,
) -> plt.Figure:
    """Create the slab-weight shear vs elastic-input coverage comparison figure."""
    shear_plot = shear_cov.sort_values("n_all_inputs", ascending=False).copy()
    elasticity_plot = (
        elasticity_cov.head(top_n).copy().sort_values("n_all_inputs", ascending=False)
    )
    shear_plot["label"] = [
        f"{method_label(method, short=True)} ({int(count):,})"
        for method, count in zip(
            shear_plot["density_method"], shear_plot["n_all_inputs"], strict=True
        )
    ]
    elasticity_plot["label"] = [
        (
            rf"$\rho$: {method_label(dm, short=True)} | "
            rf"$E$: {method_label(em, short=True)} | "
            rf"$\nu$: {method_label(nu, short=True)} ({int(count):,})"
        )
        for dm, em, nu, count in zip(
            elasticity_plot["density_method"],
            elasticity_plot["emod_method"],
            elasticity_plot["nu_method"],
            elasticity_plot["n_all_inputs"],
            strict=True,
        )
    ]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(DOUBLE_COL, 5.25),
        sharey=True,
        gridspec_kw={"width_ratios": [4, 10]},
    )

    def _method_color(method: str) -> str:
        if method in SUPPORT_METHOD_STYLES:
            return SUPPORT_METHOD_STYLES[method]["color"]
        if method == "data_flow":
            return "#8F8F8F"
        return DENSITY_COLORS.get(method, "#8F8F8F")

    def _draw_bar_chart(
        ax: plt.Axes,
        labels: Sequence[str],
        values: Sequence[float],
        colors: Sequence[str],
        *,
        value_offset: float,
    ) -> None:
        x_pos = np.arange(len(labels))
        ax.bar(
            x_pos,
            values,
            width=0.58,
            color=colors,
            edgecolor=COLOR_BORDER,
            linewidth=0.7,
            alpha=0.85,
        )
        for x_idx, value in zip(x_pos, values, strict=True):
            ax.text(
                x_idx,
                value + value_offset,
                f"{value:.1f}%",
                va="bottom",
                ha="center",
                fontsize=6.8,
                clip_on=False,
            )
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha="right", rotation_mode="anchor")

    for ax, title in zip(
        axes,
        [
            r"Shear Weight ($W_S$) Pathways",
            r"Shear Weight ($W_S$) with Elasticity Parameters ($E$, $\nu$) Pathways",
        ],
        strict=True,
    ):
        _setup_publication_axes(ax, x_grid=False, y_grid=True)
        ax.set_title(title, loc="left", fontsize=8, fontweight="bold", pad=3)
        ax.set_ylim(0, 42)
        ax.set_yticks([0, 10, 20, 30, 40])
        ax.set_ylabel("Coverage of ECTP slabs (%)", fontsize=7.5)

    shear_widths = shear_plot["n_all_inputs"] / total_slabs * 100.0
    _draw_bar_chart(
        axes[0],
        shear_plot["label"],
        shear_widths,
        [_method_color(m) for m in shear_plot["density_method"]],
        value_offset=0.7,
    )

    elasticity_widths = elasticity_plot["n_all_inputs"] / total_slabs * 100.0
    _draw_bar_chart(
        axes[1],
        elasticity_plot["label"],
        elasticity_widths,
        [_method_color(m) for m in elasticity_plot["density_method"]],
        value_offset=0.35,
    )

    axes[0].set_xlabel("Pathway (successful slabs)", fontsize=7.5)
    axes[1].set_xlabel("Pathway (successful slabs)", fontsize=7.5)
    for ax in axes:
        ax.tick_params(axis="x", labelsize=6.1)
        ax.tick_params(axis="y", labelsize=7.0, labelleft=True)

    legend_handles = [
        mpatches.Patch(
            facecolor=_method_color(method),
            edgecolor=COLOR_BORDER,
            label=method_label(method),
            alpha=0.85,
        )
        for method in DENSITY_METHOD_ORDER
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.50, 0.055),
        ncol=2,
        frameon=False,
        fontsize=7.0,
        title="Density Method",
        title_fontsize=7.2,
        columnspacing=1.2,
        handlelength=1.5,
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.92, bottom=0.48, wspace=0.24)
    return fig


def build_coverage_comparison_figure(
    roch_cov: pd.DataFrame,
    weac_cov: pd.DataFrame,
    total_slabs: int,
    *,
    top_n: int = 12,
) -> plt.Figure:
    """Create the coverage comparison figure.

    Kept for backwards compatibility with earlier Roch/WEAC notebook names.
    """
    return build_slab_weight_coverage_comparison_figure(
        roch_cov,
        weac_cov,
        total_slabs,
        top_n=top_n,
    )


def build_slab_weight_shear_with_elasticity_attrition_figure(
    steps: Sequence[tuple[str, int]],
    total_slabs: int,
    pathway_label: str,
    method_steps: Sequence[str] | None = None,
) -> plt.Figure:
    """Create a funnel-style slab-weight-shear-with-elasticity attrition figure."""
    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 3.25))
    ax.axis("off")

    y_positions = np.linspace(0.78, 0.16, len(steps))
    base_color = DENSITY_COLORS["kim_jamieson_table2"]
    alphas = [0.35, 0.50, 0.68, 0.85]
    bar_center = 0.43
    max_bar_width = 0.56
    min_bar_width = 0.12
    if method_steps is not None and len(method_steps) != len(steps):
        raise ValueError("method_steps must have one label per attrition step.")

    ax.text(
        0.05,
        0.92,
        "Requirement",
        ha="left",
        va="center",
        fontsize=7.5,
        transform=ax.transAxes,
    )
    ax.text(
        0.76,
        0.92,
        "Method/input applied",
        ha="left",
        va="center",
        fontsize=7.5,
        transform=ax.transAxes,
    )

    for idx, ((label, count), y_pos) in enumerate(zip(steps, y_positions, strict=True)):
        width = min_bar_width + (max_bar_width - min_bar_width) * (count / total_slabs)
        x0 = bar_center - width / 2
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
        ax.text(
            0.05,
            y_pos - 0.01,
            label,
            ha="left",
            va="center",
            fontsize=8.2,
            transform=ax.transAxes,
        )
        ax.text(
            bar_center,
            y_pos - 0.01,
            f"{count:,} slabs ({count / total_slabs:.1%})",
            ha="center",
            va="center",
            fontsize=8.4,
            fontweight="bold",
            transform=ax.transAxes,
        )
        if method_steps is not None:
            ax.text(
                0.76,
                y_pos - 0.01,
                method_steps[idx],
                ha="left",
                va="center",
                fontsize=7.8,
                color="#333333",
                transform=ax.transAxes,
            )
        if idx < len(steps) - 1:
            _add_arrow(
                ax,
                (bar_center, y_pos - 0.09),
                (bar_center, y_positions[idx + 1] + 0.05),
                color="#6A6A6A",
            )

    fig.tight_layout(pad=0.3)
    return fig


def build_weac_attrition_figure(
    steps: Sequence[tuple[str, int]], total_slabs: int, pathway_label: str
) -> plt.Figure:
    """Create a funnel-style attrition figure.

    Kept for backwards compatibility with earlier WEAC notebook names.
    """
    return build_slab_weight_shear_with_elasticity_attrition_figure(
        steps,
        total_slabs,
        pathway_label,
    )


def build_slab_weight_attrition_figure(
    steps: Sequence[tuple[str, int]],
    total_slabs: int,
    pathway_label: str,
) -> plt.Figure:
    """Create a funnel-style slab-weight-shear-with-elasticity attrition figure.

    Kept as a short compatibility alias for the earlier slab-weight notebook name.
    """
    return build_slab_weight_shear_with_elasticity_attrition_figure(
        steps,
        total_slabs,
        pathway_label,
    )


def build_d11_paired_pathway_effects_figure(
    paired_effects: pd.DataFrame,
    selected_paths: Sequence[str],
    *,
    top_n: int = 8,
) -> plt.Figure:
    """Create a paired pathway-effect figure using within-slab D11 ratios."""
    ratio_data: list[np.ndarray] = []
    labels: list[str] = []
    colors: list[str] = []

    for pathway in list(selected_paths)[:top_n]:
        pathway_rows = paired_effects[paired_effects["pathway"] == pathway]
        ratios = np.asarray(pathway_rows["pathway_ratio"], dtype=float)
        ratios = ratios[np.isfinite(ratios) & (ratios > 0)]
        if ratios.size == 0:
            continue

        density_method = pathway.split(" -> ")[0]
        ratio_data.append(ratios)
        labels.append(format_method_path(*pathway.split(" -> "), short=True))
        colors.append(DENSITY_COLORS.get(density_method, "#888888"))

    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 4.2))
    box = ax.boxplot(
        ratio_data,
        vert=False,
        patch_artist=True,
        widths=0.62,
        showfliers=False,
        showmeans=True,
        whis=(5, 95),
        meanprops={
            "marker": "o",
            "markerfacecolor": "#222222",
            "markeredgecolor": "white",
            "markersize": 3.8,
        },
        medianprops={"color": "#222222", "linewidth": 1.1},
        whiskerprops={"color": "#555555", "linewidth": 0.9},
        capprops={"color": "#555555", "linewidth": 0.9},
    )
    for patch, color in zip(box["boxes"], colors, strict=True):
        patch.set_facecolor(color)
        patch.set_edgecolor(COLOR_BORDER)
        patch.set_alpha(0.72)

    ax.axvline(1.0, color=COLOR_BORDER, linewidth=1.0, linestyle="--")
    ax.set_xscale("log")
    ax.set_xlabel(r"$D_{11}$ ratio to within-slab median")
    y_positions = np.arange(1, len(labels) + 1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    _setup_publication_axes(ax, x_grid=True, y_grid=False)
    fig.tight_layout(pad=0.5)
    return fig


def build_d11_spread_attribute_correlations_figure(
    correlations: pd.DataFrame,
    *,
    top_n: int = 10,
    xlabel: str = r"Spearman $\rho$ with paired pathway spread",
) -> plt.Figure:
    """Create a bar chart of Spearman correlations with D11 spread."""
    table = correlations.head(top_n).iloc[::-1].copy()
    colors = np.where(table["Spearman rho"] >= 0, "#0072B2", "#D55E00")

    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 3.9))
    ax.barh(table["Attribute"], table["Spearman rho"], color=colors, alpha=0.82)
    ax.axvline(0, color=COLOR_BORDER, linewidth=0.8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=8)
    _setup_publication_axes(ax, x_grid=True, y_grid=False)
    fig.tight_layout(pad=0.5)
    return fig


def prepare_slab_weight_shear_table(
    shear_cov: pd.DataFrame, total_slabs: int
) -> pd.DataFrame:
    """Create the compact slab-weight-shear coverage table."""
    table = shear_cov.copy()
    table["Successful slabs"] = table["n_all_inputs"].map(
        lambda value: f"{int(value):,}"
    )
    table["Coverage (%)"] = table["n_all_inputs"].map(
        lambda value: f"{100.0 * value / total_slabs:.1f}"
    )
    return table.rename(columns={"density_method": "Density method"})[
        [
            "Density method",
            "Successful slabs",
            "Coverage (%)",
        ]
    ].assign(
        **{"Density method": lambda frame: frame["Density method"].map(method_label)}
    )


def prepare_roch_table(roch_cov: pd.DataFrame, total_slabs: int) -> pd.DataFrame:
    """Create the compact density-only coverage table.

    Kept for backwards compatibility with earlier Roch notebook names.
    """
    return prepare_slab_weight_shear_table(roch_cov, total_slabs)


def prepare_slab_weight_shear_with_elasticity_table(
    elasticity_cov: pd.DataFrame,
    total_slabs: int,
    *,
    top_n: int = 8,
) -> pd.DataFrame:
    """Create the compact slab-weight-shear-with-elasticity coverage table."""
    table = elasticity_cov.head(top_n).copy()
    table["Successful slabs"] = table["n_all_inputs"].map(
        lambda value: f"{int(value):,}"
    )
    table["Coverage (%)"] = table["n_all_inputs"].map(
        lambda value: f"{100.0 * value / total_slabs:.1f}"
    )
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


def prepare_weac_table(
    weac_cov: pd.DataFrame, total_slabs: int, *, top_n: int = 8
) -> pd.DataFrame:
    """Create the compact elastic-input coverage table.

    Kept for backwards compatibility with earlier WEAC notebook names.
    """
    return prepare_slab_weight_shear_with_elasticity_table(
        weac_cov, total_slabs, top_n=top_n
    )


def prepare_slab_weight_shear_elasticity_table(
    elasticity_cov: pd.DataFrame,
    total_slabs: int,
    *,
    top_n: int = 8,
) -> pd.DataFrame:
    """Create the compact slab-weight-shear-with-elasticity coverage table.

    Kept as a short compatibility alias for the earlier slab-weight notebook name.
    """
    return prepare_slab_weight_shear_with_elasticity_table(
        elasticity_cov,
        total_slabs,
        top_n=top_n,
    )


def notebook_latex(df: pd.DataFrame) -> str:
    """Return a compact LaTeX string for notebook display."""
    return df.to_latex(index=False, escape=False)
