# Graph Visualization

Graph diagrams are generated from the canonical parameter graph so the
documentation stays aligned with the implemented calculation pathways.

## Canonical Diagrams

The generated diagram set lives in `docs/diagrams/`:

- `overview.md` / `overview.png` — high-level parameter groups
- `layer.md` / `layer.png` — layer-parameter pathways
- `slab.md` / `slab.png` — slab-stiffness pathways
- `slab_weight.md` / `slab_weight.png` — slab-weight pathway targets
- `full.md` / `full.png` — full parameter graph

The slab-weight diagram intentionally uses slab-weight language rather than
stability language. Roch and WEAC remain available as direct stability-criteria
APIs, but they are not graph targets.

## Regeneration

From the repository root:

```bash
python scripts/generate_diagram.py --type all --format both --output docs/diagrams/
```

Generate a single diagram by replacing `all` with one of:
`overview`, `layer`, `slab`, `slab_weight`, or `full`.

## Python API

```python
from snowpyt_mechparams.graph import graph
from snowpyt_mechparams.graph.visualize import save_mermaid_full_detail

save_mermaid_full_detail(graph, "docs/diagrams/full.md")
```

Focused Mermaid helpers are named `generate_mermaid_*_detail` and
`save_mermaid_*_detail`; the matplotlib helpers are named
`generate_matplotlib_*_detail`.
