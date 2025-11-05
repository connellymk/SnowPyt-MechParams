from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from data_structures import Node, Graph


@dataclass
class PathSegment:
    """Represents a segment of a path: node -- edge --> node"""
    from_node: str
    edge_name: str
    to_node: str
    
    def __str__(self) -> str:
        return f"{self.from_node} -- {self.edge_name} --> {self.to_node}"


@dataclass
class Branch:
    """Represents a single branch in a parameterization"""
    segments: List[PathSegment]
    
    def __str__(self) -> str:
        if not self.segments:
            return "(empty branch)"
        return " ".join([self.segments[0].from_node] + 
                       [f"-- {seg.edge_name} --> {seg.to_node}" for seg in self.segments])


@dataclass
class Parameterization:
    """Represents a complete parameterization with branches and merges"""
    branches: List[Branch]
    merge_points: List[Tuple[List[int], str, List[PathSegment]]]  # (branch_indices, merge_node_name, continuation_path)
    
    def __str__(self) -> str:
        result = []
        for i, branch in enumerate(self.branches, 1):
            result.append(f"branch {i}: {branch}")
        
        for branch_indices, merge_node, continuation in self.merge_points:
            branch_list = ", ".join([f"branch {i+1}" for i in branch_indices])
            if continuation:
                # Build the continuation path string
                cont_str = " ".join([f"-- {seg.edge_name} --> {seg.to_node}" for seg in continuation])
                result.append(f"merge {branch_list}: {merge_node} {cont_str}")
            else:
                result.append(f"merge {branch_list}: {merge_node}")
        
        return "\n".join(result)


@dataclass
class PathTree:
    """Internal representation of a path tree for building parameterizations"""
    node_name: str
    branches: List[Tuple['PathTree', str]]  # List of (subtree, edge_name) tuples
    edge_from_parent: Optional[str] = None  # Edge that led to this node
    is_merge: bool = False

def find_parameterizations(graph: Graph, target_parameter: Node) -> List[Parameterization]:
    """
    Find all parameterizations of the target parameter in the graph.
    
    Uses recursion with dynamic programming to traverse backwards from the target
    parameter to the snow_pit node, collecting all possible paths.
    
    Parameters
    ----------
    graph : Graph
        The parameter dependency graph
    target_parameter : Node
        The parameter node to find parameterizations for
    
    Returns
    -------
    List[Parameterization]
        List of all possible parameterizations, each showing branches and merge points
    """
    end_node = graph.get_node("snow_pit")
    
    # Memoization: cache results for each node
    memo: Dict[Node, List[PathTree]] = {}
    
    def backtrack(node: Node) -> List[PathTree]:
        """
        Recursively find all path trees from node back to snow_pit.
        
        Returns a list of PathTree objects, each representing one way to reach
        snow_pit from this node.
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
            def cartesian_product(lists: List[List[Tuple[PathTree, str]]]) -> List[List[Tuple[PathTree, str]]]:
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
                    branches=combination,  # Store (tree, edge_name) tuples
                    edge_from_parent=None,  # Merge nodes don't have a single parent edge
                    is_merge=True
                )
                all_trees.append(new_tree)
        
        memo[node] = all_trees
        return all_trees
    
    # Get all path trees starting from target
    path_trees = backtrack(target_parameter)
    
    # Convert PathTree objects to Parameterization objects
    parameterizations = []
    for tree in path_trees:
        param = _tree_to_parameterization(tree)
        parameterizations.append(param)
    
    return parameterizations


def _tree_to_parameterization(tree: PathTree) -> Parameterization:
    """
    Convert a PathTree to a Parameterization with branches and merge points.
    
    The tree represents the full dependency graph from target back to snow_pit.
    We need to flatten this into a list of branches and merge points.
    
    Strategy:
    - Traverse the tree from target to snow_pit
    - When we hit a merge node, split into multiple branches that end at the merge
    - The continuation path after the merge is stored with the merge point
    """
    branches = []
    merge_points = []
    closed_branches = set()  # Track branches that end at a merge and shouldn't be extended
    
    def process_node(node: PathTree, continuation_path: List[PathSegment]) -> List[int]:
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
            # The branch will be built up as we return from recursion
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
                
                # For each branch returned, we need to extend it to this merge
                for branch_idx in sub_indices:
                    # Check if this branch is closed (already ends at a merge)
                    if branch_idx in closed_branches:
                        # Branch is closed - don't extend it, just reference it
                        branch_indices.append(branch_idx)
                    elif branches[branch_idx].segments:
                        # Branch already has segments but isn't closed - add edge to current merge
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
                            if not n.branches:
                                return []
                            child, child_edge = n.branches[0]
                            child_path = build_path_to_merge(child)
                            seg = PathSegment(from_node=child.node_name, edge_name=child_edge, to_node=n.node_name)
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
            merge_points.append((branch_indices, node.node_name, continuation_path.copy()))
            
            # Mark these branches as closed (they end at this merge)
            for idx in branch_indices:
                closed_branches.add(idx)
            
            # Return the branch indices (they all end at this merge)
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
    
    # If there's no merge (simple path), the branch needs to be completed
    # by adding segments from snow_pit to target
    if not merge_points and len(branch_indices) == 1:
        # Build the path by traversing the tree
        def build_simple_path(node: PathTree) -> List[PathSegment]:
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