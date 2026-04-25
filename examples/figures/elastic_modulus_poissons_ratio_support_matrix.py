"""Create a support chart for elastic modulus and Poisson's ratio methods.

The figure compares which density ranges and grain forms are supported by each
implemented empirical method. It communicates support only, not equation form,
uncertainty, or method preference.

Run from the repository root:

    python examples/figures/elastic_modulus_poissons_ratio_support_matrix.py
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
EXAMPLES_DIR = REPO_ROOT / "examples"
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

from notebook_utils import PAPER_FIGURES_DIRS


METHOD_LANES = {
    "elastic_modulus": ["bergfeld", "kochle", "wautier", "schottner"],
    "poissons_ratio": ["kochle", "srivastava"],
}

METHOD_STYLES = {
    "bergfeld": {
        "label": "Bergfeld et al. (2023)",
        "color": "#9ECAE1",
        "hatch": None,
    },
    "kochle": {
        "label": "Kochle and Schneebeli (2014)",
        "color": "#D7A6C8",
        "hatch": None,
    },
    "wautier": {
        "label": "Wautier et al. (2015)",
        "color": "#F2CF6B",
        "hatch": None,
    },
    "schottner": {
        "label": "Schottner et al. (2026)*",
        "color": "#A1D99B",
        "hatch": None,
    },
    "srivastava": {
        "label": "Srivastava et al. (2016)",
        "color": "#FDBB84",
        "hatch": None,
    },
}

GRID_COLOR = "#7F7F7F"
ROW_GRID_COLOR = "#D0D0D0"
METHOD_GRID_COLOR = "#F2F2F2"
DENSITY_X_MIN = 0.0
DENSITY_X_MAX = 600.0
DENSITY_BOUNDARIES = [103, 110, 150, 200, 363, 450, 544, 580]
ROW_SPACING = 1.65
ROW_HEIGHT = 1.45

GRAIN_FORM_ORDER = [
    "PP",
    "MM",
    "DF",
    "RG",
    "FC",
    "DH",
    "SH",
    "MF",
    "IF",
]

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


def _main_grain_form(grain_form: str) -> str:
    """Return the two-character grain class used by the implementations."""
    return grain_form[:2].upper()


def _elastic_supported_ranges(
    method: str,
    grain_form: str,
) -> list[tuple[float, float]]:
    """Return supported density ranges for an elastic-modulus method."""
    support = ELASTIC_SUPPORT[method]
    main_grain_form = _main_grain_form(grain_form)
    if main_grain_form not in support["grain_forms"]:
        return []
    return support["density_ranges"]


def _poissons_supported_ranges(
    method: str,
    grain_form: str,
) -> list[tuple[float, float]]:
    """Return supported density ranges for a Poisson's-ratio method."""
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


def _supported_ranges(
    method: str,
    grain_form: str,
    parameter: str,
) -> list[tuple[float, float]]:
    """Return supported density ranges for a method and grain form."""
    if parameter == "elastic_modulus":
        return _elastic_supported_ranges(method, grain_form)
    if parameter == "poissons_ratio":
        return _poissons_supported_ranges(method, grain_form)
    raise ValueError(f"Unknown parameter: {parameter}")


def _draw_support_bars(
    ax: plt.Axes,
    y: float,
    grain_form: str,
    parameter: str,
) -> None:
    """Draw one grain-form row as fixed horizontal method bars."""
    method_lanes = METHOD_LANES[parameter]
    segment_height = ROW_HEIGHT / len(method_lanes)
    row_bottom = y - ROW_HEIGHT / 2.0

    for segment, method in enumerate(method_lanes):
        method_style = METHOD_STYLES[method]
        y_bottom = row_bottom + segment * segment_height
        for x_start, x_end in _supported_ranges(method, grain_form, parameter):
            x_start = max(x_start, DENSITY_X_MIN)
            x_end = min(x_end, DENSITY_X_MAX)
            width = x_end - x_start
            ax.add_patch(
                mpatches.Rectangle(
                    (x_start, y_bottom),
                    width,
                    segment_height,
                    facecolor=method_style["color"],
                    edgecolor=METHOD_GRID_COLOR,
                    hatch=method_style["hatch"],
                    linewidth=0.5,
                )
            )


def _draw_support_chart(
    ax: plt.Axes,
    parameter: str,
) -> None:
    """Draw one continuous-density support chart for one property."""
    y_positions = np.arange(len(GRAIN_FORM_ORDER)) * ROW_SPACING
    for y, grain_form in zip(y_positions, GRAIN_FORM_ORDER):
        _draw_support_bars(ax, y, grain_form, parameter)

    ax.vlines(
        DENSITY_BOUNDARIES,
        -ROW_SPACING / 2.0,
        y_positions[-1] + ROW_SPACING / 2.0,
        colors=GRID_COLOR,
        linewidth=0.6,
        alpha=0.9,
        zorder=10,
    )
    ax.hlines(
        np.arange(len(GRAIN_FORM_ORDER) + 1) * ROW_SPACING - ROW_SPACING / 2.0,
        DENSITY_X_MIN,
        DENSITY_X_MAX,
        colors=ROW_GRID_COLOR,
        linewidth=0.5,
        zorder=10,
    )

    ax.set_xlim(DENSITY_X_MIN, DENSITY_X_MAX)
    ax.set_ylim(y_positions[-1] + ROW_SPACING / 2.0, -ROW_SPACING / 2.0)
    ax.set_xticks(np.arange(DENSITY_X_MIN, DENSITY_X_MAX + 1, 100))
    ax.set_xticks(DENSITY_BOUNDARIES, minor=True)
    ax.tick_params(axis="both", length=0, labelsize=7.5)
    ax.tick_params(axis="x", which="minor", length=2, color=GRID_COLOR)

    for spine in ax.spines.values():
        spine.set_visible(False)


def build_elastic_modulus_poissons_ratio_support_figure() -> plt.Figure:
    """Build a grain-form by density support chart for both properties."""
    fig, axes = plt.subplots(
        ncols=2,
        sharey=True,
        figsize=(10.2, 7.13),
        gridspec_kw={"wspace": 0.08},
    )

    _draw_support_chart(axes[0], "elastic_modulus")
    _draw_support_chart(axes[1], "poissons_ratio")

    axes[0].set_title(r"Elastic modulus, $E$", fontsize=8.5, pad=6)
    axes[1].set_title(r"Poisson's ratio, $\nu$", fontsize=8.5, pad=6)

    axes[0].set_yticks(np.arange(len(GRAIN_FORM_ORDER)) * ROW_SPACING)
    axes[0].set_yticklabels(GRAIN_FORM_ORDER)
    axes[0].set_ylabel("Grain form")
    axes[0].set_xlabel(r"Density, $\rho$ (kg m$^{-3}$)")
    axes[1].set_xlabel(r"Density, $\rho$ (kg m$^{-3}$)")

    fig.suptitle(
        r"Elastic modulus ($E$) and Poisson's ratio ($\nu$) method support by density and grain form",
        x=0.08,
        ha="left",
        fontsize=10,
        fontweight="bold",
    )

    handles = [
        mpatches.Patch(
            facecolor=method_style["color"],
            edgecolor=GRID_COLOR,
            hatch=method_style["hatch"],
            label=method_style["label"],
        )
        for method_style in METHOD_STYLES.values()
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.55, 0.035),
        fontsize=7.5,
    )
    fig.subplots_adjust(left=0.10, right=0.99, top=0.88, bottom=0.24)
    return fig


def main() -> None:
    """Save the support figure as PNG and PDF in both paper figure directories."""
    fig = build_elastic_modulus_poissons_ratio_support_figure()
    for output_dir in PAPER_FIGURES_DIRS:
        output_dir.mkdir(parents=True, exist_ok=True)
        for extension in ("png", "pdf"):
            fig.savefig(
                output_dir / f"elastic_modulus_poissons_ratio_density_ranges.{extension}",
                dpi=300,
                bbox_inches="tight",
            )
    plt.close(fig)


if __name__ == "__main__":
    main()
