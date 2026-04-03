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
    - Stability criteria inputs (slab_elasticity_parameters, weak_layer_info* placeholder)

Functions
---------
generate_mermaid_overview
    Big-picture diagram using subgraph blocks, no method names
generate_mermaid_layer_detail
    Layer parameter pathways with method names on edges
generate_mermaid_slab_detail
    Slab stiffness assembly with method names on edges
generate_mermaid_stability_detail
    Weak-layer parameters and stability criteria with method names on edges
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
...     save_mermaid_slab_detail, save_mermaid_stability_detail,
... )
>>> save_mermaid_overview(graph, "docs/diagrams/overview.md")
>>> save_mermaid_layer_detail(graph, "docs/diagrams/layer_params.md")
>>> save_mermaid_slab_detail(graph, "docs/diagrams/slab_params.md")
>>> save_mermaid_stability_detail(graph, "docs/diagrams/stability.md")
"""

from typing import Dict, List
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
    "density": "ρ (density)",
    "elastic_modulus": "E (elastic modulus)",
    "poissons_ratio": "ν (Poisson's ratio)",
    "shear_modulus": "G (shear modulus)",
    "A11": "A11",
    "B11": "B11",
    "D11": "D11",
    "A55": "A55",
    "weak_layer_info*": "weak layer info* (placeholder)",
    "g_delta": "g_Δ (WEAC)",
    "s_r": "S_r (Roch natural)",

    # Merge node labels (short, single line)
    "merge_hand_hardness_grain_form": "HH + grain form",
    "merge_hand_hardness_grain_form_grain_size": "HH + grain form + size",
    "merge_density_grain_form": "ρ + grain form",
    "merge_elastic_modulus_poissons_ratio": "E + ν (layer)",
    "merge_E_nu": "E + ν (all layers)",
    "merge_hi_G": "h_i + G (all layers)",
    "merge_hi_E_nu": "h_i + E + ν",
    "slab_elasticity_parameters": "slab elasticity (E + ν)",
    "merge_weac_inputs": "WEAC inputs",
    "merge_roch_inputs": "Roch inputs",
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
    lines = [
        "    %% Styling",
        "    classDef rootNode fill:#e1f5ff,stroke:#0288d1,stroke-width:3px",
        "    classDef measuredNode fill:#fff9c4,stroke:#f57f17,stroke-width:2px",
        "    classDef mergeNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px",
        "    classDef layerCalc fill:#c8e6c9,stroke:#388e3c,stroke-width:2px",
        "    classDef slabCalc fill:#ffccbc,stroke:#d84315,stroke-width:3px",
        "    classDef weakLayerCalc fill:#fff3e0,stroke:#e65100,stroke-width:2px",
        "    classDef stabilityCalc fill:#fce4ec,stroke:#880e4f,stroke-width:3px",
        "    ",
    ]
    mapping = [
        ("root", "rootNode"),
        ("measured", "measuredNode"),
        ("merge", "mergeNode"),
        ("layer_calc", "layerCalc"),
        ("slab_calc", "slabCalc"),
        ("weak_layer_calc", "weakLayerCalc"),
        ("stability_calc", "stabilityCalc"),
    ]
    for cat, cls in mapping:
        nodes = node_categories.get(cat, [])
        if nodes:
            ids = ",".join(_sanitize_node_id(n.parameter) for n in nodes)
            lines.append(f"    class {ids} {cls}")
    return lines


def _mermaid_wrap(inner_lines: List[str]) -> str:
    """Wrap lines in a mermaid code fence and return as string."""
    return "\n".join(["```mermaid"] + inner_lines + ["```"])


# ==============================================================================
# Diagram 1 — Overview
# ==============================================================================

def generate_mermaid_overview(graph: Graph) -> str:
    """
    Generate a high-level overview mermaid diagram.

    Five subgraph blocks represent the conceptual parameter groups.
    No merge nodes, no method names — just the flow between groups.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph (used only for node existence checks).

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    lines = [
        "graph LR",
        "",
        "    subgraph INPUTS[Snow Pit Observations]",
        "        meas_density[density]",
        "        meas_hh[hand hardness]",
        "        meas_gf[grain form]",
        "        meas_gs[grain size]",
        "        meas_thick[layer thickness]",
        "    end",
        "",
        "    subgraph LAYER[Layer Parameters]",
        "        rho[ρ — density]",
        "        E[E — elastic modulus]",
        "        nu[ν — Poisson's ratio]",
        "        G[G — shear modulus]",
        "    end",
        "",
        "    subgraph SLAB[Slab Stiffnesses]",
        "        A11[A11]",
        "        B11[B11]",
        "        D11[D11]",
        "        A55[A55]",
        "    end",
        "",
        "    subgraph WEAKLAYER[Weak-Layer Info]",
        "        wl_info[weak layer info* — placeholder]",
        "    end",
        "",
        "    subgraph STABILITY[Stability Criteria]",
        "        elast[slab elasticity params — E + ν]",
        "        gdelta[g_Δ — WEAC skier]",
        "        sr[S_r — Roch natural]",
        "    end",
        "",
        "    %% Group-level data flow",
        "    INPUTS --> LAYER",
        "    LAYER --> SLAB",
        "    LAYER --> STABILITY",
        "    WEAKLAYER --> STABILITY",
        "",
        "    %% Styling",
        "    classDef inputGroup fill:#fff9c4,stroke:#f57f17,stroke-width:2px",
        "    classDef layerGroup fill:#c8e6c9,stroke:#388e3c,stroke-width:2px",
        "    classDef slabGroup fill:#ffccbc,stroke:#d84315,stroke-width:3px",
        "    classDef wlGroup fill:#fff3e0,stroke:#e65100,stroke-width:2px",
        "    classDef stabGroup fill:#fce4ec,stroke:#880e4f,stroke-width:3px",
        "    ",
        "    class meas_density,meas_hh,meas_gf,meas_gs,meas_thick inputGroup",
        "    class rho,E,nu,G layerGroup",
        "    class A11,B11,D11,A55 slabGroup",
        "    class wl_info wlGroup",
        "    class elast,gdelta,sr stabGroup",
    ]
    return _mermaid_wrap(lines)


# ==============================================================================
# Diagram 2 — Layer parameters (detail)
# ==============================================================================

def generate_mermaid_layer_detail(graph: Graph) -> str:
    """
    Generate a detail mermaid diagram for layer parameter calculation paths.

    Shows measured inputs → merge nodes → density / E / ν / G with
    method names labeled on edges.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    # Node names relevant to this subgraph
    layer_node_names = {
        "snow_pit",
        "measured_density", "measured_hand_hardness",
        "measured_grain_form", "measured_grain_size",
        "merge_hand_hardness_grain_form",
        "merge_hand_hardness_grain_form_grain_size",
        "merge_density_grain_form",
        "merge_elastic_modulus_poissons_ratio",
        "density", "elastic_modulus", "poissons_ratio", "shear_modulus",
    }

    node_map = {n.parameter: n for n in graph.nodes
                if n.parameter in layer_node_names}

    # Categorise for styling
    cats: Dict[str, List[Node]] = {
        "root": [], "measured": [], "merge": [],
        "layer_calc": [], "slab_calc": [], "weak_layer_calc": [], "stability_calc": [],
    }
    for n in node_map.values():
        cats[_classify_node(n)].append(n)

    lines: List[str] = ["graph TB", ""]

    # Node definitions
    for n in node_map.values():
        lines.append(_node_def(n))
    lines.append("")

    # Edges that touch only nodes in this subgraph
    lines.append("    %% Edges")
    for edge in graph.edges:
        if (edge.start.parameter in layer_node_names
                and edge.end.parameter in layer_node_names):
            lines.append(_edge_line(edge.start, edge.end, edge.method_name))
    lines.append("")

    lines.extend(_style_block(cats))
    return _mermaid_wrap(lines)


# ==============================================================================
# Diagram 3 — Slab stiffnesses (detail)
# ==============================================================================

def generate_mermaid_slab_detail(graph: Graph) -> str:
    """
    Generate a detail mermaid diagram for slab stiffness assembly.

    Shows layer parameters → slab merge nodes → A11 / B11 / D11 / A55
    with method names labeled on edges.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    slab_node_names = {
        "measured_layer_thickness",
        "density", "elastic_modulus", "poissons_ratio", "shear_modulus",
        "merge_E_nu", "merge_hi_G", "merge_hi_E_nu",
        "A11", "B11", "D11", "A55",
    }

    node_map = {n.parameter: n for n in graph.nodes
                if n.parameter in slab_node_names}

    cats: Dict[str, List[Node]] = {
        "root": [], "measured": [], "merge": [],
        "layer_calc": [], "slab_calc": [], "weak_layer_calc": [], "stability_calc": [],
    }
    for n in node_map.values():
        cats[_classify_node(n)].append(n)

    lines: List[str] = ["graph LR", ""]

    for n in node_map.values():
        lines.append(_node_def(n))
    lines.append("")

    lines.append("    %% Edges")
    for edge in graph.edges:
        if (edge.start.parameter in slab_node_names
                and edge.end.parameter in slab_node_names):
            lines.append(_edge_line(edge.start, edge.end, edge.method_name))
    lines.append("")

    lines.extend(_style_block(cats))
    return _mermaid_wrap(lines)


# ==============================================================================
# Diagram 4 — Weak-layer parameters & stability criteria (detail)
# ==============================================================================

def generate_mermaid_stability_detail(graph: Graph) -> str:
    """
    Generate a detail mermaid diagram for stability criterion inputs.

    Shows measured inputs → layer params → slab_elasticity_parameters,
    with the weak_layer_info* placeholder and the WEAC / Roch merge nodes
    leading to g_Δ and S_r outputs.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    stability_node_names = {
        "snow_pit",
        "measured_density", "measured_hand_hardness",
        "measured_grain_form", "measured_grain_size",
        "measured_layer_thickness",
        "density", "elastic_modulus", "poissons_ratio", "shear_modulus",
        "weak_layer_info*",
        "slab_elasticity_parameters",
        "merge_weac_inputs", "merge_roch_inputs",
        "g_delta", "s_r",
    }

    node_map = {n.parameter: n for n in graph.nodes
                if n.parameter in stability_node_names}

    cats: Dict[str, List[Node]] = {
        "root": [], "measured": [], "merge": [],
        "layer_calc": [], "slab_calc": [], "weak_layer_calc": [], "stability_calc": [],
    }
    for n in node_map.values():
        cats[_classify_node(n)].append(n)

    lines: List[str] = ["graph LR", ""]

    for n in node_map.values():
        lines.append(_node_def(n))
    lines.append("")

    lines.append("    %% Edges")
    for edge in graph.edges:
        if (edge.start.parameter in stability_node_names
                and edge.end.parameter in stability_node_names):
            lines.append(_edge_line(edge.start, edge.end, edge.method_name))
    lines.append("")

    lines.extend(_style_block(cats))
    return _mermaid_wrap(lines)


# ==============================================================================
# Full single-diagram (backwards-compatible)
# ==============================================================================

def generate_mermaid_diagram(graph: Graph, title: str = "Parameter Dependency Graph") -> str:
    """
    Generate a single mermaid diagram containing the full parameter graph.

    Kept for backwards compatibility. For publication use, prefer the
    focused generators: :func:`generate_mermaid_overview`,
    :func:`generate_mermaid_layer_detail`, etc.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.
    title : str, optional
        Title comment for the diagram.

    Returns
    -------
    str
        Mermaid diagram syntax as a string.
    """
    node_categories: Dict[str, List[Node]] = {
        "root": [], "measured": [], "merge": [],
        "layer_calc": [], "slab_calc": [], "weak_layer_calc": [], "stability_calc": [],
    }
    for node in graph.nodes:
        node_categories[_classify_node(node)].append(node)

    layer_merges = [n for n in node_categories["merge"]
                    if n.parameter in {
                        "merge_hand_hardness_grain_form",
                        "merge_hand_hardness_grain_form_grain_size",
                        "merge_density_grain_form",
                        "merge_elastic_modulus_poissons_ratio",
                    }]
    stability_merges = [n for n in node_categories["merge"]
                        if n.parameter in {"merge_weac_inputs", "merge_roch_inputs"}]
    slab_merges = [n for n in node_categories["merge"]
                   if n not in layer_merges and n not in stability_merges]

    lines: List[str] = ["```mermaid", "graph TB", ""]

    def _emit_group(comment: str, nodes: List[Node]) -> None:
        lines.append(f"    %% {comment}")
        for n in nodes:
            lines.append(_node_def(n))
        lines.append("    ")

    _emit_group("Root node", node_categories["root"])
    _emit_group("Measured parameter nodes", node_categories["measured"])
    _emit_group("Layer-level merge nodes", layer_merges)
    _emit_group("Calculated layer parameters", node_categories["layer_calc"])
    _emit_group("Slab-level merge nodes", slab_merges)
    _emit_group("Slab parameters", node_categories["slab_calc"])
    _emit_group("Weak-layer parameters", node_categories["weak_layer_calc"])
    _emit_group("Stability merge nodes", stability_merges)
    _emit_group("Stability model outputs", node_categories["stability_calc"])

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
    "weac_skier":             "WEAC",
    "roch_natural":           "Roch-n",
}

# Ordered subgraph definitions for the full-detail mermaid diagram.
# Each entry is (subgraph_id, display_title, [parameter_names]).
_FULL_SUBGRAPHS = [
    (
        "INPUTS",
        "Snow Pit Observations",
        [
            "snow_pit",
            "measured_density",
            "measured_hand_hardness",
            "measured_grain_form",
            "measured_grain_size",
            "measured_layer_thickness",
        ],
    ),
    (
        "LAYER_MERGES",
        "Layer Merge Nodes",
        [
            "merge_hand_hardness_grain_form",
            "merge_hand_hardness_grain_form_grain_size",
            "merge_density_grain_form",
            "merge_elastic_modulus_poissons_ratio",
        ],
    ),
    (
        "LAYER",
        "Layer Parameters",
        ["density", "elastic_modulus", "poissons_ratio", "shear_modulus"],
    ),
    (
        "SLAB_MERGES",
        "Slab Merge Nodes",
        ["merge_E_nu", "merge_hi_G", "merge_hi_E_nu"],
    ),
    (
        "SLAB",
        "Slab Stiffnesses",
        ["D11", "B11", "A11", "A55"],
    ),
    (
        "STABILITY_MERGES",
        "Stability Criterion Inputs",
        ["slab_elasticity_parameters", "weak_layer_info*"],
    ),
    (
        "STABILITY",
        "Stability Criteria",
        ["merge_weac_inputs", "merge_roch_inputs", "g_delta", "s_r"],
    ),
]


def generate_mermaid_full_detail(graph: Graph) -> str:
    """
    Generate a full-detail mermaid diagram of the entire parameter graph.

    All nodes — including merge nodes — are shown, grouped into subgraph
    blocks.  Method names are abbreviated on edges.  Greek symbols are used
    in node labels where appropriate.

    Parameters
    ----------
    graph : Graph
        The parameter dependency graph.

    Returns
    -------
    str
        Mermaid diagram syntax.
    """
    node_map = {n.parameter: n for n in graph.nodes}

    lines: List[str] = ["graph LR", ""]

    # Emit subgraph blocks
    for sg_id, sg_title, params in _FULL_SUBGRAPHS:
        lines.append(f'    subgraph {sg_id}["{sg_title}"]')
        for param in params:
            if param in node_map:
                lines.append("    " + _node_def(node_map[param]).lstrip())
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
    graph: Graph,
    filepath: str,
    title: str = "SnowPyt-MechParams — Overview",
) -> None:
    """Save the high-level overview mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_overview(graph))


def save_mermaid_layer_detail(
    graph: Graph,
    filepath: str,
    title: str = "SnowPyt-MechParams — Layer Parameters",
) -> None:
    """Save the layer-parameters detail mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_layer_detail(graph))


def save_mermaid_slab_detail(
    graph: Graph,
    filepath: str,
    title: str = "SnowPyt-MechParams — Slab Stiffnesses",
) -> None:
    """Save the slab stiffness detail mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_slab_detail(graph))


def save_mermaid_stability_detail(
    graph: Graph,
    filepath: str,
    title: str = "SnowPyt-MechParams — Stability Criteria Inputs",
) -> None:
    """Save the stability criterion inputs mermaid diagram to *filepath*."""
    _save(filepath, title, generate_mermaid_stability_detail(graph))


def save_mermaid_full_detail(
    graph: Graph,
    filepath: str,
    title: str = "SnowPyt-MechParams — Full Parameter Graph",
) -> None:
    """Save the full-detail mermaid diagram (all nodes + subgraphs) to *filepath*."""
    _save(filepath, title, generate_mermaid_full_detail(graph))


def save_mermaid_diagram(
    graph: Graph,
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


def print_mermaid_diagram(graph: Graph, title: str = "Parameter Dependency Graph") -> None:
    """Generate and print the full mermaid diagram to stdout."""
    print(generate_mermaid_diagram(graph, title=title))


# ==============================================================================
# CLI when run as script
# ==============================================================================

if __name__ == "__main__":
    import sys

    try:
        from snowpyt_mechparams.graph import graph
    except ImportError:
        print("Error: Could not import graph. Make sure the package is installed.")
        sys.exit(1)

    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        save_mermaid_diagram(graph, output_file, title="SnowPyt-MechParams Parameter Graph")
    else:
        print_mermaid_diagram(graph, title="SnowPyt-MechParams Parameter Graph")
