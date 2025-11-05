from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from data_structures import Node, Graph


@dataclass
class PathSegment:
    """Represents a segment of a path: node -> edge -> node"""
    from_node: str
    edge_name: str
    to_node: str
    
    def __str__(self) -> str:
        return f"{self.from_node} -> {self.edge_name} -> {self.to_node}"


@dataclass
class Branch:
    """Represents a single branch in a parameterization"""
    segments: List[PathSegment]
    
    def __str__(self) -> str:
        if not self.segments:
            return "(empty branch)"
        return " -> ".join([self.segments[0].from_node] + 
                          [f"{seg.edge_name} -> {seg.to_node}" for seg in self.segments])


@dataclass
class Parameterization:
    """Represents a complete parameterization with branches and merges"""
    branches: List[Branch]
    merge_points: List[Tuple[List[int], str]]  # (branch_indices, merge_node_name)
    
    def __str__(self) -> str:
        result = []
        for i, branch in enumerate(self.branches, 1):
            result.append(f"branch {i}: {branch}")
        
        for branch_indices, merge_node in self.merge_points:
            branch_list = ", ".join([f"branch {i+1}" for i in branch_indices])
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
    - Build paths in reverse (target -> snow_pit), then reverse them at the end
    - When we hit a merge node, split into multiple branches
    - Each branch goes from snow_pit to the merge point
    - After the merge, the path continues to the target
    """
    branches = []
    merge_points = []
    
    def build_path_segments(from_node: PathTree, to_node_name: str, edge_name: str) -> List[PathSegment]:
        """Helper to create a single path segment."""
        return [PathSegment(from_node=from_node.node_name, edge_name=edge_name, to_node=to_node_name)]
    
    def process_node(node: PathTree) -> List[Tuple[int, List[PathSegment]]]:
        """
        Process a node and return list of (branch_index, path_from_branch_to_node) tuples.
        
        Returns
        -------
        List[Tuple[int, List[PathSegment]]]
            Each tuple contains:
            - branch_index: the index of a branch that reaches this node
            - path: the path segments from that branch's end to this node
        """
        # Base case: reached snow_pit (leaf node)
        if not node.branches:
            # Create a branch for snow_pit
            branch = Branch(segments=[])
            branches.append(branch)
            return [(len(branches) - 1, [])]
        
        # Merge node: all inputs must be included
        if node.is_merge:
            branch_info: List[Tuple[int, List[PathSegment]]] = []
            
            # Process each input to the merge
            for sub_tree, edge_name in node.branches:
                # Recursively process each input
                sub_results = process_node(sub_tree)
                
                # For each result, the path should end at the merge node
                for branch_idx, path_to_subtree in sub_results:
                    # Extend this branch's path to include the edge to merge
                    segment = PathSegment(
                        from_node=sub_tree.node_name,
                        edge_name=edge_name,
                        to_node=node.node_name
                    )
                    branches[branch_idx].segments.extend(path_to_subtree)
                    branches[branch_idx].segments.append(segment)
                    
                    branch_info.append((branch_idx, []))
            
            # Record the merge point
            branch_indices = [idx for idx, _ in branch_info]
            merge_points.append((branch_indices, node.node_name))
            
            # Return info about all branches that meet at this merge
            # Note: The edge from this merge node to its parent will be handled by the parent
            # We return empty paths because all branches end at the merge point
            return branch_info
        
        # Regular parameter node: continue the path
        else:
            sub_tree, edge_name = node.branches[0]
            
            # Recursively process the child
            sub_results = process_node(sub_tree)
            
            # Add the edge from child to current node
            results = []
            for branch_idx, path_to_subtree in sub_results:
                new_path = path_to_subtree.copy()
                segment = PathSegment(
                    from_node=sub_tree.node_name,
                    edge_name=edge_name,
                    to_node=node.node_name
                )
                new_path.append(segment)
                results.append((branch_idx, new_path))
            
            return results
    
    # Start processing from the root (target parameter)
    results = process_node(tree)
    
    # Add any remaining path segments to branches
    for branch_idx, remaining_path in results:
        branches[branch_idx].segments.extend(remaining_path)
    
    return Parameterization(branches=branches, merge_points=merge_points)