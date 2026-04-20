"""Create a binary support figure for empirical density methods.

The figure compares which hand-hardness classes and grain forms are supported
by each implemented empirical density method. It intentionally encodes only
support versus non-support.

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
from matplotlib.colors import ListedColormap

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from snowpyt_mechparams.constants import GRAIN_FORM_METHODS, HARDNESS_MAPPING


METHODS = [
    ("geldsetzer", "Geldsetzer and\nJamieson"),
    ("kim_jamieson_table2", "Kim and Jamieson\nTable 2"),
    ("kim_jamieson_table5", "Kim and Jamieson\nTable 5"),
]

GRAIN_FORM_ORDER = [
    "PP",
    "PPgp",
    "DF",
    "RG",
    "RGmx",
    "RGxf",
    "FC",
    "FCmx",
    "FCxr",
    "DH",
    "MF",
    "MFcr",
]


def _support_matrix(labels: list[str], supported_by_method: dict[str, set[str]]) -> np.ndarray:
    """Return a binary method-by-label support matrix."""
    return np.array(
        [
            [label in supported_by_method[method] for label in labels]
            for method, _method_label in METHODS
        ],
        dtype=int,
    )


def _density_method_grain_forms() -> dict[str, set[str]]:
    """Collect supported basic and sub-grain forms for each density method."""
    return {
        method: set(codes["basic_grain_class"]) | set(codes["sub_grain_class"])
        for method, codes in GRAIN_FORM_METHODS.items()
    }


def _draw_matrix(
    ax: plt.Axes,
    matrix: np.ndarray,
    column_labels: list[str],
    panel_label: str,
    *,
    show_y_labels: bool,
) -> None:
    """Draw a compact binary support matrix."""
    cmap = ListedColormap(["#F1F1F1", "#3F7F8F"])
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(np.arange(len(column_labels)))
    ax.set_xticklabels(column_labels, rotation=0, ha="center")
    ax.set_yticks(np.arange(len(METHODS)))
    ax.set_yticklabels([label for _method, label in METHODS] if show_y_labels else [])
    ax.tick_params(axis="both", length=0, labelsize=8)
    ax.set_title(panel_label, loc="left", fontsize=10, fontweight="bold", pad=8)

    ax.set_xticks(np.arange(-0.5, len(column_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(METHODS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.4)
    ax.tick_params(which="minor", bottom=False, left=False)

    for spine in ax.spines.values():
        spine.set_visible(False)


def build_density_method_support_figure() -> plt.Figure:
    """Build the two-panel density-method support figure."""
    hardness_labels = list(HARDNESS_MAPPING)
    hardness_support = {
        method: set(hardness_labels)
        for method, _method_label in METHODS
    }
    grain_form_support = _density_method_grain_forms()

    hardness_matrix = _support_matrix(hardness_labels, hardness_support)
    grain_form_matrix = _support_matrix(GRAIN_FORM_ORDER, grain_form_support)

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(7.2, 3.7),
        gridspec_kw={"height_ratios": [1.0, 1.0], "hspace": 0.58},
    )

    _draw_matrix(
        axes[0],
        hardness_matrix,
        hardness_labels,
        "a) Supported hand-hardness classes",
        show_y_labels=True,
    )
    _draw_matrix(
        axes[1],
        grain_form_matrix,
        GRAIN_FORM_ORDER,
        "b) Supported grain forms",
        show_y_labels=True,
    )

    handles = [
        mpatches.Patch(facecolor="#3F7F8F", label="Supported"),
        mpatches.Patch(facecolor="#F1F1F1", edgecolor="#B8B8B8", label="Not supported"),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.54, -0.02),
        fontsize=8,
    )
    fig.subplots_adjust(left=0.20, right=0.98, top=0.92, bottom=0.18)
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
