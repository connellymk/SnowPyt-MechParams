"""Pathway fingerprinting and deduplication helpers."""

from __future__ import annotations

from snowpyt_mechparams.pathway.types import Parameterization, PathSegment


def method_fingerprint(parameterization: Parameterization) -> str:
    """Return a canonical key for the methods selected by a parameterization."""
    methods: dict[str, str] = {}
    skip_prefixes = ("measured_", "merge_")
    skip_names = {"snow_pit"}

    def record(segment: PathSegment) -> None:
        node = segment.to_node
        if (
            any(node.startswith(prefix) for prefix in skip_prefixes)
            or node in skip_names
        ):
            return
        methods[node] = segment.edge_name if segment.edge_name else "data_flow"

    for branch in parameterization.branches:
        for segment in branch.segments:
            record(segment)

    for _indices, _merge_node, continuation in parameterization.merge_points:
        for segment in continuation:
            record(segment)

    return "->".join(
        f"{parameter}:{method}" for parameter, method in sorted(methods.items())
    )
