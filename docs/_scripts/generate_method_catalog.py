"""Generate the registry-backed methods/provenance documentation page."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
OUTPUT = ROOT / "docs" / "methods.md"

sys.path.insert(0, str(SRC))

from snowpyt_mechparams.methods import default_registry  # noqa: E402

HEADER = """# Methods And Provenance

This page is generated from `snowpyt_mechparams.methods.default_registry()`.
Update registry metadata, then regenerate this file instead of hand-editing the
table.

```bash
uv run --extra dev python docs/_scripts/generate_method_catalog.py
uv run --extra dev python docs/_scripts/generate_method_catalog.py --check
```

The table records graph dependencies, runtime inputs, output attributes, cache
scope, citation labels, and short descriptions for every built-in method.

"""

FOOTER = """

## Source Materials

The `sources/` directory contains reference materials used to implement the
published parameterizations. Those files are retained for traceability in the
repository but are not included in installed packages.

Formula-level docstrings in `src/snowpyt_mechparams/methods/` provide equation
notes, units, uncertainty behavior, supported grain forms, and validity ranges.
"""


def _format_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "-"


def _cell(value: str | None) -> str:
    text = value or "-"
    return text.replace("|", "\\|").replace("\n", " ")


def build_catalog() -> str:
    """Return the complete Markdown catalog."""
    rows = [
        "| Target | Method | Level | Graph inputs | Runtime inputs | Output attribute | Cache | Citation | Description |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for spec in default_registry().all():
        rows.append(
            " | ".join(
                [
                    f"| `{_cell(spec.target)}`",
                    f"`{_cell(spec.method_name)}`",
                    f"`{_cell(spec.level.value)}`",
                    _format_tuple(spec.source_nodes),
                    _format_tuple(spec.required_inputs),
                    f"`{_cell(spec.output_attr)}`",
                    f"`{_cell(spec.cache_scope)}`",
                    _cell(spec.citation),
                    _cell(spec.description),
                ]
            )
            + " |"
        )
    return HEADER + "\n".join(rows) + FOOTER


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if docs/methods.md differs from registry metadata",
    )
    args = parser.parse_args()

    content = build_catalog()
    if args.check:
        existing = OUTPUT.read_text() if OUTPUT.exists() else ""
        if existing != content:
            print(
                f"{OUTPUT.relative_to(ROOT)} is stale; run "
                "python docs/_scripts/generate_method_catalog.py",
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT.write_text(content)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
