"""Create a support figure for empirical density methods.

The figure compares which hand-hardness and grain-form combinations are
supported by each implemented empirical density method.

Run from the repository root:

    python examples/figures/density_method_support_matrix.py
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from snowpyt_mechparams.constants import HARDNESS_MAPPING


METHODS = [
    ("geldsetzer", "Geldsetzer and Jamieson", "#3B78A6"),
    ("kim_jamieson_table2", "Kim and Jamieson Table 2", "#D87745"),
    ("kim_jamieson_table5", "Kim and Jamieson Table 5", "#4E9F50"),
]

GRAIN_FORM_ORDER = [
    "PP",
    "PPgp",
    "MM",
    "DF",
    "RG",
    "RGmx",
    "RGxf",
    "FC",
    "FCmx",
    "FCxr",
    "DH",
    "SH",
    "MF",
    "MFcr",
    "IF",
]

HARDNESS_RANGES = {
    "geldsetzer": {
        "PP": (0.67, 4.00),    # F- to P
        "PPgp": (0.67, 4.00),  # F- to P
        "DF": (0.67, 4.33),    # F- to P+
        "RG": (1.00, 5.33),    # F to K+
        "RGmx": (0.67, 4.33),  # F- to P+
        "FC": (0.67, 4.67),    # F- to K-
        "FCmx": (1.00, 5.33),  # F to K+
        "DH": (1.00, 5.00),    # F to K
    },
    "kim_jamieson_table2": {
        "PP": (0.67, 4.00),    # F- to P
        "PPgp": (0.67, 4.00),  # F- to P
        "DF": (0.67, 4.67),    # F- to K-
        "RG": (0.67, 5.33),    # F- to K+
        "RGmx": (0.67, 4.33),  # F- to P+
        "RGxf": (0.67, 4.33),  # F- to P+
        "FC": (0.67, 5.00),    # F- to K
        "FCmx": (0.67, 5.33),  # F- to K+
        "FCxr": (0.67, 5.33),  # F- to K+
        "DH": (1.00, 5.00),    # F to K
        "MFcr": (2.00, 5.33),  # 4F to K+
    },
    "kim_jamieson_table5": {
        "FC": (1.67, 4.00),    # 4F- to P
        "FCxr": (2.33, 4.33),  # 4F+ to P+
        "PP": (0.67, 2.00),    # F- to 4F
        "PPgp": (1.00, 3.33),  # F to 1F+
        "DF": (1.00, 3.00),    # F to 1F
        "MF": (2.33, 4.33),    # 4F+ to P+
    },
}


def _supported_methods(grain_form: str, hhi: float) -> list[tuple[str, str, str]]:
    """Return density methods supporting a grain-form/HHI combination."""
    supported = []
    for method, label, color in METHODS:
        method_ranges = HARDNESS_RANGES[method]
        if grain_form not in method_ranges:
            continue
        min_hhi, max_hhi = method_ranges[grain_form]
        if min_hhi <= hhi <= max_hhi:
            supported.append((method, label, color))
    return supported


def _draw_support_cell(
    ax: plt.Axes,
    x: int,
    y: int,
    supported_methods: list[tuple[str, str, str]],
) -> None:
    """Draw one matrix cell, splitting supported cells by method color."""
    ax.add_patch(
        mpatches.Rectangle(
            (x - 0.5, y - 0.5),
            1.0,
            1.0,
            facecolor="#F1F1F1",
            edgecolor="white",
            linewidth=1.2,
        )
    )
    if not supported_methods:
        return

    segment_width = 1.0 / len(supported_methods)
    for segment, (_method, _label, color) in enumerate(supported_methods):
        ax.add_patch(
            mpatches.Rectangle(
                (x - 0.5 + segment * segment_width, y - 0.5),
                segment_width,
                1.0,
                facecolor=color,
                edgecolor="white",
                linewidth=0.6,
            )
        )


def build_density_method_support_figure() -> plt.Figure:
    """Build a grain-form by hand-hardness support figure."""
    hardness_items = list(HARDNESS_MAPPING.items())
    fig, ax = plt.subplots(figsize=(8.8, 6.7))

    for y, grain_form in enumerate(GRAIN_FORM_ORDER):
        for x, (_hardness_code, hhi) in enumerate(hardness_items):
            _draw_support_cell(ax, x, y, _supported_methods(grain_form, hhi))

    ax.set_xlim(-0.5, len(hardness_items) - 0.5)
    ax.set_ylim(len(GRAIN_FORM_ORDER) - 0.5, -0.5)
    ax.set_xticks(np.arange(len(hardness_items)))
    ax.set_xticklabels(
        [code for code, _hhi in hardness_items],
        rotation=45,
        ha="right",
        rotation_mode="anchor",
    )
    ax.set_yticks(np.arange(len(GRAIN_FORM_ORDER)))
    ax.set_yticklabels(GRAIN_FORM_ORDER)
    ax.tick_params(axis="both", length=0, labelsize=8)
    ax.set_xlabel("Hand-hardness")
    ax.set_ylabel("Grain form")
    ax.set_title(
        "Density method support by hand hardness and grain form",
        loc="left",
        fontsize=10,
        fontweight="bold",
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    handles = [
        mpatches.Patch(facecolor=color, label=label)
        for _method, label, color in METHODS
    ]
    handles.append(
        mpatches.Patch(facecolor="#F1F1F1", edgecolor="#B8B8B8", label="Not supported"),
    )
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.54, 0.07),
        fontsize=8,
    )
    fig.subplots_adjust(left=0.09, right=0.99, top=0.92, bottom=0.20)
    return fig


def main() -> None:
    """Save the support figure as PNG and PDF in this directory."""
    output_dir = Path(__file__).resolve().parent
    fig = build_density_method_support_figure()
    for extension in ("png", "pdf"):
        fig.savefig(
            output_dir / f"density_method_support_matrix.{extension}",
            dpi=300,
            bbox_inches="tight",
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
