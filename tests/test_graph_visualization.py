"""
Tests for graph visualization functionality.
"""

import pytest
from snowpyt_mechparams.graph.structures import GraphBuilder, Node
from snowpyt_mechparams.graph.visualize import (
    generate_mermaid_diagram,
    generate_mermaid_full_detail,
    generate_mermaid_stability_detail,
    _classify_node,
    _sanitize_node_id,
    _get_node_label,
    _get_node_shape,
)


def test_classify_node_root():
    """Test classification of root node."""
    node = Node(type="parameter", parameter="snow_pit")
    assert _classify_node(node) == "root"


def test_classify_node_measured():
    """Test classification of measured nodes."""
    assert _classify_node(Node(type="parameter", parameter="measured_density")) == "measured"
    assert _classify_node(Node(type="parameter", parameter="measured_hand_hardness")) == "measured"
    assert _classify_node(Node(type="parameter", parameter="measured_layer_thickness")) == "measured"


def test_classify_node_merge():
    """Test classification of merge nodes."""
    node = Node(type="merge", parameter="merge_density_grain_form")
    assert _classify_node(node) == "merge"


def test_classify_node_layer_calc():
    """Test classification of layer calculated parameters (level='layer')."""
    assert _classify_node(Node(type="parameter", parameter="density", level="layer")) == "layer_calc"
    assert _classify_node(Node(type="parameter", parameter="elastic_modulus", level="layer")) == "layer_calc"
    assert _classify_node(Node(type="parameter", parameter="poissons_ratio", level="layer")) == "layer_calc"
    assert _classify_node(Node(type="parameter", parameter="shear_modulus", level="layer")) == "layer_calc"


def test_classify_node_slab_calc():
    """Test classification of slab calculated parameters (level='slab')."""
    assert _classify_node(Node(type="parameter", parameter="D11", level="slab")) == "slab_calc"
    assert _classify_node(Node(type="parameter", parameter="A11", level="slab")) == "slab_calc"
    assert _classify_node(Node(type="parameter", parameter="B11", level="slab")) == "slab_calc"
    assert _classify_node(Node(type="parameter", parameter="A55", level="slab")) == "slab_calc"


def test_sanitize_node_id():
    """Test node ID sanitization."""
    assert _sanitize_node_id("snow_pit") == "snow_pit"
    assert _sanitize_node_id("measured_density") == "measured_density"
    assert _sanitize_node_id("merge-density-form") == "merge_density_form"


def test_get_node_shape():
    """Test node shape generation."""
    param_node = Node(type="parameter", parameter="density")
    merge_node = Node(type="merge", parameter="merge_density_grain_form")
    
    assert _get_node_shape(param_node) == ("[", "]")
    assert _get_node_shape(merge_node) == ("{", "}")


def test_get_node_label():
    """Test node label generation returns non-empty strings for known nodes."""
    # Labels no longer include category tags (color conveys node type instead)
    assert _get_node_label(Node(type="parameter", parameter="snow_pit")) != ""
    assert "density" in _get_node_label(Node(type="parameter", parameter="measured_density")).lower()
    assert _get_node_label(Node(type="parameter", parameter="density")) != ""
    assert "D11" in _get_node_label(Node(type="parameter", parameter="D11"))


def test_generate_mermaid_simple_graph():
    """Test mermaid diagram generation for a simple graph."""
    builder = GraphBuilder()
    
    # Create simple graph
    snow_pit = builder.param("snow_pit")
    density = builder.param("density")
    builder.flow(snow_pit, density)
    
    graph = builder.build()
    
    # Generate diagram
    diagram = generate_mermaid_diagram(graph)
    
    # Verify basic structure
    assert "```mermaid" in diagram
    assert "graph TB" in diagram
    assert "snow_pit" in diagram
    assert "density" in diagram
    assert "```" in diagram.split("```mermaid")[1]  # Closing backticks exist


def test_generate_mermaid_with_method():
    """Test mermaid diagram generation with method edges."""
    builder = GraphBuilder()
    
    # Create graph with method
    density = builder.param("density")
    grain_form = builder.param("measured_grain_form")
    merge = builder.merge("merge_density_grain_form")
    elastic = builder.param("elastic_modulus")
    
    builder.flow(density, merge)
    builder.flow(grain_form, merge)
    builder.method_edge(merge, elastic, "bergfeld")
    
    graph = builder.build()
    
    # Generate diagram
    diagram = generate_mermaid_diagram(graph)
    
    # Verify method is labeled
    assert "bergfeld" in diagram
    assert "|bergfeld|" in diagram


def test_generate_mermaid_has_styling():
    """Test that generated diagram includes styling."""
    builder = GraphBuilder()
    
    snow_pit = builder.param("snow_pit")
    density = builder.param("density")
    builder.flow(snow_pit, density)
    
    graph = builder.build()
    diagram = generate_mermaid_diagram(graph)
    
    # Check for styling section
    assert "classDef" in diagram
    assert "rootNode" in diagram
    assert "class snow_pit rootNode" in diagram


def test_classify_node_weak_layer_calc():
    """Test classification of weak-layer placeholder nodes."""
    assert _classify_node(Node(type="parameter", parameter="weak_layer_info*", level="weak_layer")) == "weak_layer_calc"


def test_classify_node_stability_calc():
    """Test classification of stability model output nodes."""
    assert _classify_node(Node(type="parameter", parameter="g_delta", level="stability_model")) == "stability_calc"
    assert _classify_node(Node(type="parameter", parameter="s_r", level="stability_model")) == "stability_calc"


def test_generate_mermaid_complete_graph():
    """Test mermaid generation with the actual parameter graph."""
    # Import the real graph
    from snowpyt_mechparams.graph import graph
    
    # Generate diagram
    diagram = generate_mermaid_diagram(graph)
    
    # Verify key nodes are present
    assert "snow_pit" in diagram
    assert "density" in diagram
    assert "elastic_modulus" in diagram
    assert "D11" in diagram
    assert "A11" in diagram
    
    # Verify key methods are present
    assert "bergfeld" in diagram
    assert "kochle" in diagram
    assert "weissgraeber_rosendahl" in diagram
    
    # Verify structure
    assert "```mermaid" in diagram
    assert "graph TB" in diagram
    assert "classDef" in diagram


def test_generate_mermaid_stability_detail_uses_slab_weight_graph():
    """Slab-weight detail should reflect the canonical graph, not old criteria."""
    diagram = generate_mermaid_stability_detail()

    assert "slab_weight_shear_with_elasticity" in diagram
    assert "merge_slab_weight_shear_elasticity" in diagram
    assert "measured_slope_angle" in diagram
    assert "merge_weac_inputs" not in diagram
    assert "merge_roch_inputs" not in diagram
    assert "weak_layer_info" not in diagram


def test_generate_mermaid_full_detail_groups_slab_weight_branch():
    """Full detail should derive readable slab-weight groups from the graph."""
    diagram = generate_mermaid_full_detail()

    assert 'subgraph WEIGHT_MERGES["Slab Weight Merge Nodes"]' in diagram
    assert 'subgraph WEIGHT["Slab Weight Pathways"]' in diagram
    assert "slab_weight_shear" in diagram
    assert "merge_slab_weight_slope_angle" in diagram


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
