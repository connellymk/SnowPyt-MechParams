"""
Graph data structures for parameter dependency representation.

This module provides the core data structures for representing parameter
calculation dependencies as a directed graph. The graph consists of:

- **Parameter nodes**: Represent measured or calculated parameters
- **Merge nodes**: Represent combinations of parameters used as method inputs  
- **Edges**: Represent data flow or calculation methods connecting nodes

These structures are used by the parameterization algorithm to find all
possible calculation pathways from measured inputs to target parameters.

Classes
-------
Node
    A node in the parameter graph (parameter or merge type)
Edge
    A directed edge connecting two nodes (with optional method)
Graph
    Container for nodes and edges with query methods
GraphBuilder
    Fluent API for constructing graphs

Examples
--------
Building a simple graph:

>>> builder = GraphBuilder()
>>> snow_pit = builder.param("snow_pit")
>>> density = builder.param("density")
>>> builder.flow(snow_pit, density)
>>> graph = builder.build()

Querying the graph:

>>> node = graph.get_node("density")
>>> print(node.parameter)
density
>>> print(len(node.incoming_edges))
1

See Also
--------
snowpyt_mechparams.graph.definitions : Complete parameter graph definition
snowpyt_mechparams.algorithm : Pathfinding algorithms for the graph
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

# Type alias for node types
NodeType = Literal["parameter", "merge"]


@dataclass
class Node:
    """
    Represents a node in the parameter dependency graph.
    
    A node can be either a 'parameter' node (representing a measured or
    calculated parameter) or a 'merge' node (representing a combination
    of parameters that serve as inputs to a calculation method).
    
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
    
    Examples
    --------
    >>> node = Node(type="parameter", parameter="density")
    >>> print(node.parameter)
    density
    >>> print(len(node.incoming_edges))
    0
    
    Notes
    -----
    Nodes are hashable and can be used in sets and dictionaries.
    Edges automatically update the incoming_edges and outgoing_edges
    lists when created.
    """
    type: NodeType
    parameter: str
    incoming_edges: List[Edge] = field(default_factory=list, repr=False)
    outgoing_edges: List[Edge] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Validate node after initialization."""
        if not self.parameter:
            raise ValueError("Node parameter cannot be empty")
        if self.type not in ("parameter", "merge"):
            raise ValueError(
                f"Node type must be 'parameter' or 'merge', got '{self.type}'"
            )
    
    def __hash__(self) -> int:
        """Make nodes hashable for use in sets/dicts."""
        return hash((self.type, self.parameter))


@dataclass
class Edge:
    """
    Represents a directed edge in the parameter dependency graph.
    
    Edges connect nodes in a directed manner. Some edges represent
    calculation methods (transformations), while others represent
    simple data flow (no transformation).
    
    When an edge is created, it automatically updates the incoming_edges
    and outgoing_edges lists of the connected nodes.
    
    Attributes
    ----------
    start : Node
        The source node of the edge
    end : Node
        The destination node of the edge
    method_name : Optional[str]
        If this edge represents a calculation method, this contains
        the method name. None if the edge is just a data flow connection.
    
    Examples
    --------
    >>> snow_pit = Node(type="parameter", parameter="snow_pit")
    >>> density = Node(type="parameter", parameter="density")
    >>> edge = Edge(start=snow_pit, end=density, method_name=None)
    >>> print(edge.method_name)
    None
    >>> print(len(snow_pit.outgoing_edges))
    1
    
    Notes
    -----
    The __post_init__ method automatically updates the edge lists of
    both connected nodes, so you don't need to manually manage these
    relationships.
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
    """
    Represents a directed graph of parameter dependencies.
    
    The graph holds all nodes and edges, allowing for computation
    of various graph properties and traversals. Used by the
    parameterization algorithm to find calculation pathways.
    
    Attributes
    ----------
    nodes : List[Node]
        List of all nodes in the graph
    edges : List[Edge]
        List of all edges in the graph
    
    Examples
    --------
    >>> graph = Graph(nodes=[node1, node2], edges=[edge1])
    >>> density_node = graph.get_node("density")
    >>> if density_node:
    ...     print(f"Found {density_node.parameter}")
    Found density
    
    Notes
    -----
    The graph validates consistency on initialization, ensuring all
    edges reference nodes that exist in the graph.
    """
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate graph consistency."""
        # Check that all edges reference valid nodes
        node_ids = {id(node) for node in self.nodes}
        for edge in self.edges:
            if id(edge.start) not in node_ids:
                raise ValueError(
                    f"Edge references node not in graph: {edge.start}"
                )
            if id(edge.end) not in node_ids:
                raise ValueError(
                    f"Edge references node not in graph: {edge.end}"
                )
    
    def get_node(self, parameter: str) -> Optional[Node]:
        """
        Get a node by its parameter name.
        
        Parameters
        ----------
        parameter : str
            The parameter name to search for
        
        Returns
        -------
        Optional[Node]
            The node with matching parameter name, or None if not found
        
        Examples
        --------
        >>> node = graph.get_node("density")
        >>> if node:
        ...     print(f"Found {node.type} node")
        Found parameter node
        """
        for node in self.nodes:
            if node.parameter == parameter:
                return node
        return None
    
    def add_node(self, node: Node) -> None:
        """
        Add a node to the graph.
        
        Parameters
        ----------
        node : Node
            The node to add
        
        Notes
        -----
        If the node is already in the graph, this is a no-op.
        """
        if node not in self.nodes:
            self.nodes.append(node)
    
    def add_edge(self, edge: Edge) -> None:
        """
        Add an edge to the graph.
        
        Parameters
        ----------
        edge : Edge
            The edge to add
        
        Notes
        -----
        If the edge is already in the graph, this is a no-op.
        Automatically ensures both connected nodes are in the graph.
        """
        if edge not in self.edges:
            self.edges.append(edge)
            # Ensure both nodes are in the graph
            self.add_node(edge.start)
            self.add_node(edge.end)


class GraphBuilder:
    """
    Builder class for constructing parameter dependency graphs.
    
    This provides a fluent API for building graphs that is more concise
    than manually creating all nodes and edges. Use the builder to
    create nodes and define connections, then call build() to get the
    final Graph object.
    
    Methods
    -------
    param(name)
        Create or get a parameter node
    merge(name)
        Create or get a merge node
    flow(start, end)
        Create a data flow edge (no method)
    method_edge(start, end, method)
        Create a method edge with a method name
    build()
        Build and return the final Graph object
    
    Examples
    --------
    >>> builder = GraphBuilder()
    >>> snow_pit = builder.param("snow_pit")
    >>> density = builder.param("density")
    >>> elastic_modulus = builder.param("elastic_modulus")
    >>> 
    >>> # Create merge node for density + grain_form
    >>> merge_d_gf = builder.merge("merge_density_grain_form")
    >>> 
    >>> # Connect them
    >>> builder.flow(snow_pit, density)
    >>> builder.flow(density, merge_d_gf)
    >>> builder.method_edge(merge_d_gf, elastic_modulus, "bergfeld")
    >>> 
    >>> graph = builder.build()
    >>> print(len(graph.nodes))
    4
    >>> print(len(graph.edges))
    3
    
    Notes
    -----
    Calling param() or merge() with the same name multiple times
    returns the same node instance, ensuring nodes are unique by name.
    """
    
    def __init__(self) -> None:
        """Initialize an empty builder."""
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
    
    def param(self, name: str) -> Node:
        """
        Create or get a parameter node.
        
        Parameters
        ----------
        name : str
            The parameter name
        
        Returns
        -------
        Node
            The parameter node (created if new, existing if already created)
        
        Examples
        --------
        >>> builder = GraphBuilder()
        >>> density = builder.param("density")
        >>> print(density.type)
        parameter
        """
        if name not in self._nodes:
            self._nodes[name] = Node(type="parameter", parameter=name)
        return self._nodes[name]
    
    def merge(self, name: str) -> Node:
        """
        Create or get a merge node.
        
        Parameters
        ----------
        name : str
            The merge node name
        
        Returns
        -------
        Node
            The merge node (created if new, existing if already created)
        
        Examples
        --------
        >>> builder = GraphBuilder()
        >>> merge = builder.merge("merge_density_grain_form")
        >>> print(merge.type)
        merge
        """
        if name not in self._nodes:
            self._nodes[name] = Node(type="merge", parameter=name)
        return self._nodes[name]
    
    def edge(self, start: Node, end: Node, method: Optional[str] = None) -> Edge:
        """
        Create an edge between two nodes.
        
        Parameters
        ----------
        start : Node
            The source node
        end : Node
            The destination node
        method : Optional[str]
            The method name if this is a method edge
        
        Returns
        -------
        Edge
            The created edge
        """
        edge = Edge(start=start, end=end, method_name=method)
        self._edges.append(edge)
        return edge
    
    def flow(self, start: Node, end: Node) -> Edge:
        """
        Create a data flow edge (no method) between two nodes.
        
        Parameters
        ----------
        start : Node
            The source node
        end : Node
            The destination node
        
        Returns
        -------
        Edge
            The created edge with method_name=None
        
        Examples
        --------
        >>> builder = GraphBuilder()
        >>> snow_pit = builder.param("snow_pit")
        >>> density = builder.param("density")
        >>> builder.flow(snow_pit, density)
        Edge(...)
        """
        return self.edge(start, end, method=None)
    
    def method_edge(self, start: Node, end: Node, method: str) -> Edge:
        """
        Create a method edge between two nodes.
        
        Parameters
        ----------
        start : Node
            The source node (inputs to the method)
        end : Node
            The destination node (output of the method)
        method : str
            The method name
        
        Returns
        -------
        Edge
            The created edge with the specified method_name
        
        Examples
        --------
        >>> builder = GraphBuilder()
        >>> merge = builder.merge("merge_density_grain_form")
        >>> elastic_modulus = builder.param("elastic_modulus")
        >>> builder.method_edge(merge, elastic_modulus, "bergfeld")
        Edge(...)
        """
        return self.edge(start, end, method=method)
    
    def build(self) -> Graph:
        """
        Build and return the final Graph object.
        
        Returns
        -------
        Graph
            The constructed graph containing all nodes and edges
        
        Examples
        --------
        >>> builder = GraphBuilder()
        >>> # ... create nodes and edges ...
        >>> graph = builder.build()
        >>> print(len(graph.nodes))
        """
        return Graph(nodes=list(self._nodes.values()), edges=self._edges)
