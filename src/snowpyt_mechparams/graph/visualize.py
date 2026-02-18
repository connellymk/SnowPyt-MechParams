"""
Generate mermaid diagrams from the parameter graph.

This module provides utilities to visualize the parameter dependency graph
as mermaid diagrams for documentation and understanding the calculation pathways.

Functions
---------
generate_mermaid_diagram
    Generate mermaid diagram syntax from a Graph object
save_mermaid_diagram
    Generate and save mermaid diagram to a file
print_mermaid_diagram
    Generate and print mermaid diagram to stdout

Examples
--------
>>> from snowpyt_mechparams.graph import graph
>>> from snowpyt_mechparams.graph.visualize import generate_mermaid_diagram
>>> 
>>> # Generate mermaid diagram
>>> diagram = generate_mermaid_diagram(graph)
>>> print(diagram)

>>> # Save to file
>>> save_mermaid_diagram(graph, "docs/parameter_graph.md")
"""

from typing import Dict, List, Set
from snowpyt_mechparams.graph.structures import Graph, Node


def _classify_node(node: Node) -> str:
    """
    Classify a node into visualization categories.
    
    Parameters
    ----------
    node : Node
        The node to classify
    
    Returns
    -------
    str
        One of: 'root', 'measured', 'merge', 'layer_calc', 'slab_calc'
    """
    param = node.parameter
    
    # Root node
    if param == "snow_pit":
        return "root"
    
    # Merge nodes
    if node.type == "merge":
        return "merge"
    
    # Measured parameters (all measured_* names, including measured_layer_thickness)
    if param.startswith("measured_"):
        return "measured"
    
    # Use the node's level tag to classify calculated parameters
    if node.level == "slab":
        return "slab_calc"
    if node.level == "layer":
        return "layer_calc"
    
    # Default to layer_calc for any untagged parameter nodes
    return "layer_calc"


def _sanitize_node_id(parameter: str) -> str:
    """
    Convert parameter name to valid mermaid node ID.
    
    Parameters
    ----------
    parameter : str
        The parameter name
    
    Returns
    -------
    str
        Sanitized ID safe for use in mermaid
    """
    # Replace underscores and spaces with underscores, remove special chars
    return parameter.replace(" ", "_").replace("-", "_")


def _get_node_label(node: Node) -> str:
    """
    Generate display label for a node.
    
    Parameters
    ----------
    node : Node
        The node to label
    
    Returns
    -------
    str
        Multi-line label for the node
    """
    param = node.parameter
    category = _classify_node(node)
    
    # Special labels for specific nodes
    labels = {
        "snow_pit": "snow_pit<br/>ROOT",
        "measured_density": "measured_density<br/>MEASURED",
        "measured_hand_hardness": "measured_hand_hardness<br/>MEASURED",
        "measured_grain_form": "measured_grain_form<br/>MEASURED",
        "measured_grain_size": "measured_grain_size<br/>MEASURED",
        "measured_layer_thickness": "measured_layer_thickness<br/>MEASURED",
        "density": "density<br/>CALCULATED",
        "elastic_modulus": "elastic_modulus<br/>CALCULATED",
        "poissons_ratio": "poissons_ratio<br/>CALCULATED",
        "shear_modulus": "shear_modulus<br/>CALCULATED",
        "D11": "D11<br/>Bending Stiffness<br/>SLAB",
        "A55": "A55<br/>Shear Stiffness<br/>SLAB",
        "A11": "A11<br/>Extensional Stiffness<br/>SLAB",
        "B11": "B11<br/>Bending-Extension Coupling<br/>SLAB",
        "zi": "zi<br/>spatial info",
    }
    
    if param in labels:
        return labels[param]
    
    # For merge nodes, format nicely
    if node.type == "merge":
        # Split on underscore and add line breaks for readability
        if param.startswith("merge_"):
            base = param[6:]  # Remove "merge_" prefix
            # Add line break after "merge"
            return f"merge_{base.replace('_', '<br/>_')}"
        return param.replace("_", "<br/>_")
    
    # Default: use parameter name with category
    return f"{param}<br/>{category.upper()}"


def _get_node_shape(node: Node) -> tuple[str, str]:
    """
    Get mermaid shape syntax for a node.
    
    Parameters
    ----------
    node : Node
        The node
    
    Returns
    -------
    tuple[str, str]
        Opening and closing shape markers (e.g., "[", "]" or "{", "}")
    """
    if node.type == "merge":
        return "{", "}"  # Diamond shape for merge nodes
    else:
        return "[", "]"  # Rectangle shape for parameter nodes


def generate_mermaid_diagram(graph: Graph, title: str = "Parameter Dependency Graph") -> str:
    """
    Generate mermaid diagram syntax from a parameter graph.
    
    Parameters
    ----------
    graph : Graph
        The parameter dependency graph
    title : str, optional
        Title comment for the diagram (default: "Parameter Dependency Graph")
    
    Returns
    -------
    str
        Mermaid diagram syntax as a string
    
    Examples
    --------
    >>> from snowpyt_mechparams.graph import graph
    >>> diagram = generate_mermaid_diagram(graph)
    >>> print(diagram)
    """
    lines = []
    lines.append("```mermaid")
    lines.append("graph TB")
    
    # Group nodes by category for organized output
    node_categories: Dict[str, List[Node]] = {
        "root": [],
        "measured": [],
        "merge": [],
        "layer_calc": [],
        "slab_calc": [],
    }
    
    for node in graph.nodes:
        category = _classify_node(node)
        node_categories[category].append(node)
    
    # Generate node definitions by category
    lines.append("    %% Root node")
    for node in node_categories["root"]:
        node_id = _sanitize_node_id(node.parameter)
        label = _get_node_label(node)
        open_shape, close_shape = _get_node_shape(node)
        lines.append(f"    {node_id}{open_shape}{label}{close_shape}")
    
    lines.append("    ")
    lines.append("    %% Measured parameter nodes")
    for node in node_categories["measured"]:
        node_id = _sanitize_node_id(node.parameter)
        label = _get_node_label(node)
        open_shape, close_shape = _get_node_shape(node)
        lines.append(f"    {node_id}{open_shape}{label}{close_shape}")
    
    lines.append("    ")
    lines.append("    %% Layer-level merge nodes")
    layer_merges = [n for n in node_categories["merge"] 
                    if n.parameter in {"merge_hand_hardness_grain_form",
                                      "merge_hand_hardness_grain_form_grain_size",
                                      "merge_density_grain_form"}]
    for node in layer_merges:
        node_id = _sanitize_node_id(node.parameter)
        label = _get_node_label(node)
        open_shape, close_shape = _get_node_shape(node)
        lines.append(f"    {node_id}{open_shape}{label}{close_shape}")
    
    lines.append("    ")
    lines.append("    %% Calculated layer parameters")
    for node in node_categories["layer_calc"]:
        node_id = _sanitize_node_id(node.parameter)
        label = _get_node_label(node)
        open_shape, close_shape = _get_node_shape(node)
        lines.append(f"    {node_id}{open_shape}{label}{close_shape}")
    
    lines.append("    ")
    lines.append("    %% Slab-level merge nodes")
    slab_merges = [n for n in node_categories["merge"] 
                   if n not in layer_merges]
    for node in slab_merges:
        node_id = _sanitize_node_id(node.parameter)
        label = _get_node_label(node)
        open_shape, close_shape = _get_node_shape(node)
        lines.append(f"    {node_id}{open_shape}{label}{close_shape}")
    
    lines.append("    ")
    lines.append("    %% Slab parameters")
    for node in node_categories["slab_calc"]:
        node_id = _sanitize_node_id(node.parameter)
        label = _get_node_label(node)
        open_shape, close_shape = _get_node_shape(node)
        lines.append(f"    {node_id}{open_shape}{label}{close_shape}")
    
    # Generate edges
    lines.append("    ")
    lines.append("    %% Snow pit to measured parameters (data flow)")
    snow_pit_edges = [e for e in graph.edges 
                      if e.start.parameter == "snow_pit"]
    for edge in snow_pit_edges:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        lines.append(f"    {start_id} --> {end_id}")
    
    lines.append("    ")
    lines.append("    %% Density pathways")
    density_edges = [e for e in graph.edges 
                     if (e.end.parameter == "density" and 
                         e.start.parameter != "snow_pit")]
    for edge in density_edges:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        if edge.method_name:
            lines.append(f"    {start_id} -->|{edge.method_name}| {end_id}")
        else:
            lines.append(f"    {start_id} --> {end_id}")
    
    # Add edges to density merge nodes
    density_merge_edges = [e for e in graph.edges
                          if e.end.parameter in {"merge_hand_hardness_grain_form",
                                                "merge_hand_hardness_grain_form_grain_size"}]
    for edge in density_merge_edges:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        lines.append(f"    {start_id} --> {end_id}")
    
    lines.append("    ")
    lines.append("    %% Elastic modulus pathways")
    # Edges to merge_density_grain_form
    merge_d_gf_in = [e for e in graph.edges 
                     if e.end.parameter == "merge_density_grain_form"]
    for edge in merge_d_gf_in:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        lines.append(f"    {start_id} --> {end_id}")
    
    # Edges from merge_density_grain_form to elastic_modulus
    elastic_edges = [e for e in graph.edges 
                     if (e.end.parameter == "elastic_modulus" and 
                         e.start.parameter == "merge_density_grain_form")]
    for edge in elastic_edges:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        if edge.method_name:
            lines.append(f"    {start_id} -->|{edge.method_name}| {end_id}")
        else:
            lines.append(f"    {start_id} --> {end_id}")
    
    lines.append("    ")
    lines.append("    %% Poisson's ratio pathways")
    poisson_edges = [e for e in graph.edges 
                     if e.end.parameter == "poissons_ratio"]
    for edge in poisson_edges:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        if edge.method_name:
            lines.append(f"    {start_id} -->|{edge.method_name}| {end_id}")
        else:
            lines.append(f"    {start_id} --> {end_id}")
    
    lines.append("    ")
    lines.append("    %% Shear modulus pathways")
    shear_edges = [e for e in graph.edges 
                   if e.end.parameter == "shear_modulus"]
    for edge in shear_edges:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        if edge.method_name:
            lines.append(f"    {start_id} -->|{edge.method_name}| {end_id}")
        else:
            lines.append(f"    {start_id} --> {end_id}")
    
    lines.append("    ")
    lines.append("    %% Slab-level calculations")
    slab_edges = [e for e in graph.edges
                  if (e.start.parameter in {"measured_layer_thickness", "elastic_modulus", 
                                           "poissons_ratio", "shear_modulus",
                                           "zi", "merge_E_nu", "merge_zi_E_nu",
                                           "merge_hi_G", "merge_hi_E_nu"} and
                      e.end.parameter in {"zi", "merge_E_nu", "merge_zi_E_nu",
                                         "merge_hi_G", "merge_hi_E_nu",
                                         "A11", "B11", "D11", "A55"})]
    for edge in slab_edges:
        start_id = _sanitize_node_id(edge.start.parameter)
        end_id = _sanitize_node_id(edge.end.parameter)
        if edge.method_name:
            lines.append(f"    {start_id} -->|{edge.method_name}| {end_id}")
        else:
            lines.append(f"    {start_id} --> {end_id}")
    
    # Add styling
    lines.append("    ")
    lines.append("    %% Styling")
    lines.append("    classDef rootNode fill:#e1f5ff,stroke:#0288d1,stroke-width:3px")
    lines.append("    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px")
    lines.append("    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px")
    lines.append("    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px")
    lines.append("    classDef slabCalc fill:#ffccbc,stroke:#d84315,stroke-width:3px")
    lines.append("    ")
    
    # Apply styles to nodes
    if node_categories["root"]:
        root_ids = [_sanitize_node_id(n.parameter) for n in node_categories["root"]]
        lines.append(f"    class {','.join(root_ids)} rootNode")
    
    if node_categories["measured"]:
        measured_ids = [_sanitize_node_id(n.parameter) for n in node_categories["measured"]]
        lines.append(f"    class {','.join(measured_ids)} measuredNode")
    
    if node_categories["merge"]:
        merge_ids = [_sanitize_node_id(n.parameter) for n in node_categories["merge"]]
        lines.append(f"    class {','.join(merge_ids)} mergeNode")
    
    if node_categories["layer_calc"]:
        layer_ids = [_sanitize_node_id(n.parameter) for n in node_categories["layer_calc"]]
        lines.append(f"    class {','.join(layer_ids)} layerCalc")
    
    if node_categories["slab_calc"]:
        slab_ids = [_sanitize_node_id(n.parameter) for n in node_categories["slab_calc"]]
        lines.append(f"    class {','.join(slab_ids)} slabCalc")
    
    lines.append("```")
    
    return "\n".join(lines)


def save_mermaid_diagram(
    graph: Graph, 
    filepath: str, 
    title: str = "Parameter Dependency Graph"
) -> None:
    """
    Generate and save mermaid diagram to a file.
    
    Parameters
    ----------
    graph : Graph
        The parameter dependency graph
    filepath : str
        Path to output file (typically .md or .mmd extension)
    title : str, optional
        Title for the diagram (default: "Parameter Dependency Graph")
    
    Examples
    --------
    >>> from snowpyt_mechparams.graph import graph
    >>> save_mermaid_diagram(graph, "docs/parameter_graph.md")
    """
    diagram = generate_mermaid_diagram(graph, title=title)
    
    with open(filepath, "w") as f:
        f.write(f"# {title}\n\n")
        f.write(diagram)
        f.write("\n")
    
    print(f"Saved mermaid diagram to: {filepath}")


def print_mermaid_diagram(graph: Graph, title: str = "Parameter Dependency Graph") -> None:
    """
    Generate and print mermaid diagram to stdout.
    
    Parameters
    ----------
    graph : Graph
        The parameter dependency graph
    title : str, optional
        Title for the diagram (default: "Parameter Dependency Graph")
    
    Examples
    --------
    >>> from snowpyt_mechparams.graph import graph
    >>> print_mermaid_diagram(graph)
    """
    diagram = generate_mermaid_diagram(graph, title=title)
    print(diagram)


# CLI interface when run as a script
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Import the graph
    try:
        from snowpyt_mechparams.graph import graph
    except ImportError:
        print("Error: Could not import graph. Make sure the package is installed.")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        save_mermaid_diagram(graph, output_file)
    else:
        # Print to stdout
        print_mermaid_diagram(graph)
