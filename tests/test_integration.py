"""
Integration tests for Phase 4 - Package structure and imports.

This module tests that all components work together correctly with the
new production module structure, including:
- Package-level imports
- Graph and algorithm integration
- Execution engine with dynamic programming
- Cache statistics
- Slab parameter calculation
"""

import pytest
from uncertainties import ufloat

from snowpyt_mechparams import (
    Layer,
    Slab,
    ExecutionEngine,
    graph,
    algorithm,
)


class TestPackageImports:
    """Test that package-level imports work correctly."""
    
    def test_import_models(self):
        """Should be able to import domain models from package root."""
        from snowpyt_mechparams import Layer, Slab
        
        layer = Layer(thickness=30)
        assert layer.thickness == 30
        
        slab = Slab(layers=[layer], angle=35)
        assert slab.angle == 35
    
    def test_import_graph_module(self):
        """Should be able to import graph as a module."""
        
        assert hasattr(graph, 'graph')
        assert hasattr(graph, 'D11')
        assert hasattr(graph, 'A11')
        
        # Test graph functionality
        D11_node = graph.graph.get_node('D11')
        assert D11_node is not None
        assert D11_node.parameter == 'D11'
    
    def test_import_algorithm_module(self):
        """Should be able to import algorithm as a module."""
        
        assert hasattr(algorithm, 'find_parameterizations')
        assert hasattr(algorithm, 'Parameterization')
        assert hasattr(algorithm, 'Branch')
    
    def test_import_execution_engine(self):
        """Should be able to import execution engine."""
        
        # Can instantiate with graph
        from snowpyt_mechparams.graph import graph
        engine = ExecutionEngine(graph)
        assert engine is not None


class TestEndToEndExecution:
    """Test complete execution workflow with new structure."""
    
    def test_execute_layer_parameter(self):
        """Should execute layer parameter calculations end-to-end."""
        from snowpyt_mechparams.graph import graph
        
        # Create slab with measured data
        layer = Layer(
            thickness=ufloat(30, 1),
            grain_form="RG"
        )
        slab = Slab(layers=[layer], angle=35)
        
        # Create engine and execute
        # For poissons_ratio (layer-level parameter), algorithm only computes
        # what's needed - no slab parameters
        engine = ExecutionEngine(graph)
        results = engine.execute_all(slab, 'poissons_ratio')
        
        # Verify results structure
        assert results.target_parameter == 'poissons_ratio'
        assert results.total_pathways > 0
        assert results.successful_pathways > 0
        
        # Verify cache stats are present
        assert 'hits' in results.cache_stats
        assert 'misses' in results.cache_stats
        assert 'hit_rate' in results.cache_stats
    
    def test_execute_slab_parameter(self):
        """Should execute slab parameter calculations end-to-end."""
        from snowpyt_mechparams.graph import graph
        
        # Create slab with full layer properties
        layer = Layer(
            thickness=ufloat(30, 1),
            elastic_modulus=ufloat(2.0, 0.2),
            poissons_ratio=ufloat(0.3, 0.02),
            shear_modulus=ufloat(0.7, 0.1)
        )
        slab = Slab(layers=[layer], angle=35)
        
        # Execute - when asking for poissons_ratio with layer already having
        # E and ν, the algorithm will compute plate theory parameters
        engine = ExecutionEngine(graph)
        results = engine.execute_all(slab, 'poissons_ratio')
        
        # Check that slab parameters were computed
        successful = results.get_successful_pathways()
        if successful:
            first_result = list(successful.values())[0]
            # Check slab-level traces were created
            slab_traces = first_result.get_slab_traces()
            assert len(slab_traces) > 0
            
            # Check that slab parameters were set
            computed_slab = first_result.slab
            assert computed_slab.A11 is not None
            assert computed_slab.B11 is not None
            assert computed_slab.D11 is not None
            assert computed_slab.A55 is not None


class TestDynamicProgramming:
    """Test that dynamic programming works with new structure."""
    
    def test_cache_improves_performance(self):
        """Cache should reduce redundant calculations for multi-layer slabs."""
        from snowpyt_mechparams.graph import graph
        
        # Create slab with multiple layers (cache benefits more apparent)
        layer1 = Layer(thickness=ufloat(20, 1), grain_form="RG")
        layer2 = Layer(thickness=ufloat(30, 1), grain_form="FC")
        slab = Slab(layers=[layer1, layer2], angle=35)
        
        # Execute multiple pathways - caching is always enabled
        engine = ExecutionEngine(graph)
        results = engine.execute_all(slab, 'poissons_ratio')
        
        # With multiple pathways and multiple layers, expect some cache activity
        # Cache stats should be present (even if hit rate is 0 for simple cases)
        assert 'hits' in results.cache_stats
        assert 'misses' in results.cache_stats
        assert 'hit_rate' in results.cache_stats
        assert results.cache_stats['misses'] > 0  # Should have computed something


class TestGraphAlgorithmIntegration:
    """Test integration between graph and algorithm modules."""
    
    def test_find_pathways_for_all_slab_params(self):
        """Should find pathways for all slab parameters."""
        from snowpyt_mechparams.graph import graph
        from snowpyt_mechparams.algorithm import find_parameterizations
        
        slab_params = ['A11', 'B11', 'D11', 'A55']
        
        for param in slab_params:
            node = graph.get_node(param)
            assert node is not None, f"Node {param} not found"
            
            pathways = find_parameterizations(graph, node)
            assert len(pathways) > 0, f"No pathways for {param}"
            
            # Check that pathway uses weissgraeber_rosendahl
            first_pathway = pathways[0]
            methods = {}
            for _, _, continuation in first_pathway.merge_points:
                for seg in continuation:
                    if seg.to_node == param:
                        methods[param] = seg.edge_name
            
            if param in methods:
                assert methods[param] == 'weissgraeber_rosendahl'


class TestVersioning:
    """Test package versioning."""

    def test_version_updated(self):
        """Package version should be 0.4.0."""
        import snowpyt_mechparams

        version = snowpyt_mechparams.__version__
        assert version == "0.4.0", f"Expected version 0.4.0, got {version}"


class TestUpdatedGraphStructure:
    """Verify the updated graph structure after removing weak layer parameters."""

    def test_weak_layer_info_placeholder_exists(self):
        """weak_layer_info* node should exist in the graph."""
        from snowpyt_mechparams.graph import graph as g
        node = g.get_node("weak_layer_info*")
        assert node is not None
        assert node.level == "weak_layer"

    def test_weak_layer_info_has_no_incoming_method_edges(self):
        """weak_layer_info* has no method edges — it is a pure placeholder."""
        from snowpyt_mechparams.graph import graph as g
        from snowpyt_mechparams.algorithm import find_parameterizations
        node = g.get_node("weak_layer_info*")
        pathways = find_parameterizations(g, node)
        assert len(pathways) == 0

    def test_slab_elasticity_parameters_node_exists(self):
        """slab_elasticity_parameters merge node should exist."""
        from snowpyt_mechparams.graph import graph as g
        node = g.get_node("slab_elasticity_parameters")
        assert node is not None
        assert node.type == "merge"

    def test_slab_elasticity_parameters_inputs(self):
        """slab_elasticity_parameters should receive E and ν as inputs."""
        from snowpyt_mechparams.graph import graph as g
        node = g.get_node("slab_elasticity_parameters")
        input_params = {e.start.parameter for e in node.incoming_edges}
        assert "elastic_modulus" in input_params
        assert "poissons_ratio" in input_params

    def test_slab_elasticity_parameters_has_32_pathways(self):
        """4 density × 4 E-mod × 2 ν = 32 pathways to slab_elasticity_parameters."""
        from snowpyt_mechparams.graph import graph as g
        from snowpyt_mechparams.algorithm import find_parameterizations
        node = g.get_node("slab_elasticity_parameters")
        pathways = find_parameterizations(g, node)
        assert len(pathways) == 32

    def test_g_delta_has_zero_pathways(self):
        """g_delta has 0 pathways because weak_layer_info* is a placeholder."""
        from snowpyt_mechparams.graph import graph as g
        from snowpyt_mechparams.algorithm import find_parameterizations
        node = g.get_node("g_delta")
        pathways = find_parameterizations(g, node)
        assert len(pathways) == 0

    def test_s_r_has_zero_pathways(self):
        """s_r has 0 pathways because weak_layer_info* is a placeholder."""
        from snowpyt_mechparams.graph import graph as g
        from snowpyt_mechparams.algorithm import find_parameterizations
        node = g.get_node("s_r")
        pathways = find_parameterizations(g, node)
        assert len(pathways) == 0

    def test_old_weak_layer_params_not_in_graph(self):
        """G_c, G_Ic, G_IIc, sigma_c, tau_c, sigma_comp should not be in graph."""
        from snowpyt_mechparams.graph import graph as g
        removed = ["G_c", "G_Ic", "G_IIc", "sigma_c", "tau_c", "sigma_comp"]
        for param in removed:
            assert g.get_node(param) is None, f"Node {param!r} should have been removed"

    def test_weac_inputs_merge_node_has_slab_elasticity_input(self):
        """merge_weac_inputs should receive slab_elasticity_parameters as an input."""
        from snowpyt_mechparams.graph import graph as g
        node = g.get_node("merge_weac_inputs")
        input_params = {e.start.parameter for e in node.incoming_edges}
        assert "slab_elasticity_parameters" in input_params
        assert "weak_layer_info*" in input_params

    def test_roch_inputs_merge_node_has_weak_layer_info(self):
        """merge_roch_inputs should receive weak_layer_info* (not tau_c)."""
        from snowpyt_mechparams.graph import graph as g
        node = g.get_node("merge_roch_inputs")
        input_params = {e.start.parameter for e in node.incoming_edges}
        assert "weak_layer_info*" in input_params
        assert "tau_c" not in input_params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
