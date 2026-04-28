"""Search a parameter graph for executable calculation pathways."""

from __future__ import annotations

from snowpyt_mechparams.graph.structures import Graph, Node
from snowpyt_mechparams.pathway.fingerprint import method_fingerprint
from snowpyt_mechparams.pathway.types import (
    Branch,
    Parameterization,
    PathSegment,
    PathTree,
)


def find_parameterizations(
    graph: Graph, target_parameter: Node
) -> list[Parameterization]:
    """Find all calculation pathways from ``snow_pit`` to a target parameter."""
    end_node = graph.get_node("snow_pit")
    memo: dict[Node, list[PathTree]] = {}

    def backtrack(node: Node) -> list[PathTree]:
        if node in memo:
            return memo[node]

        if node == end_node:
            return [PathTree(node_name=node.parameter, branches=[])]

        all_trees = []
        if node.type == "parameter":
            for edge in node.incoming_edges:
                edge_name = edge.method_name if edge.method_name else "data_flow"
                source_trees = backtrack(edge.start)
                for source_tree in source_trees:
                    all_trees.append(
                        PathTree(
                            node_name=node.parameter,
                            branches=[(source_tree, edge_name)],
                            edge_from_parent=edge_name,
                            is_merge=False,
                        )
                    )
        elif node.type == "merge":
            if not node.incoming_edges:
                memo[node] = []
                return []

            input_trees_list = []
            for edge in node.incoming_edges:
                edge_name = edge.method_name if edge.method_name else "data_flow"
                source_trees = backtrack(edge.start)
                input_trees_list.append([(tree, edge_name) for tree in source_trees])

            for combination in _cartesian_product(input_trees_list):
                all_trees.append(
                    PathTree(
                        node_name=node.parameter,
                        branches=combination,
                        edge_from_parent=None,
                        is_merge=True,
                    )
                )

        memo[node] = all_trees
        return all_trees

    seen: set[str] = set()
    parameterizations = []
    for tree in backtrack(target_parameter):
        parameterization = _tree_to_parameterization(tree)
        key = method_fingerprint(parameterization)
        if key not in seen:
            seen.add(key)
            parameterizations.append(parameterization)

    return parameterizations


def _cartesian_product(
    lists: list[list[tuple[PathTree, str]]],
) -> list[list[tuple[PathTree, str]]]:
    """Return the Cartesian product of pathway tree choices."""
    if not lists:
        return [[]]
    result: list[list[tuple[PathTree, str]]] = []
    for item in lists[0]:
        for rest in _cartesian_product(lists[1:]):
            result.append([item] + rest)
    return result


def _tree_to_parameterization(tree: PathTree) -> Parameterization:
    """Convert an internal path tree into a flattened parameterization."""
    branches: list[Branch] = []
    merge_points: list[tuple[list[int], str, list[PathSegment]]] = []
    closed_branches: set[int] = set()

    def build_path_to_merge(node: PathTree) -> list[PathSegment]:
        if not node.branches:
            return []
        child, child_edge = node.branches[0]
        child_path = build_path_to_merge(child)
        return child_path + [
            PathSegment(
                from_node=child.node_name,
                edge_name=child_edge,
                to_node=node.node_name,
            )
        ]

    def process_node(node: PathTree, continuation_path: list[PathSegment]) -> list[int]:
        if not node.branches:
            branch = Branch(segments=[])
            branches.append(branch)
            return [len(branches) - 1]

        if node.is_merge:
            branch_indices = []
            for sub_tree, edge_name in node.branches:
                sub_indices = process_node(sub_tree, [])
                for branch_idx in sub_indices:
                    if branch_idx in closed_branches:
                        branch_indices.append(branch_idx)
                    elif branches[branch_idx].segments:
                        branches[branch_idx].segments.append(
                            PathSegment(
                                from_node=sub_tree.node_name,
                                edge_name=edge_name,
                                to_node=node.node_name,
                            )
                        )
                        branch_indices.append(branch_idx)
                    else:
                        path_to_subtree = build_path_to_merge(sub_tree)
                        segment = PathSegment(
                            from_node=sub_tree.node_name,
                            edge_name=edge_name,
                            to_node=node.node_name,
                        )
                        branches[branch_idx].segments = path_to_subtree + [segment]
                        branch_indices.append(branch_idx)

            merge_points.append(
                (branch_indices, node.node_name, continuation_path.copy())
            )
            for idx in branch_indices:
                closed_branches.add(idx)
            return branch_indices

        sub_tree, edge_name = node.branches[0]
        segment = PathSegment(
            from_node=sub_tree.node_name,
            edge_name=edge_name,
            to_node=node.node_name,
        )
        return process_node(sub_tree, [segment] + continuation_path)

    branch_indices = process_node(tree, [])
    if not merge_points and len(branch_indices) == 1:
        branches[branch_indices[0]].segments = _build_simple_path(tree)

    return Parameterization(branches=branches, merge_points=merge_points)


def _build_simple_path(node: PathTree) -> list[PathSegment]:
    """Build a simple linear path from ``snow_pit`` to target."""
    if not node.branches:
        return []
    sub_tree, edge_name = node.branches[0]
    return _build_simple_path(sub_tree) + [
        PathSegment(
            from_node=sub_tree.node_name,
            edge_name=edge_name,
            to_node=node.node_name,
        )
    ]
