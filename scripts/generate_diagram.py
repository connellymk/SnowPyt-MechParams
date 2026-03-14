#!/usr/bin/env python3
"""
Standalone script to generate mermaid diagram of the parameter graph.

Run after installing the package (pip install -e .):
    python scripts/generate_diagram.py [output_file.md]

If no output file is specified, the diagram is printed to stdout.
"""

import sys

from snowpyt_mechparams.graph import graph
from snowpyt_mechparams.graph.visualize import save_mermaid_diagram, print_mermaid_diagram


def main() -> None:
    """Main entry point for diagram generation."""
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        save_mermaid_diagram(graph, output_file, title="SnowPyt-MechParams Parameter Graph")
        print(f"Diagram saved to: {output_file}")
    else:
        print_mermaid_diagram(graph, title="SnowPyt-MechParams Parameter Graph")


if __name__ == "__main__":
    main()
