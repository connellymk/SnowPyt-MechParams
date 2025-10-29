from __future__ import annotations
from typing import List, Literal, Optional
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
    incoming_edges: List[Edge] = field(default_factory=list)
    outgoing_edges: List[Edge] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.parameter:
            raise ValueError("Node parameter cannot be empty")
        if self.type not in ("parameter", "merge"):
            raise ValueError(f"Node type must be 'parameter' or 'merge', got '{self.type}'")


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