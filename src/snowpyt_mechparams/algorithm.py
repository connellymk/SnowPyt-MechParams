"""
Parameterization algorithm for finding calculation pathways.

This module provides the core algorithm for finding all possible calculation
pathways from measured inputs (snow pit data) to target parameters. The
algorithm uses graph traversal with dynamic programming to efficiently
enumerate all valid calculation paths.

Key Concepts
------------

**Parameterization**: A complete calculation pathway from snow_pit to a target
parameter, showing all required branches and where they merge.

**Branch**: A linear sequence of calculation steps (parameter → method → parameter).

**Merge Point**: A location where multiple branches combine their results as
inputs to a method. All branches feeding a merge must be computed before
continuing past the merge.

Algorithm Overview
------------------

The algorithm performs a backward traversal from the target parameter to the
snow_pit root node:

1. **Parameter Nodes** (OR logic): Try each incoming edge independently.
   Each edge represents an alternative method for calculating the parameter.

2. **Merge Nodes** (AND logic): Must include ALL incoming edges.
   All input parameters are required for the merge.

3. **Dynamic Programming**: Cache results for each node to avoid redundant
   computation when the same node appears in multiple paths.

The result is a list of Parameterization objects, each representing one
complete way to calculate the target parameter from measured inputs.

Execution Order
---------------

When executing a parameterization:

1. **Layer-level calculations**: Process each layer sequentially, computing
   all required parameters on that layer.

2. **Slab-level calculations**: After all layers are complete, compute slab
   parameters (A11, B11, D11, A55) which require properties from all layers.

This two-phase execution ensures that slab-level calculations have all
necessary layer properties available.

Classes
-------
PathSegment
    Represents one step: node --[method]--> node
Branch
    Linear sequence of PathSegments
Parameterization
    Complete pathway with branches and merge points
PathTree
    Internal tree structure for building parameterizations

Functions
---------
find_parameterizations(graph, target_parameter)
    Find all calculation pathways to a target parameter

Examples
--------
Finding all ways to calculate elastic modulus:

>>> from snowpyt_mechparams.graph import graph
>>> from snowpyt_mechparams.algorithm import find_parameterizations
>>>
>>> # Get the elastic_modulus node
>>> E_node = graph.get_node("elastic_modulus")
>>>
>>> # Find all pathways
>>> pathways = find_parameterizations(graph, E_node)
>>> print(f"Found {len(pathways)} pathways")
Found 16 pathways
>>>
>>> # Each pathway shows the calculation steps
>>> print(pathways[0])
branch 1: snow_pit -- data_flow --> measured_density -- data_flow --> density
branch 2: snow_pit -- data_flow --> measured_grain_form
merge branch 1, branch 2: merge_density_grain_form -- bergfeld --> elastic_modulus

Finding all ways to calculate D11:

>>> D11_node = graph.get_node("D11")
>>> pathways = find_parameterizations(graph, D11_node)
>>> print(f"Found {len(pathways)} pathways")
Found 32 pathways  # (4 density methods) × (4 E methods) × (2 ν methods)
                   # Duplicate structural traversals are removed before returning.
>>>
>>> # D11 requires elastic_modulus and poissons_ratio on all layers
>>> # Plus layer thickness for spatial weighting
>>> for i, pathway in enumerate(pathways[:3], 1):
...     print(f"\nPathway {i}:")
...     print(pathway)

Notes
-----
- The algorithm finds ALL possible pathways, including those that may fail
  at execution time due to missing measured inputs.
- Pathways are independent - executing one does not affect others.
- Dynamic programming makes the algorithm efficient even for large graphs
  with many alternative methods.

See Also
--------
snowpyt_mechparams.graph : Parameter dependency graph definition
snowpyt_mechparams.execution : Execution engine for running pathways
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from snowpyt_mechparams.graph.structures import Graph, Node


def _method_fingerprint(parameterization: 'Parameterization') -> str:
    """
    Return a canonical string key that uniquely identifies the set of
    (parameter, method) choices made by a Parameterization.

    Two Parameterization objects with different graph-traversal structures
    but identical (parameter → method) mappings will produce the same key.
    This is used inside find_parameterizations to discard redundant traversals
    before returning.

    Parameters
    ----------
    parameterization : Parameterization
        The parameterization to fingerprint.

    Returns
    -------
    str
        Sorted, joined ``parameter:method`` pairs, e.g.
        ``"D11:weissgraeber_rosendahl->density:geldsetzer->elastic_modulus:bergfeld->..."``.
    """
    methods: Dict[str, str] = {}

    skip_prefixes = ("measured_", "merge_")
    skip_names = {"snow_pit"}

    def _record(segment: 'PathSegment') -> None:
        node = segment.to_node
        if any(node.startswith(p) for p in skip_prefixes) or node in skip_names:
            return
        methods[node] = segment.edge_name if segment.edge_name else "data_flow"

    for branch in parameterization.branches:
        for seg in branch.segments:
            _record(seg)

    for _indices, _merge_node, continuation in parameterization.merge_points:
        for seg in continuation:
            _record(seg)

    return "->".join(f"{p}:{m}" for p, m in sorted(methods.items()))


@dataclass
class PathSegment:
    """
    Represents a single step in a calculation pathway.
    
    A path segment shows how one parameter is calculated from another:
    from_node --[edge_name]--> to_node
    
    Attributes
    ----------
    from_node : str
        Source parameter name
    edge_name : str
        Method name or "data_flow" for direct connections
    to_node : str
        Destination parameter name
    
    Examples
    --------
    >>> seg = PathSegment(
    ...     from_node="density",
    ...     edge_name="bergfeld",
    ...     to_node="elastic_modulus"
    ... )
    >>> print(seg)
    density -- bergfeld --> elastic_modulus
    """
    from_node: str
    edge_name: str
    to_node: str
    
    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.from_node} -- {self.edge_name} --> {self.to_node}"


@dataclass
class Branch:
    """
    Represents a linear sequence of calculation steps.
    
    A branch shows a path from snow_pit to some parameter through a
    series of transformations. Multiple branches can converge at a
    merge point.
    
    Attributes
    ----------
    segments : List[PathSegment]
        Ordered list of calculation steps in this branch
    
    Examples
    --------
    >>> branch = Branch(segments=[
    ...     PathSegment("snow_pit", "data_flow", "measured_density"),
    ...     PathSegment("measured_density", "data_flow", "density"),
    ... ])
    >>> print(branch)
    snow_pit -- data_flow --> measured_density -- data_flow --> density
    """
    segments: List[PathSegment]
    
    def __str__(self) -> str:
        """Return human-readable representation."""
        if not self.segments:
            return "(empty branch)"
        return " ".join(
            [self.segments[0].from_node] + 
            [f"-- {seg.edge_name} --> {seg.to_node}" for seg in self.segments]
        )


@dataclass
class Parameterization:
    """
    Represents a complete calculation pathway from snow_pit to target.
    
    A parameterization includes:
    - Multiple branches (linear calculation sequences)
    - Merge points where branches combine
    - Continuation paths after merges
    
    This structure allows the execution engine to:
    1. Identify all required input parameters
    2. Determine calculation dependencies
    3. Execute methods in the correct order
    
    Attributes
    ----------
    branches : List[Branch]
        All branches in this parameterization
    merge_points : List[Tuple[List[int], str, List[PathSegment]]]
        Merge information: (branch_indices, merge_node_name, continuation_path)
        - branch_indices: Which branches feed into this merge
        - merge_node_name: Name of the merge node
        - continuation_path: Steps to take after the merge
    
    Examples
    --------
    >>> # Simple parameterization with no merges
    >>> param = Parameterization(
    ...     branches=[Branch(segments=[
    ...         PathSegment("snow_pit", "data_flow", "measured_grain_form"),
    ...         PathSegment("measured_grain_form", "kochle", "poissons_ratio"),
    ...     ])],
    ...     merge_points=[]
    ... )
    >>> print(param)
    branch 1: snow_pit -- data_flow --> measured_grain_form -- kochle --> poissons_ratio
    
    >>> # Parameterization with merge
    >>> param = Parameterization(
    ...     branches=[
    ...         Branch(segments=[...]),  # density path
    ...         Branch(segments=[...]),  # grain_form path
    ...     ],
    ...     merge_points=[
    ...         ([0, 1], "merge_density_grain_form", [
    ...             PathSegment("merge_density_grain_form", "bergfeld", "elastic_modulus")
    ...         ])
    ...     ]
    ... )
    """
    branches: List[Branch]
    merge_points: List[Tuple[List[int], str, List[PathSegment]]]
    
    def __str__(self) -> str:
        """Return human-readable representation."""
        result = []
        
        # Show all branches
        for i, branch in enumerate(self.branches, 1):
            result.append(f"branch {i}: {branch}")
        
        # Show all merge points with continuations
        for branch_indices, merge_node, continuation in self.merge_points:
            branch_list = ", ".join([f"branch {i+1}" for i in branch_indices])
            if continuation:
                # Build the continuation path string
                cont_str = " ".join(
                    [f"-- {seg.edge_name} --> {seg.to_node}" for seg in continuation]
                )
                result.append(f"merge {branch_list}: {merge_node} {cont_str}")
            else:
                result.append(f"merge {branch_list}: {merge_node}")
        
        return "\n".join(result)


@dataclass
class PathTree:
    """
    Internal tree representation for building parameterizations.
    
    This is an intermediate data structure used during the backward
    traversal from target to snow_pit. After traversal, PathTrees
    are converted to Parameterization objects.
    
    Attributes
    ----------
    node_name : str
        Name of this node in the graph
    branches : List[Tuple[PathTree, str]]
        Child subtrees with their edge names
    edge_from_parent : Optional[str]
        Edge that led to this node from parent
    is_merge : bool
        Whether this node is a merge node
    
    Notes
    -----
    This is an internal class not exposed in the public API.
    """
    node_name: str
    branches: List[Tuple['PathTree', str]]
    edge_from_parent: Optional[str] = None
    is_merge: bool = False


def find_parameterizations(
    graph: Graph,
    target_parameter: Node
) -> List[Parameterization]:
    """
    Find all calculation pathways from snow_pit to target parameter.
    
    This function performs a backward traversal from the target parameter
    to the snow_pit root, using dynamic programming to cache intermediate
    results. It handles both parameter nodes (OR logic - try each method)
    and merge nodes (AND logic - all inputs required).
    
    Parameters
    ----------
    graph : Graph
        The parameter dependency graph
    target_parameter : Node
        The parameter node to find pathways for
    
    Returns
    -------
    List[Parameterization]
        All possible parameterizations, each showing branches and merge points.
        The number of parameterizations equals the product of alternative
        methods at each decision point.
    
    Examples
    --------
    Find pathways for elastic modulus:
    
    >>> from snowpyt_mechparams.graph import graph
    >>> E_node = graph.get_node("elastic_modulus")
    >>> pathways = find_parameterizations(graph, E_node)
    >>> len(pathways)
    16
    
    Find pathways for D11:
    
    >>> D11_node = graph.get_node("D11")
    >>> pathways = find_parameterizations(graph, D11_node)
    >>> len(pathways)
    32
    
    Examine a specific pathway:
    
    >>> pathway = pathways[0]
    >>> print(pathway)
    branch 1: snow_pit -- data_flow --> measured_density -- data_flow --> density
    branch 2: snow_pit -- data_flow --> measured_grain_form
    merge branch 1, branch 2: merge_density_grain_form -- bergfeld --> elastic_modulus
    ...
    
    Notes
    -----
    - Uses dynamic programming: each node's pathways are computed once
    - Handles cyclic dependencies (though the current graph is acyclic)
    - Returns empty list if no pathways exist (disconnected node)
    
    Algorithm Complexity
    --------------------
    - Time: O(V + E) where V = nodes, E = edges, with memoization
    - Space: O(V × P) where P = average pathways per node
    
    See Also
    --------
    Parameterization : The returned data structure
    snowpyt_mechparams.execution.executor : Executes parameterizations
    """
    end_node = graph.get_node("snow_pit")
    
    # Memoization: cache results for each node
    memo: Dict[Node, List[PathTree]] = {}
    
    def backtrack(node: Node) -> List[PathTree]:
        """
        Recursively find all path trees from node back to snow_pit.
        
        Returns a list of PathTree objects, each representing one way to
        reach snow_pit from this node.
        
        Parameters
        ----------
        node : Node
            Current node to process
        
        Returns
        -------
        List[PathTree]
            All possible path trees from this node to snow_pit
        """
        # Check memoization cache
        if node in memo:
            return memo[node]
        
        # Base case: reached snow_pit (root)
        if node == end_node:
            return [PathTree(node_name=node.parameter, branches=[])]
        
        all_trees = []
        
        if node.type == "parameter":
            # For parameter nodes: try each incoming edge independently (OR logic)
            # Each edge represents a different way to calculate this parameter
            for edge in node.incoming_edges:
                edge_name = edge.method_name if edge.method_name else "data_flow"
                
                # Recursively get all path trees from the source node
                source_trees = backtrack(edge.start)
                
                # Create a new tree for each source tree
                for source_tree in source_trees:
                    new_tree = PathTree(
                        node_name=node.parameter,
                        branches=[(source_tree, edge_name)],
                        edge_from_parent=edge_name,
                        is_merge=False
                    )
                    all_trees.append(new_tree)
        
        elif node.type == "merge":
            # For merge nodes: must include ALL incoming edges (AND logic)
            # All inputs are required for the merge
            if not node.incoming_edges:
                memo[node] = []
                return []
            
            # Get path trees for each input
            input_trees_list = []
            for edge in node.incoming_edges:
                edge_name = edge.method_name if edge.method_name else "data_flow"
                source_trees = backtrack(edge.start)
                
                # Attach edge name to each tree
                trees_with_edge = [(tree, edge_name) for tree in source_trees]
                input_trees_list.append(trees_with_edge)
            
            # Compute cartesian product: combine one tree from each input
            def cartesian_product(
                lists: List[List[Tuple[PathTree, str]]]
            ) -> List[List[Tuple[PathTree, str]]]:
                """Compute cartesian product of lists."""
                if not lists:
                    return [[]]
                result: List[List[Tuple[PathTree, str]]] = []
                for item in lists[0]:
                    for rest in cartesian_product(lists[1:]):
                        result.append([item] + rest)
                return result
            
            combinations = cartesian_product(input_trees_list)
            
            # Create a tree for each combination
            for combination in combinations:
                # combination is already a list of (tree, edge_name) tuples
                new_tree = PathTree(
                    node_name=node.parameter,
                    branches=combination,
                    edge_from_parent=None,
                    is_merge=True
                )
                all_trees.append(new_tree)
        
        memo[node] = all_trees
        return all_trees
    
    # Get all path trees starting from target
    path_trees = backtrack(target_parameter)

    # Convert PathTree objects to Parameterization objects, then deduplicate.
    #
    # The graph traversal can produce multiple structurally distinct trees that
    # resolve to the same (parameter → method) mapping.  This happens when a
    # parameter node is reachable via more than one branch of a merge node
    # (e.g. `density` feeds both `elastic_modulus` and `srivastava`, so the
    # Cartesian-product merge logic enumerates all cross-combinations of the
    # two density sub-paths).  At execution time those combinations are
    # identical, so only the first occurrence of each unique fingerprint is kept.
    seen: set = set()
    parameterizations = []
    for tree in path_trees:
        param = _tree_to_parameterization(tree)
        key = _method_fingerprint(param)
        if key not in seen:
            seen.add(key)
            parameterizations.append(param)

    return parameterizations


def _tree_to_parameterization(tree: PathTree) -> Parameterization:
    """
    Convert a PathTree to a Parameterization with branches and merge points.
    
    The tree represents the full dependency graph from target back to snow_pit.
    We flatten this into a list of branches and merge points for execution.
    
    Strategy:
    - Traverse the tree from target to snow_pit
    - When we hit a merge node, split into multiple branches that end at the merge
    - The continuation path after the merge is stored with the merge point
    
    Parameters
    ----------
    tree : PathTree
        The path tree to convert
    
    Returns
    -------
    Parameterization
        Flattened representation with branches and merges
    """
    branches = []
    merge_points = []
    closed_branches = set()  # Track branches that end at a merge
    
    def process_node(
        node: PathTree,
        continuation_path: List[PathSegment]
    ) -> List[int]:
        """
        Process a node and return list of branch indices.
        
        Parameters
        ----------
        node : PathTree
            The current node being processed
        continuation_path : List[PathSegment]
            Path segments from this node to the target (for merge nodes)
        
        Returns
        -------
        List[int]
            List of branch indices that reach this node
        """
        # Base case: reached snow_pit (leaf node)
        if not node.branches:
            # Create a branch starting from snow_pit
            branch = Branch(segments=[])
            branches.append(branch)
            return [len(branches) - 1]
        
        # Merge node: all inputs must be included
        if node.is_merge:
            branch_indices = []
            
            # Process each input to the merge
            for sub_tree, edge_name in node.branches:
                # Recursively process each input (no continuation path for inputs)
                sub_indices = process_node(sub_tree, [])
                
                # For each branch returned, extend it to this merge
                for branch_idx in sub_indices:
                    # Check if this branch is closed (already ends at a merge)
                    if branch_idx in closed_branches:
                        # Branch is closed - don't extend it, just reference it
                        branch_indices.append(branch_idx)
                    elif branches[branch_idx].segments:
                        # Branch has segments but isn't closed - add edge to merge
                        segment = PathSegment(
                            from_node=sub_tree.node_name,
                            edge_name=edge_name,
                            to_node=node.node_name
                        )
                        branches[branch_idx].segments.append(segment)
                        branch_indices.append(branch_idx)
                    else:
                        # Empty branch - build complete path from snow_pit
                        def build_path_to_merge(n: PathTree) -> List[PathSegment]:
                            """Build path from snow_pit to node."""
                            if not n.branches:
                                return []
                            child, child_edge = n.branches[0]
                            child_path = build_path_to_merge(child)
                            seg = PathSegment(
                                from_node=child.node_name,
                                edge_name=child_edge,
                                to_node=n.node_name
                            )
                            return child_path + [seg]
                        
                        # Get path from snow_pit to sub_tree
                        path_to_subtree = build_path_to_merge(sub_tree)
                        
                        # Add segment from sub_tree to merge
                        segment = PathSegment(
                            from_node=sub_tree.node_name,
                            edge_name=edge_name,
                            to_node=node.node_name
                        )
                        
                        branches[branch_idx].segments = path_to_subtree + [segment]
                        branch_indices.append(branch_idx)
            
            # Record the merge point with its continuation path
            merge_points.append((
                branch_indices,
                node.node_name,
                continuation_path.copy()
            ))
            
            # Mark these branches as closed (they end at this merge)
            for idx in branch_indices:
                closed_branches.add(idx)
            
            return branch_indices
        
        # Regular parameter node: continue the path
        else:
            sub_tree, edge_name = node.branches[0]
            
            # Build the segment from child to current node
            segment = PathSegment(
                from_node=sub_tree.node_name,
                edge_name=edge_name,
                to_node=node.node_name
            )
            
            # Add this segment to the continuation path
            new_continuation = [segment] + continuation_path
            
            # Recursively process the child with the extended continuation
            return process_node(sub_tree, new_continuation)
    
    # Start processing from the root (target parameter)
    branch_indices = process_node(tree, [])
    
    # If there's no merge (simple path), complete the branch
    if not merge_points and len(branch_indices) == 1:
        # Build the path by traversing the tree
        def build_simple_path(node: PathTree) -> List[PathSegment]:
            """Build a simple linear path from snow_pit to target."""
            if not node.branches:
                return []
            sub_tree, edge_name = node.branches[0]
            child_segments = build_simple_path(sub_tree)
            segment = PathSegment(
                from_node=sub_tree.node_name,
                edge_name=edge_name,
                to_node=node.node_name
            )
            return child_segments + [segment]
        
        branches[branch_indices[0]].segments = build_simple_path(tree)
    
    return Parameterization(branches=branches, merge_points=merge_points)


__all__ = [
    "PathSegment",
    "Branch",
    "Parameterization",
    "PathTree",
    "find_parameterizations",
    "_method_fingerprint",
]
