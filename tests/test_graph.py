"""
Tests for the parameter graph module.

This module tests the graph structure, node accessibility, and basic
graph properties for both layer-level and slab-level parameters.
"""

import pytest

from snowpyt_mechparams.graph import (
    graph,
    Graph,
    Node,
    GraphBuilder,
    # Root
    snow_pit,
    # Measured parameters
    measured_density,
    measured_hand_hardness,
    measured_grain_form,
    measured_grain_size,
    # Layer properties
    measured_layer_thickness,
    # Layer parameters
    density,
    elastic_modulus,
    poissons_ratio,
    shear_modulus,
    # Slab parameters
    A11,
    B11,
    D11,
    A55,
)


class TestGraphStructure:
    """Test basic graph structure and properties."""
    
    def test_graph_instance_exists(self):
        """Graph instance should be created."""
        assert graph is not None
        assert isinstance(graph, Graph)
    
    def test_graph_has_nodes(self):
        """Graph should have nodes."""
        assert len(graph.nodes) > 0
    
    def test_graph_has_edges(self):
        """Graph should have edges."""
        assert len(graph.edges) > 0
    
    def test_root_node_exists(self):
        """Snow pit root node should exist."""
        node = graph.get_node("snow_pit")
        assert node is not None
        assert node.parameter == "snow_pit"
        assert node.type == "parameter"


class TestLayerParameterNodes:
    """Test layer-level parameter nodes."""
    
    def test_measured_parameter_nodes_exist(self):
        """All measured parameter nodes should exist."""
        measured_params = [
            "measured_density",
            "measured_hand_hardness",
            "measured_grain_form",
            "measured_grain_size",
        ]
        for param in measured_params:
            node = graph.get_node(param)
            assert node is not None, f"Node {param} not found"
            assert node.type == "parameter"
    
    def test_layer_property_nodes_exist(self):
        """Layer property nodes should exist."""
        node = graph.get_node("measured_layer_thickness")
        assert node is not None
        assert node.type == "parameter"
        assert node.parameter == "measured_layer_thickness"
    
    def test_calculated_layer_parameter_nodes_exist(self):
        """All calculated layer parameter nodes should exist."""
        calc_params = [
            "density",
            "elastic_modulus",
            "poissons_ratio",
            "shear_modulus",
        ]
        for param in calc_params:
            node = graph.get_node(param)
            assert node is not None, f"Node {param} not found"
            assert node.type == "parameter"
    
    def test_density_has_incoming_edges(self):
        """Density node should have incoming edges (methods)."""
        node = graph.get_node("density")
        assert len(node.incoming_edges) > 0
        
        # Should have data flow from measured_density
        has_data_flow = any(
            edge.method_name is None and edge.start.parameter == "measured_density"
            for edge in node.incoming_edges
        )
        assert has_data_flow
        
        # Should have method edges
        method_edges = [
            edge for edge in node.incoming_edges 
            if edge.method_name is not None
        ]
        assert len(method_edges) >= 3  # geldsetzer, kim_jamieson_table2, kim_jamieson_table5


class TestSlabParameterNodes:
    """Test slab-level parameter nodes."""
    
    def test_slab_parameter_nodes_exist(self):
        """All slab parameter nodes should exist."""
        slab_params = ["A11", "B11", "D11", "A55"]
        for param in slab_params:
            node = graph.get_node(param)
            assert node is not None, f"Node {param} not found"
            assert node.type == "parameter"
    
    def test_slab_parameters_have_incoming_edges(self):
        """Slab parameters should have incoming method edges."""
        slab_params = ["A11", "B11", "D11", "A55"]
        for param in slab_params:
            node = graph.get_node(param)
            assert len(node.incoming_edges) > 0, f"{param} has no incoming edges"
            
            # Should have at least one method edge
            method_edges = [
                edge for edge in node.incoming_edges
                if edge.method_name is not None
            ]
            assert len(method_edges) > 0, f"{param} has no method edges"
    
    def test_D11_uses_weissgraeber_rosendahl(self):
        """D11 should use weissgraeber_rosendahl method."""
        node = graph.get_node("D11")
        methods = [
            edge.method_name for edge in node.incoming_edges
            if edge.method_name is not None
        ]
        assert "weissgraeber_rosendahl" in methods
    
    def test_all_slab_params_use_weissgraeber_rosendahl(self):
        """All slab parameters should use weissgraeber_rosendahl method."""
        slab_params = ["A11", "B11", "D11", "A55"]
        for param in slab_params:
            node = graph.get_node(param)
            methods = [
                edge.method_name for edge in node.incoming_edges
                if edge.method_name is not None
            ]
            assert "weissgraeber_rosendahl" in methods, \
                f"{param} does not have weissgraeber_rosendahl method"


class TestMergeNodes:
    """Test merge node structure."""
    
    def test_layer_level_merge_nodes_exist(self):
        """Layer-level merge nodes should exist."""
        merge_nodes = [
            "merge_hand_hardness_grain_form",
            "merge_hand_hardness_grain_form_grain_size",
            "merge_density_grain_form",
        ]
        for merge in merge_nodes:
            node = graph.get_node(merge)
            assert node is not None, f"Merge node {merge} not found"
            assert node.type == "merge"
    
    def test_slab_level_merge_nodes_exist(self):
        """Slab-level merge nodes should exist."""
        merge_nodes = [
            "zi",
            "merge_E_nu",
            "merge_zi_E_nu",
            "merge_hi_G",
            "merge_hi_E_nu",
        ]
        for merge in merge_nodes:
            node = graph.get_node(merge)
            assert node is not None, f"Merge node {merge} not found"
            assert node.type == "merge"
    
    def test_merge_E_nu_has_correct_inputs(self):
        """merge_E_nu should combine elastic_modulus and poissons_ratio."""
        node = graph.get_node("merge_E_nu")
        assert node is not None
        
        # Check incoming edges
        input_params = {edge.start.parameter for edge in node.incoming_edges}
        assert "elastic_modulus" in input_params
        assert "poissons_ratio" in input_params
    
    def test_merge_zi_E_nu_has_correct_inputs(self):
        """merge_zi_E_nu should combine zi and merge_E_nu."""
        node = graph.get_node("merge_zi_E_nu")
        assert node is not None
        
        # Check incoming edges
        input_params = {edge.start.parameter for edge in node.incoming_edges}
        assert "zi" in input_params
        assert "merge_E_nu" in input_params
    
    def test_merge_hi_G_has_correct_inputs(self):
        """merge_hi_G should combine measured_layer_thickness and shear_modulus."""
        node = graph.get_node("merge_hi_G")
        assert node is not None
        
        # Check incoming edges
        input_params = {edge.start.parameter for edge in node.incoming_edges}
        assert "measured_layer_thickness" in input_params
        assert "shear_modulus" in input_params
    
    def test_merge_hi_E_nu_has_correct_inputs(self):
        """merge_hi_E_nu should combine measured_layer_thickness and merge_E_nu."""
        node = graph.get_node("merge_hi_E_nu")
        assert node is not None
        
        # Check incoming edges
        input_params = {edge.start.parameter for edge in node.incoming_edges}
        assert "measured_layer_thickness" in input_params
        assert "merge_E_nu" in input_params


class TestExportedNodes:
    """Test that exported nodes match graph nodes."""
    
    def test_exported_snow_pit_matches_graph(self):
        """Exported snow_pit node should match graph node."""
        node = graph.get_node("snow_pit")
        assert snow_pit is node
    
    def test_exported_density_matches_graph(self):
        """Exported density node should match graph node."""
        node = graph.get_node("density")
        assert density is node
    
    def test_exported_D11_matches_graph(self):
        """Exported D11 node should match graph node."""
        node = graph.get_node("D11")
        assert D11 is node
    
    def test_all_slab_params_exported(self):
        """All slab parameter nodes should be exported."""
        assert A11 is graph.get_node("A11")
        assert B11 is graph.get_node("B11")
        assert D11 is graph.get_node("D11")
        assert A55 is graph.get_node("A55")


class TestGraphBuilder:
    """Test GraphBuilder functionality."""
    
    def test_can_create_simple_graph(self):
        """Should be able to create a simple graph with builder."""
        builder = GraphBuilder()
        node1 = builder.param("param1")
        node2 = builder.param("param2")
        builder.flow(node1, node2)
        
        g = builder.build()
        
        assert len(g.nodes) == 2
        assert len(g.edges) == 1
        assert g.get_node("param1") is not None
        assert g.get_node("param2") is not None
    
    def test_can_create_merge_nodes(self):
        """Should be able to create merge nodes."""
        builder = GraphBuilder()
        merge = builder.merge("test_merge")
        
        assert merge.type == "merge"
        assert merge.parameter == "test_merge"
    
    def test_can_create_method_edges(self):
        """Should be able to create method edges."""
        builder = GraphBuilder()
        node1 = builder.param("input")
        node2 = builder.param("output")
        edge = builder.method_edge(node1, node2, "test_method")
        
        assert edge.method_name == "test_method"
        assert edge.start is node1
        assert edge.end is node2


class TestGraphDispatcherConsistency:
    """Verify every method edge in the graph has a matching dispatcher registration."""

    def test_all_graph_method_edges_have_dispatcher_entries(self):
        """Every method_edge in definitions.py must map to a MethodDispatcher key.

        This catches typos in method names that would silently create broken
        graph edges (the pathway would be discovered but execution would fail
        at dispatch time).
        """
        from snowpyt_mechparams.execution.dispatcher import MethodDispatcher

        dispatcher = MethodDispatcher()
        registered_keys = set(dispatcher._registry.keys())

        # Collect all (parameter, method_name) pairs from the graph's method edges
        missing = []
        for edge in graph.edges:
            if edge.method_name is not None:
                key = (edge.end.parameter, edge.method_name)
                if key not in registered_keys:
                    missing.append(key)

        assert missing == [], (
            f"Graph method edges without dispatcher registration: {missing}. "
            "Either register the method in MethodDispatcher._register_all_methods() "
            "or fix the method name in graph/definitions.py."
        )

    def test_all_dispatcher_entries_have_graph_edges(self):
        """Every dispatcher registration should correspond to at least one graph edge.

        This catches stale dispatcher entries for methods that were removed from
        the graph.
        """
        from snowpyt_mechparams.execution.dispatcher import MethodDispatcher

        dispatcher = MethodDispatcher()
        registered_keys = set(dispatcher._registry.keys())

        # Collect all (parameter, method_name) from graph edges
        graph_keys = set()
        for edge in graph.edges:
            if edge.method_name is not None:
                graph_keys.add((edge.end.parameter, edge.method_name))

        # data_flow is registered in the dispatcher but not a method_edge in the graph
        # (it's a flow edge, i.e., method_name is None). Exclude it.
        stale = registered_keys - graph_keys - {("density", "data_flow")}

        assert stale == set(), (
            f"Dispatcher registrations without corresponding graph edges: {stale}. "
            "Either add the edge to graph/definitions.py or remove the "
            "stale dispatcher registration."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
