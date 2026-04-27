"""Pathway data structures produced by graph search."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PathSegment:
    """A single graph step in a calculation pathway."""

    from_node: str
    edge_name: str
    to_node: str

    def __str__(self) -> str:
        return f"{self.from_node} -- {self.edge_name} --> {self.to_node}"


@dataclass
class Branch:
    """A linear sequence of path segments."""

    segments: list[PathSegment]

    def __str__(self) -> str:
        if not self.segments:
            return "(empty branch)"
        return " ".join(
            [self.segments[0].from_node]
            + [f"-- {seg.edge_name} --> {seg.to_node}" for seg in self.segments]
        )


@dataclass
class Parameterization:
    """A complete method pathway from measured inputs to a target parameter."""

    branches: list[Branch]
    merge_points: list[tuple[list[int], str, list[PathSegment]]]

    def __str__(self) -> str:
        result = []
        for i, branch in enumerate(self.branches, 1):
            result.append(f"branch {i}: {branch}")

        for branch_indices, merge_node, continuation in self.merge_points:
            branch_list = ", ".join([f"branch {i + 1}" for i in branch_indices])
            if continuation:
                cont_str = " ".join(
                    [f"-- {seg.edge_name} --> {seg.to_node}" for seg in continuation]
                )
                result.append(f"merge {branch_list}: {merge_node} {cont_str}")
            else:
                result.append(f"merge {branch_list}: {merge_node}")

        return "\n".join(result)


@dataclass
class PathTree:
    """Internal tree representation used while building parameterizations."""

    node_name: str
    branches: list[tuple["PathTree", str]]
    edge_from_parent: str | None = None
    is_merge: bool = False
