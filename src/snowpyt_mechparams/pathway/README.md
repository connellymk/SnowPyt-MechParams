# pathway

Graph search and pathway dataclasses.

- `types.py` defines `PathSegment`, `Branch`, `Parameterization`, and the internal `PathTree`.
- `search.py` provides `find_parameterizations(graph, target_node)`.
- `fingerprint.py` deduplicates structurally different traversals that resolve to the same parameter-to-method choices.

Pathway search is data-independent: it only uses graph structure. Missing measurements, invalid grain forms, and out-of-range values are handled later by `execution`.
