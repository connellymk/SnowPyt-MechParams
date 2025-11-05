from __future__ import annotations
from typing import List, Literal, Optional, Dict
from dataclasses import dataclass, field

NodeType = Literal["parameter", "merge"]


@dataclass
class Node:
    """Represents a node in the graph.
    
    A node can be either a 'parameter' node or a 'merge' node.
    Parameter nodes represent specific parameters, while merge nodes
    combine parameters that serve as inputs to a method for a parameter node.
    
    Attributes
    ----------
    type : NodeType
        Type of node: either 'parameter' or 'merge'
    parameter : str
        The parameter name or identifier for this node
    incoming_edges : List[Edge]
        List of edges pointing to this node (defaults to empty list)
    outgoing_edges : List[Edge]
        List of edges pointing from this node (defaults to empty list)
    """
    type: NodeType
    parameter: str
    incoming_edges: List[Edge] = field(default_factory=list, repr=False)
    outgoing_edges: List[Edge] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self.parameter:
            raise ValueError("Node parameter cannot be empty")
        if self.type not in ("parameter", "merge"):
            raise ValueError(f"Node type must be 'parameter' or 'merge', got '{self.type}'")
    
    def __hash__(self) -> int:
        """Make nodes hashable for use in sets/dicts."""
        return hash((self.type, self.parameter))


@dataclass
class Edge:
    """Represents a directed edge in the graph.
    
    Edges connect nodes in a directed manner. Some edges represent
    methods (transformations/calculations), while others represent
    simple data flow.
    
    When an edge is created, it automatically updates the incoming_edges
    and outgoing_edges of the connected nodes.
    
    Attributes
    ----------
    start : Node
        The source node of the edge
    end : Node
        The destination node of the edge
    method_name : Optional[str]
        If this edge represents a method/transformation, this contains
        the method name. None if the edge is just a data flow connection.
    """
    start: Node
    end: Node
    method_name: Optional[str] = None

    def __post_init__(self) -> None:
        """Automatically update connected nodes' edge lists."""
        # Add this edge to start node's outgoing edges
        if self not in self.start.outgoing_edges:
            self.start.outgoing_edges.append(self)
        
        # Add this edge to end node's incoming edges
        if self not in self.end.incoming_edges:
            self.end.incoming_edges.append(self)


@dataclass
class Graph:
    """Represents a directed graph of nodes and edges.
    
    The graph holds all nodes and edges, allowing for computation
    of various graph properties and traversals.
    
    Attributes
    ----------
    nodes : List[Node]
        List of all nodes in the graph
    edges : List[Edge]
        List of all edges in the graph
    """
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate graph consistency."""
        # Check that all edges reference valid nodes
        node_ids = {id(node) for node in self.nodes}
        for edge in self.edges:
            if id(edge.start) not in node_ids:
                raise ValueError(f"Edge references node not in graph: {edge.start}")
            if id(edge.end) not in node_ids:
                raise ValueError(f"Edge references node not in graph: {edge.end}")
    
    def get_node(self, parameter: str) -> Optional[Node]:
        """Get a node by its parameter name."""
        for node in self.nodes:
            if node.parameter == parameter:
                return node
        return None
    
    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        if node not in self.nodes:
            self.nodes.append(node)
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        if edge not in self.edges:
            self.edges.append(edge)
            # Ensure both nodes are in the graph
            self.add_node(edge.start)
            self.add_node(edge.end)


class GraphBuilder:
    """Builder class for constructing graphs with a fluent API.
    
    This provides a more concise way to build graphs compared to
    manually creating all nodes and edges.
    
    Example
    -------
    >>> builder = GraphBuilder()
    >>> snow_pit = builder.param("snow_pit")
    >>> density = builder.param("density")
    >>> builder.edge(snow_pit, density)
    >>> graph = builder.build()
    """
    
    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
    
    def param(self, name: str) -> Node:
        """Create or get a parameter node."""
        if name not in self._nodes:
            self._nodes[name] = Node(type="parameter", parameter=name)
        return self._nodes[name]
    
    def merge(self, name: str) -> Node:
        """Create or get a merge node."""
        if name not in self._nodes:
            self._nodes[name] = Node(type="merge", parameter=name)
        return self._nodes[name]
    
    def edge(self, start: Node, end: Node, method: Optional[str] = None) -> Edge:
        """Create an edge between two nodes."""
        edge = Edge(start=start, end=end, method_name=method)
        self._edges.append(edge)
        return edge
    
    def flow(self, start: Node, end: Node) -> Edge:
        """Create a data flow edge (no method) between two nodes."""
        return self.edge(start, end, method=None)
    
    def method_edge(self, start: Node, end: Node, method: str) -> Edge:
        """Create a method edge between two nodes."""
        return self.edge(start, end, method=method)
    
    def build(self) -> Graph:
        """Build and return the final graph."""
        return Graph(nodes=list(self._nodes.values()), edges=self._edges)
