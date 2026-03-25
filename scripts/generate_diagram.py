#!/usr/bin/env python3
"""
Generate parameter graph diagrams for SnowPyt-MechParams.

Run after installing the package (pip install -e .):

    # All diagrams, both formats, into docs/diagrams/
    python scripts/generate_diagram.py --type all --format both --output docs/diagrams/

    # Single mermaid overview
    python scripts/generate_diagram.py --type overview --format mermaid --output docs/diagrams/overview.md

    # Matplotlib layer-params figure
    python scripts/generate_diagram.py --type layer --format matplotlib --output docs/diagrams/layer_params.png

Available --type values:
    overview    High-level five-group overview (no method names)
    layer       Layer parameter pathways (density, E, ν, G) with methods
    slab        Slab stiffness assembly (A11, B11, D11, A55) with methods
    stability   Weak-layer parameters and stability criteria with methods
    all         Generate all four diagrams (default)

Available --format values:
    mermaid     Mermaid markdown file(s) only
    matplotlib  PNG figure(s) only (300 DPI, publication quality)
    both        Both mermaid and matplotlib (default)

When --type is 'all', --output must be a directory.
When --type is a single diagram, --output may be a file path or directory.
"""

import argparse
import os
import sys


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _mermaid_path(output: str, name: str) -> str:
    """Return output path for a mermaid file."""
    if output.endswith(".md"):
        return output
    _ensure_dir(output)
    return os.path.join(output, f"{name}.md")


def _png_path(output: str, name: str) -> str:
    """Return output path for a PNG file."""
    if output.endswith(".png"):
        return output
    _ensure_dir(output)
    return os.path.join(output, f"{name}.png")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SnowPyt-MechParams parameter graph diagrams.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--type",
        dest="diagram_type",
        choices=["overview", "layer", "slab", "stability", "full", "all"],
        default="all",
        help="Which diagram to generate (default: all)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["mermaid", "matplotlib", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--output",
        default="docs/diagrams",
        help="Output file or directory (default: docs/diagrams/)",
    )
    args = parser.parse_args()

    # Import graph
    try:
        from snowpyt_mechparams.graph import graph
    except ImportError:
        print("Error: could not import graph. Run 'pip install -e .' first.")
        sys.exit(1)

    # Import visualisation modules lazily so missing matplotlib doesn't break
    # mermaid-only use
    if args.fmt in ("mermaid", "both"):
        from snowpyt_mechparams.graph.visualize import (
            save_mermaid_overview,
            save_mermaid_layer_detail,
            save_mermaid_slab_detail,
            save_mermaid_stability_detail,
            save_mermaid_full_detail,
        )

    if args.fmt in ("matplotlib", "both"):
        try:
            from snowpyt_mechparams.graph.visualize_matplotlib import (
                generate_matplotlib_overview,
                generate_matplotlib_layer_detail,
                generate_matplotlib_slab_detail,
                generate_matplotlib_stability_detail,
                generate_matplotlib_full_detail,
            )
            import matplotlib.pyplot as plt
        except ImportError as exc:
            print(f"Error: matplotlib not available — {exc}")
            sys.exit(1)

    # ------------------------------------------------------------------ #
    # Build list of (name, mermaid_fn, matplotlib_fn) to generate         #
    # ------------------------------------------------------------------ #

    ALL_DIAGRAMS = [
        ("overview",   "SnowPyt-MechParams — Overview"),
        ("layer",      "SnowPyt-MechParams — Layer Parameters"),
        ("slab",       "SnowPyt-MechParams — Slab Stiffnesses"),
        ("stability",  "SnowPyt-MechParams — Weak-Layer Parameters & Stability Criteria"),
        ("full",       "SnowPyt-MechParams — Full Parameter Graph"),
    ]

    if args.diagram_type == "all":
        selected = ALL_DIAGRAMS
    else:
        selected = [d for d in ALL_DIAGRAMS if d[0] == args.diagram_type]

    for name, title in selected:
        # --- Mermaid ---
        if args.fmt in ("mermaid", "both"):
            path = _mermaid_path(args.output, name)
            if name == "overview":
                save_mermaid_overview(graph, path, title=title)
            elif name == "layer":
                save_mermaid_layer_detail(graph, path, title=title)
            elif name == "slab":
                save_mermaid_slab_detail(graph, path, title=title)
            elif name == "stability":
                save_mermaid_stability_detail(graph, path, title=title)
            elif name == "full":
                save_mermaid_full_detail(graph, path, title=title)

        # --- Matplotlib ---
        if args.fmt in ("matplotlib", "both"):
            path = _png_path(args.output, name)
            if name == "overview":
                fig = generate_matplotlib_overview(graph)
            elif name == "layer":
                fig = generate_matplotlib_layer_detail(graph)
            elif name == "slab":
                fig = generate_matplotlib_slab_detail(graph)
            elif name == "stability":
                fig = generate_matplotlib_stability_detail(graph)
            elif name == "full":
                fig = generate_matplotlib_full_detail(graph)
            fig.savefig(path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            print(f"Saved matplotlib figure to: {path}")

    if not selected:
        print(f"Unknown diagram type: {args.diagram_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()
