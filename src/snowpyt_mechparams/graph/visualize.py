"""
Generate mermaid diagrams from the parameter graph.

This module provides utilities to visualize the parameter dependency graph
as mermaid diagrams for documentation and as matplotlib figures for publication.

Overview diagram
    One high-level diagram showing the conceptual parameter groups with
    simple arrows between them — no merge nodes, no method names.

Detail diagrams
    Three focused diagrams, one per subsystem, with method-labeled edges:
    - Layer parameters (density, E, ν, G)
    - Slab stiffnesses (A11, B11, D11, A55)
    - Slab weight pathways (W, W_s, W_s with E + ν)

Functions
---------
generate_mermaid_overview
    Big-picture diagram using subgraph blocks, no method names
generate_mermaid_layer_detail
    Layer parameter pathways with method names on edges
generate_mermaid_slab_detail
    Slab stiffness assembly with method names on edges
generate_mermaid_slab_weight_detail
    Slab weight pathways with method names on edges
generate_mermaid_diagram
    Full single-diagram output (kept for backwards compatibility)
save_mermaid_overview, save_mermaid_layer_detail, ...
    Convenience wrappers that write each diagram to a .md file
save_mermaid_diagram
    Backwards-compatible single-file save

Examples
--------
>>> from snowpyt_mechparams.graph import graph
>>> from snowpyt_mechparams.graph.visualize import (
...     save_mermaid_overview, save_mermaid_layer_detail,
...     save_mermaid_slab_detail, save_mermaid_slab_weight_detail,
... )
>>> save_mermaid_overview(graph, "docs/diagrams/overview.md")
>>> save_mermaid_layer_detail(graph, "docs/diagrams/layer.md")
>>> save_mermaid_slab_detail(graph, "docs/diagrams/slab.md")
>>> save_mermaid_slab_weight_detail(graph, "docs/diagrams/slab_weight.md")
"""

from typing import Dict, Iterable, List, Optional, Set

from snowpyt_mechparams.graph.parameter_graph import graph as PARAMETER_GRAPH
from snowpyt_mechparams.graph.structures import Graph, Node


# ==============================================================================
# Shared helpers
# ==============================================================================

def _classify_node(node: Node) -> str:
    """Classify a node into one of seven visualization categories."""
    param = node.parameter

    if param == "snow_pit":
        return "root"
    if node.type == "merge":
        return "merge"
    if param.startswith("measured_"):
        return "measured"
    if node.level == "slab":
        return "slab_calc"
    if node.level == "layer":
        return "layer_calc"
    if node.level == "weak_layer":
        return "weak_layer_calc"
    if node.level == "stability_model":
        return "stability_calc"
    return "layer_calc"


def _resolve_graph(graph: Optional[Graph]) -> Graph:
    """Return the provided graph, or the canonical parameter graph."""
    return PARAMETER_GRAPH if graph is None else graph


def _sanitize_node_id(parameter: str) -> str:
    """Convert parameter name to a valid mermaid node ID."""
    return parameter.replace(" ", "_").replace("-", "_")


# Human-readable single-line labels (no category tags — color conveys type).
_NODE_LABELS: Dict[str, str] = {
    "snow_pit": "snow pit",
    "measured_density": "density (measured)",
    "measured_hand_hardness": "hand hardness",
    "measured_grain_form": "grain form",
    "measured_grain_size": "grain size",
    "measured_layer_thickness": "layer thickness",
    "measured_slope_angle": "slope angle",
    "density": "ρ (density)",
    "elastic_modulus": "E (elastic modulus)",
    "poissons_ratio": "ν (Poisson's ratio)",
    "shear_modulus": "G (shear modulus)",
    "A11": "A11",
    "B11": "B11",
    "D11": "D11",
    "A55": "A55",
    "slab_weight": "slab weight (W)",
    "slab_weight_shear": "slab weight_shear (W_s)",
    "slab_weight_shear_with_elasticity": "slab weight_shear with elasticity",

    # Merge node labels (short, single line)
    "merge_hand_hardness_grain_form": "HH + grain form",
    "merge_hand_hardness_grain_form_grain_size": "HH + grain form + size",
    "merge_density_grain_form": "ρ + grain form",
    "merge_elastic_modulus_poissons_ratio": "E + ν (layer)",
    "merge_E_nu": "E + ν (all layers)",
    "merge_hi_G": "h_i + G (all layers)",
    "merge_hi_E_nu": "h_i + E + ν",
    "merge_slab_weight_inputs": "ρ + h_i",
    "merge_slab_weight_slope_angle": "W + slope angle",
    "merge_slab_weight_shear_elasticity": "W_s + E + ν",
}


def _label(node: Node) -> str:
    """Return the display label for a node."""
    return _NODE_LABELS.get(node.parameter, node.parameter)


def _get_node_label(node: Node) -> str:
    """Return the display label for a node (alias for :func:`_label`)."""
    return _label(node)


def _get_node_shape(node: Node) -> tuple[str, str]:
    """
    Get mermaid shape markers for a node.

    Returns
    -------
    tuple[str, str]
        Opening and closing shape markers, e.g. ``("[", "]")`` or ``("{", "}")``.
    """
    if node.type == "merge":
        return "{", "}"
    return "[", "]"


def _node_def(node: Node) -> str:
    """Return the mermaid node definition line (indented 4 spaces)."""
    nid = _sanitize_node_id(node.parameter)
    lbl = _label(node)
    if node.type == "merge":
        return f"    {nid}{{{lbl}}}"
    return f"    {nid}[{lbl}]"


def _edge_line(start: Node, end: Node, method: str | None = None) -> str:
    """Return a mermaid edge line (indented 4 spaces)."""
    sid = _sanitize_node_id(start.parameter)
    eid = _sanitize_node_id(end.parameter)
    if method:
        return f"    {sid} -->|{method}| {eid}"
    return f"    {sid} --> {eid}"


def _style_block(node_categories: Dict[str, List[Node]]) -> List[str]:
    """Return classDef and class-assignment lines."""
    lines = ["    %% Styling"]
    mapping = [
        ("root", "rootNode", "fill:#e1f5ff,stroke:#0288d1,stroke-width:3px"),
        ("measured", "measuredNode", "fill:#fff9c4,stroke:#f57f17,stroke-width:2px"),
        ("merge", "mergeNode", "fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px"),
        ("layer_calc", "layerCalc", "fill:#c8e6c9,stroke:#388e3c,stroke-width:2px"),
        ("slab_calc", "slabCalc", "fill:#ffccbc,stroke:#d84315,stroke-width:3px"),
        ("weak_layer_calc", "weakLayerCalc", "fill:#fff3e0,stroke:#e65100,stroke-width:2px"),
        ("stability_calc", "stabilityCalc", "fill:#fce4ec,stroke:#880e4f,stroke-width:3px"),
    ]
    for cat, cls, style in mapping:
        nodes = node_categories.get(cat, [])
        if nodes:
            lines.append(f"    classDef {cls} {style}")
            ids = ",".join(_sanitize_node_id(n.parameter) for n in nodes)
            lines.append(f"    class {ids} {cls}")
    return lines


def _mermaid_wrap(inner_lines: List[str]) -> str:
    """Wrap lines in a mermaid code fence and return as string."""
    return "\n".join(["```mermaid"] + inner_lines + ["```"])


def _node_map(graph: Graph) -> Dict[str, Node]:
    """Return graph nodes keyed by parameter name."""
    return {node.parameter: node for node in graph.nodes}


def _nodes_for_names(graph: Graph, names: Iterable[str]) -> List[Node]:
    """Return nodes in graph insertion order for the supplied names."""
    wanted = set(names)
    return [node for node in graph.nodes if node.parameter in wanted]


def _categories_for_nodes(nodes: Iterable[Node]) -> Dict[str, List[Node]]:
    """Categorize a collection of nodes for styling."""
    cats: Dict[str, List[Node]] = {
        "root": [],
        "measured": [],
        "merge": [],
        "layer_calc": [],
        "slab_calc": [],
        "weak_layer_calc": [],
        "stability_calc": [],
    }
    for node in nodes:
        cats[_classify_node(node)].append(node)
    return cats


def _ancestor_names(
    graph: Graph,
    targets: Iterable[str],
    stop_at: Optional[Iterable[str]] = None,
) -> Set[str]:
    """
    Return target nodes and their graph ancestors.

    Parameters in ``stop_at`` are included, but traversal does not continue
    beyond them. This keeps focused diagrams readable while still deriving
    the visible structure from the real graph edges.
    """
    stops = set(stop_at or ())
    node_lookup = _node_map(graph)
    seen: Set[str] = set()
    stack = [name for name in targets if name in node_lookup]

    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        if name in stops:
            continue

        node = node_lookup[name]
        for edge in node.incoming_edges:
            stack.append(edge.start.parameter)

    return seen


def _emit_nodes_and_edges(
    graph: Graph,
    node_names: Iterable[str],
    direction: str = "LR",
    abbreviate_methods: bool = False,
) -> str:
    """Render an induced mermaid subgraph for the selected node names."""
    selected = set(node_names)
    nodes = _nodes_for_names(graph, selected)
    cats = _categories_for_nodes(nodes)

    lines: List[str] = [f"graph {direction}", ""]
    for node in nodes:
        lines.append(_node_def(node))
    lines.append("")

    lines.append("    %% Edges")
    for edge in graph.edges:
        if edge.start.parameter in selected and edge.end.parameter in selected:
            method = edge.method_name
            if abbreviate_methods and method:
                method = _METHOD_ABBREV.get(method, method)
            lines.append(_edge_line(edge.start, edge.end, method))
    lines.append("")

    lines.extend(_style_block(cats))
    return _mermaid_wrap(lines)


def _slab_weight_params(graph: Graph) -> Set[str]:
    """Return slab-level parameters that describe the slab-weight branch."""
    return {
        node.parameter
        for node in graph.nodes
        if node.level == "slab" and node.parameter.startswith("slab_weight")
    }


def _slab_stiffness_params(graph: Graph) -> Set[str]:
    """Return slab-level parameters that are not part of slab-weight coverage."""
    weight_params = _slab_weight_params(graph)
    return {
        node.parameter
        for node in graph.nodes
        if node.level == "slab" and node.parameter not in weight_params
    }


def _merge_downstream_parameter_names(node: Node, seen: Optional[Set[str]] = None) -> Set[str]:
    """
    Return calculated parameters immediately downstream of a merge chain.

    The traversal follows merge-to-merge edges, but stops at parameter nodes.
    That lets us classify reusable layer merges as layer nodes even though
    those layer parameters later feed slab calculations.
    """
    seen = set() if seen is None else seen
    if node.parameter in seen:
        return set()
    seen.add(node.parameter)

    downstream: Set[str] = set()
    for edge in node.outgoing_edges:
        end = edge.end
        if end.type == "parameter":
            downstream.add(end.parameter)
        elif end.type == "merge":
            downstream.update(_merge_downstream_parameter_names(end, seen))
    return downstream


_FULL_GROUPS = [
    ("INPUTS", "Snow Pit Observations"),
    ("LAYER_MERGES", "Layer Merge Nodes"),
    ("LAYER", "Layer Parameters"),
    ("SLAB_MERGES", "Slab Stiffness Merge Nodes"),
    ("SLAB", "Slab Stiffnesses"),
    ("WEIGHT_MERGES", "Slab Weight Merge Nodes"),
    ("WEIGHT", "Slab Weight Pathways"),
    ("OTHER", "Other Nodes"),
]


def _full_group_for_node(graph: Graph, node: Node) -> str:
    """Assign a node to a full-detail diagram group using graph structure."""
    if node.parameter == "snow_pit" or node.parameter.startswith("measured_"):
        return "INPUTS"
    if node.type == "merge":
        downstream = _merge_downstream_parameter_names(node)
        if downstream & _slab_weight_params(graph):
            return "WEIGHT_MERGES"
        if downstream & _slab_stiffness_params(graph):
            return "SLAB_MERGES"
        if downstream & graph.layer_params:
            return "LAYER_MERGES"
        return "OTHER"
    if node.level == "layer":
        return "LAYER"
    if node.level == "slab":
        if node.parameter in _slab_weight_params(graph):
            return "WEIGHT"
        return "SLAB"
    return "OTHER"


def _group_nodes_for_full_detail(graph: Graph) -> Dict[str, List[Node]]:
    """Group graph nodes for the full-detail diagram."""
    groups: Dict[str, List[Node]] = {group_id: [] for group_id, _ in _FULL_GROUPS}
    for node in graph.nodes:
        groups[_full_group_for_node(graph, node)].append(node)
    return groups


# ==============================================================================
# Diagram 1 — Overview
# ==============================================================================

def generate_mermaid_overview(graph: Optional[Graph] = None) -> str:
    """
    Generate a high-level overview mermaid diagram.

    Five subgraph blocks represent the conceptual parameter groups.
    No merge nodes, no method names — just the flow between groups.

    Parameters
    ----------
    graph : Graph, optional
        The parameter dependency graph. If omitted, the canonical graph from
        :mod:`snowpyt_mechparams.graph.parameter_graph` is used.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    graph = _resolve_graph(graph)
    measured_nodes = [
        node for node in graph.nodes
        if node.parameter.startswith("measured_")
    ]
    layer_nodes = [
        node for node in graph.nodes
        if node.parameter in graph.layer_params
    ]
    slab_stiffness_nodes = [
        node for node in graph.nodes
        if node.parameter in _slab_stiffness_params(graph)
    ]
    slab_weight_nodes = [
        node for node in graph.nodes
        if node.parameter in _slab_weight_params(graph)
    ]

    lines = [
        "graph LR",
        "",
        "    subgraph INPUTS[Snow Pit Observations]",
    ]

    for node in measured_nodes:
        lines.append(_node_def(node))
    lines.extend([
        "    end",
        "",
        "    subgraph LAYER[Layer Parameters]",
    ])
    for node in layer_nodes:
        lines.append(_node_def(node))
    lines.extend([
        "    end",
        "",
        "    subgraph SLAB[Slab Stiffnesses]",
    ])
    for node in slab_stiffness_nodes:
        lines.append(_node_def(node))
    lines.extend([
        "    end",
        "",
        "    subgraph WEIGHT[Slab Weight Pathways]",
    ])
    for node in slab_weight_nodes:
        lines.append(_node_def(node))
    lines.extend([
        "    end",
        "",
        "    %% Group-level data flow",
        "    INPUTS --> LAYER",
        "    LAYER --> SLAB",
        "    INPUTS --> SLAB",
        "    INPUTS --> WEIGHT",
        "    LAYER --> WEIGHT",
        "",
        "    %% Styling",
        "    classDef inputGroup fill:#fff9c4,stroke:#f57f17,stroke-width:2px",
        "    classDef layerGroup fill:#c8e6c9,stroke:#388e3c,stroke-width:2px",
        "    classDef slabGroup fill:#ffccbc,stroke:#d84315,stroke-width:3px",
        "    classDef weightGroup fill:#fce4ec,stroke:#880e4f,stroke-width:3px",
        "    ",
    ])
    if measured_nodes:
        lines.append(
            "    class "
            + ",".join(_sanitize_node_id(node.parameter) for node in measured_nodes)
            + " inputGroup"
        )
    if layer_nodes:
        lines.append(
            "    class "
            + ",".join(_sanitize_node_id(node.parameter) for node in layer_nodes)
            + " layerGroup"
        )
    if slab_stiffness_nodes:
        lines.append(
            "    class "
            + ",".join(_sanitize_node_id(node.parameter) for node in slab_stiffness_nodes)
            + " slabGroup"
        )
    if slab_weight_nodes:
        lines.append(
            "    class "
            + ",".join(_sanitize_node_id(node.parameter) for node in slab_weight_nodes)
            + " weightGroup"
        )
    return _mermaid_wrap(lines)


# ==============================================================================
# Diagram 2 — Layer parameters (detail)
# ==============================================================================

def generate_mermaid_layer_detail(graph: Optional[Graph] = None) -> str:
    """
    Generate a detail mermaid diagram for layer parameter calculation paths.

    Shows measured inputs → merge nodes → density / E / ν / G with
    method names labeled on edges.

    Parameters
    ----------
    graph : Graph, optional
        The parameter dependency graph. If omitted, the canonical graph from
        :mod:`snowpyt_mechparams.graph.parameter_graph` is used.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    graph = _resolve_graph(graph)
    layer_node_names = _ancestor_names(graph, graph.layer_params)
    return _emit_nodes_and_edges(graph, layer_node_names, direction="TB")


# ==============================================================================
# Diagram 3 — Slab stiffnesses (detail)
# ==============================================================================

def generate_mermaid_slab_detail(graph: Optional[Graph] = None) -> str:
    """
    Generate a detail mermaid diagram for slab stiffness assembly.

    Shows layer parameters → slab merge nodes → A11 / B11 / D11 / A55
    with method names labeled on edges.

    Parameters
    ----------
    graph : Graph, optional
        The parameter dependency graph. If omitted, the canonical graph from
        :mod:`snowpyt_mechparams.graph.parameter_graph` is used.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    graph = _resolve_graph(graph)
    boundary_nodes = set(graph.layer_params) | {"measured_layer_thickness"}
    slab_node_names = _ancestor_names(
        graph,
        _slab_stiffness_params(graph),
        stop_at=boundary_nodes,
    )
    return _emit_nodes_and_edges(graph, slab_node_names, direction="LR")


# ==============================================================================
# Diagram 4 — Slab weight pathways (detail)
# ==============================================================================

def generate_mermaid_slab_weight_detail(graph: Optional[Graph] = None) -> str:
    """
    Generate a detail mermaid diagram for slab weight pathways.

    Shows measured inputs and layer parameters leading to slab weight,
    slope-parallel slab weight, and slab weight with elastic inputs.

    Parameters
    ----------
    graph : Graph, optional
        The parameter dependency graph. If omitted, the canonical graph from
        :mod:`snowpyt_mechparams.graph.parameter_graph` is used.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    graph = _resolve_graph(graph)
    boundary_nodes = {
        "density",
        "elastic_modulus",
        "poissons_ratio",
        "measured_layer_thickness",
        "measured_slope_angle",
    }
    slab_weight_node_names = _ancestor_names(
        graph,
        _slab_weight_params(graph),
        stop_at=boundary_nodes,
    )
    return _emit_nodes_and_edges(graph, slab_weight_node_names, direction="LR")


# ==============================================================================
# Full single-diagram (backwards-compatible)
# ==============================================================================

def generate_mermaid_diagram(
    graph: Optional[Graph] = None,
    title: str = "Parameter Dependency Graph",
) -> str:
    """
    Generate a single mermaid diagram containing the full parameter graph.

    Kept for backwards compatibility. For publication use, prefer the
    focused generators: :func:`generate_mermaid_overview`,
    :func:`generate_mermaid_layer_detail`, etc.

    Parameters
    ----------
    graph : Graph, optional
        The parameter dependency graph. If omitted, the canonical graph from
        :mod:`snowpyt_mechparams.graph.parameter_graph` is used.
    title : str, optional
        Title comment for the diagram.

    Returns
    -------
    str
        Mermaid diagram syntax as a string.
    """
    graph = _resolve_graph(graph)
    node_categories = _categories_for_nodes(graph.nodes)
    groups = _group_nodes_for_full_detail(graph)

    lines: List[str] = ["```mermaid", "graph TB", ""]

    def _emit_group(comment: str, nodes: List[Node]) -> None:
        if not nodes:
            return
        lines.append(f"    %% {comment}")
        for n in nodes:
            lines.append(_node_def(n))
        lines.append("    ")

    for group_id, title in _FULL_GROUPS:
        _emit_group(title, groups[group_id])

    lines.append("    %% All parameter relationships")
    for edge in graph.edges:
        lines.append(_edge_line(edge.start, edge.end, edge.method_name))

    lines.append("    ")
    lines.extend(_style_block(node_categories))
    lines.append("```")
    return "\n".join(lines)


# ==============================================================================
# Diagram 5 — Full detail (all nodes, all merge nodes, subgraph grouping)
# ==============================================================================

# Short edge-label abbreviations used in the full-detail diagram.
# Keys must match the method_name values stored on graph edges.
_METHOD_ABBREV: Dict[str, str] = {
    "geldsetzer":             "G09",
    "kim_jamieson_table2":    "KJ-t2",
    "kim_jamieson_table5":    "KJ-t5",
    "bergfeld":               "B23",
    "kochle":                 "K14",
    "wautier":                "W15",
    "schottner":              "S26",
    "srivastava":             "Sr16",
    "lame_relationship":      "Lam",
    "weissgraeber_rosendahl": "W&R",
    "sum_layer_weight":       "W",
    "slope_parallel_component": "W_s",
    "combine_shear_weight_and_elasticity": "W_s+Eν",
}

def generate_mermaid_full_detail(graph: Optional[Graph] = None) -> str:
    """
    Generate a full-detail mermaid diagram of the entire parameter graph.

    All nodes — including merge nodes — are shown, grouped into subgraph
    blocks.  Method names are abbreviated on edges.  Greek symbols are used
    in node labels where appropriate.

    Parameters
    ----------
    graph : Graph, optional
        The parameter dependency graph. If omitted, the canonical graph from
        :mod:`snowpyt_mechparams.graph.parameter_graph` is used.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    graph = _resolve_graph(graph)
    grouped_nodes = _group_nodes_for_full_detail(graph)

    lines: List[str] = ["graph LR", ""]

    # Emit subgraph blocks
    for sg_id, sg_title in _FULL_GROUPS:
        nodes = grouped_nodes[sg_id]
        if not nodes:
            continue
        lines.append(f'    subgraph {sg_id}["{sg_title}"]')
        for node in nodes:
            lines.append("    " + _node_def(node).lstrip())
        lines.append("    end")
        lines.append("")

    # Emit edges with abbreviated method labels
    lines.append("    %% Edges")
    for edge in graph.edges:
        if edge.method_name:
            abbrev = _METHOD_ABBREV.get(edge.method_name, edge.method_name)
            lines.append(_edge_line(edge.start, edge.end, abbrev))
        else:
            lines.append(_edge_line(edge.start, edge.end))
    lines.append("")

    # Styling: classify every node
    cats: Dict[str, List[Node]] = {
        "root": [], "measured": [], "merge": [],
        "layer_calc": [], "slab_calc": [], "weak_layer_calc": [], "stability_calc": [],
    }
    for n in graph.nodes:
        cats[_classify_node(n)].append(n)
    lines.extend(_style_block(cats))

    return _mermaid_wrap(lines)


# ==============================================================================
# Save helpers
# ==============================================================================

def _save(filepath: str, title: str, diagram: str) -> None:
    with open(filepath, "w") as f:
        f.write(f"# {title}\n\n")
        f.write(diagram)
        f.write("\n")
    print(f"Saved mermaid diagram to: {filepath}")


def save_mermaid_overview(
    graph: Optional[Graph],
    filepath: str,
    title: str = "SnowPyt-MechParams — Overview",
) -> None:
    """Save the high-level overview mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_overview(graph))


def save_mermaid_layer_detail(
    graph: Optional[Graph],
    filepath: str,
    title: str = "SnowPyt-MechParams — Layer Parameters",
) -> None:
    """Save the layer-parameters detail mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_layer_detail(graph))


def save_mermaid_slab_detail(
    graph: Optional[Graph],
    filepath: str,
    title: str = "SnowPyt-MechParams — Slab Stiffnesses",
) -> None:
    """Save the slab stiffness detail mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_slab_detail(graph))


def save_mermaid_slab_weight_detail(
    graph: Optional[Graph],
    filepath: str,
    title: str = "SnowPyt-MechParams — Slab Weight Pathways",
) -> None:
    """Save the slab-weight pathway mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_slab_weight_detail(graph))


def save_mermaid_full_detail(
    graph: Optional[Graph],
    filepath: str,
    title: str = "SnowPyt-MechParams — Full Parameter Graph",
) -> None:
    """Save the full-detail mermaid diagram (all nodes + subgraphs) to *filepath*."""
    _save(filepath, title, generate_mermaid_full_detail(graph))


def save_mermaid_diagram(
    graph: Optional[Graph],
    filepath: str,
    title: str = "Parameter Dependency Graph",
) -> None:
    """
    Generate and save the full single mermaid diagram to a file.

    Kept for backwards compatibility.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.
    filepath : str
        Path to output file.
    title : str, optional
        Title for the diagram.
    """
    _save(filepath, title, generate_mermaid_diagram(graph, title=title))


def print_mermaid_diagram(
    graph: Optional[Graph] = None,
    title: str = "Parameter Dependency Graph",
) -> None:
    """Generate and print the full mermaid diagram to stdout."""
    print(generate_mermaid_diagram(graph, title=title))


# ==============================================================================
# CLI when run as script
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        save_mermaid_diagram(
            PARAMETER_GRAPH,
            output_file,
            title="SnowPyt-MechParams Parameter Graph",
        )
    else:
        print_mermaid_diagram(title="SnowPyt-MechParams Parameter Graph")
