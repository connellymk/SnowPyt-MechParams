"""
Tests for executor dynamic programming enhancements.

This module tests the enhanced PathwayExecutor with:
- Persistent caching across pathways
- Cache statistics tracking
- Layer property handling (thickness)
- Slab parameter execution with prerequisite checks
"""

import pytest
from uncertainties import ufloat

from snowpyt_mechparams.data_structures import Layer, Slab
from snowpyt_mechparams.execution.executor import PathwayExecutor
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher
from snowpyt_mechparams.graph import graph
from snowpyt_mechparams.algorithm import find_parameterizations


class TestCacheManagement:
    """Test cache management and statistics."""
    
    def test_cache_starts_empty(self):
        """Cache should start empty."""
        executor = PathwayExecutor()
        stats = executor.get_cache_stats()
        
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0
    
    def test_clear_cache(self):
        """clear_cache should reset all caches and statistics."""
        executor = PathwayExecutor()
        
        # Simulate some cache activity using the cache API
        executor.cache.set_layer_param(0, "density", "geldsetzer", ufloat(250, 10))
        executor.cache._stats.hits = 10
        executor.cache._stats.misses = 5
        
        # Verify cache has data
        stats_before = executor.get_cache_stats()
        assert stats_before['hits'] == 10
        assert stats_before['misses'] == 5
        
        # Clear cache
        executor.clear_cache()
        
        # Verify everything is reset
        stats_after = executor.get_cache_stats()
        assert stats_after['hits'] == 0
        assert stats_after['misses'] == 0
        # hit_rate should be 0.0 when there are no hits or misses
        assert stats_after['hit_rate'] == 0.0


class TestLayerPropertyHandling:
    """Test handling of layer properties (thickness)."""
    
    def test_layer_thickness_direct_flow(self):
        """Layer thickness should be direct data flow (no calculation)."""
        executor = PathwayExecutor()
        layer = Layer(thickness=ufloat(30, 1))
        
        # Get thickness via the cache-aware method
        value, was_cached, error_msg = executor._get_or_compute_layer_param(
            layer=layer,
            layer_index=0,
            parameter="measured_layer_thickness",
            method="data_flow"
        )
        
        # Should return the thickness directly
        assert value == layer.thickness
        assert was_cached == False  # No caching for direct properties
        assert error_msg is None  # No error for direct properties


class TestDynamicProgramming:
    """Test dynamic programming across pathways."""

    def test_density_cache_persists_across_calls(self):
        """
        Density cache should persist across execute_parameterization calls.

        Only density is cached. When the same density pathway is executed
        twice for the same slab, the second call should be a cache hit.
        """
        executor = PathwayExecutor()

        layer = Layer(
            thickness=ufloat(30, 1),
            grain_form="RG",
            hand_hardness="1F"
        )
        slab = Slab(layers=[layer], angle=35)

        # Get the geldsetzer density pathway
        density_node = graph.get_node("density")
        pathways = find_parameterizations(graph, density_node)
        geldsetzer_pathway = [p for p in pathways if 'geldsetzer' in str(p)][0]

        from snowpyt_mechparams.execution.config import ExecutionConfig
        config = ExecutionConfig(verbose=False)

        # Execute first time - should compute (cache miss)
        result1 = executor.execute_parameterization(
            parameterization=geldsetzer_pathway,
            slab=slab,
            target_parameter="density",
            config=config
        )

        # First execution: all misses, no hits
        stats1 = executor.get_cache_stats()
        assert stats1['misses'] > 0
        assert stats1['hits'] == 0

        # Execute second time (same pathway, same slab) - density should be a cache hit
        result2 = executor.execute_parameterization(
            parameterization=geldsetzer_pathway,
            slab=slab,
            target_parameter="density",
            config=config
        )

        # Second execution: should have density cache hits
        stats2 = executor.get_cache_stats()
        assert stats2['hits'] > stats1['hits'], "Second run should have density cache hits"
        assert stats2['hit_rate'] > 0.0

    def test_downstream_params_never_cached(self):
        """
        elastic_modulus, poissons_ratio, and shear_modulus must never be cached.

        These parameters depend on which density method was used upstream.
        Caching them would return wrong values for pathways that use a
        different density method. They must always be computed fresh.
        """
        executor = PathwayExecutor()

        layer = Layer(
            thickness=ufloat(30, 1),
            grain_form="RG",
            hand_hardness="1F"
        )
        slab = Slab(layers=[layer], angle=35)

        # Execute a kochle poissons_ratio pathway (grain_form only, no density needed)
        nu_node = graph.get_node("poissons_ratio")
        pathways = find_parameterizations(graph, nu_node)
        kochle_pathway = [p for p in pathways if 'kochle' in str(p)][0]

        from snowpyt_mechparams.execution.config import ExecutionConfig
        config = ExecutionConfig(verbose=False)

        result1 = executor.execute_parameterization(
            parameterization=kochle_pathway,
            slab=slab,
            target_parameter="poissons_ratio",
            config=config
        )

        # First run: zero hits (poissons_ratio is never cached)
        stats1 = executor.get_cache_stats()
        assert stats1['hits'] == 0, "Downstream params should never be cached"

        # Execute second time
        result2 = executor.execute_parameterization(
            parameterization=kochle_pathway,
            slab=slab,
            target_parameter="poissons_ratio",
            config=config
        )

        # Still zero hits - poissons_ratio results are never stored in the cache
        stats2 = executor.get_cache_stats()
        assert stats2['hits'] == 0, "Downstream params must remain uncached on second run"


class TestSlabParameterExecution:
    """Test slab parameter execution with prerequisites."""
    
    def test_slab_params_computed_when_prerequisites_met(self):
        """Slab parameters should be computed when prerequisites are met."""
        executor = PathwayExecutor()
        
        # Create a slab with all necessary layer properties
        layer1 = Layer(
            thickness=ufloat(20, 1),
            elastic_modulus=ufloat(1.5, 0.2),
            poissons_ratio=ufloat(0.3, 0.02),
            shear_modulus=ufloat(0.5, 0.1)
        )
        layer2 = Layer(
            thickness=ufloat(30, 1),
            elastic_modulus=ufloat(2.0, 0.3),
            poissons_ratio=ufloat(0.3, 0.02),
            shear_modulus=ufloat(0.7, 0.1)
        )
        slab = Slab(layers=[layer1, layer2], angle=35)
        
        # Execute slab calculations — one call per target parameter
        slab_traces = []
        for param in ("A11", "B11", "D11", "A55"):
            slab_traces.extend(executor._execute_slab_calculations(slab, param))
        
        # Should have one trace per slab parameter
        assert len(slab_traces) == 4
        
        # All should be successful
        for trace in slab_traces:
            assert trace.success, f"{trace.parameter} failed"
            assert trace.output is not None, f"{trace.parameter} has no output"
        
        # Check that slab object was updated
        assert slab.A11 is not None
        assert slab.B11 is not None
        assert slab.D11 is not None
        assert slab.A55 is not None
    
    def test_slab_params_fail_when_prerequisites_missing(self):
        """Slab parameters should fail gracefully when prerequisites missing."""
        executor = PathwayExecutor()
        
        # Create a slab with missing properties
        layer = Layer(
            thickness=ufloat(30, 1),
            # Missing elastic_modulus, poissons_ratio, shear_modulus
        )
        slab = Slab(layers=[layer], angle=35)
        
        # Execute slab calculations — one call per target parameter
        slab_traces = []
        for param in ("A11", "B11", "D11", "A55"):
            slab_traces.extend(executor._execute_slab_calculations(slab, param))
        
        # Should have one trace per slab parameter
        assert len(slab_traces) == 4
        
        # All should have failed due to missing prerequisites
        for trace in slab_traces:
            assert not trace.success, f"{trace.parameter} should have failed"
            assert trace.output is None, f"{trace.parameter} should have no output"
            assert trace.error is not None, f"{trace.parameter} should have error message"
        
        # Check that error messages mention prerequisites
        a11_trace = [t for t in slab_traces if t.parameter == "A11"][0]
        assert not a11_trace.success
        assert "prerequisite" in a11_trace.error.lower() or "missing" in a11_trace.error.lower()


class TestSlabCaching:
    """Test slab-level parameter caching behavior."""

    def test_slab_params_never_cached(self):
        """
        Slab parameters must NOT be cached across calls.

        D11, A11, B11, and A55 are computed from the pathway-specific layer
        values (elastic_modulus, poissons_ratio, shear_modulus) that are set
        on the working slab copy. Different pathways set different E/ν/G
        values, so a cached result from one pathway would be wrong for any
        other pathway on the same slab.

        ``_get_or_compute_slab_param`` must always recompute and always return
        ``was_cached=False``.
        """
        executor = PathwayExecutor()

        # Create a slab with all necessary properties
        layer = Layer(
            thickness=ufloat(30, 1),
            elastic_modulus=ufloat(2.0, 0.2),
            poissons_ratio=ufloat(0.3, 0.02),
            shear_modulus=ufloat(0.7, 0.1)
        )
        slab = Slab(layers=[layer], angle=35)

        # First call - should compute (not cached)
        value1, cached1, error1 = executor._get_or_compute_slab_param(
            slab, "D11", "weissgraeber_rosendahl"
        )

        assert value1 is not None
        assert cached1 == False  # Always computed fresh
        assert error1 is None

        # Second call with identical inputs - must ALSO compute fresh (not cached)
        value2, cached2, error2 = executor._get_or_compute_slab_param(
            slab, "D11", "weissgraeber_rosendahl"
        )

        assert value2 is not None
        assert cached2 == False  # Still not cached - slab params are never cached
        assert error2 is None
        # Values are equal because the inputs (layer E/ν/thickness) are the same,
        # not because of caching
        assert value1.nominal_value == value2.nominal_value


class TestErrorMessagePreservation:
    """Test that error messages from dispatcher are preserved in computation traces."""
    
    def test_layer_param_error_message_preserved(self):
        """Error messages from failed layer computations should be preserved."""
        from snowpyt_mechparams.execution.config import ExecutionConfig
        
        executor = PathwayExecutor()
        
        # Create a layer missing required data for elastic_modulus calculation
        # (elastic_modulus needs density, which requires either measured density or hand_hardness)
        layer = Layer(
            depth_top=0,
            thickness=ufloat(30, 1),
            grain_form="RG",
            # Missing: density_measured and hand_hardness
            # This will cause density calculation to fail, which cascades to E
        )
        
        slab = Slab(layers=[layer], angle=35.0)
        
        # Execute a parameterization that calculates elastic_modulus
        # This requires density first, which will fail
        E_node = graph.get_node("elastic_modulus")
        pathways = find_parameterizations(graph, E_node)
        
        # Use first pathway (any will do)
        config = ExecutionConfig(verbose=False)
        result = executor.execute_parameterization(
            parameterization=pathways[0],
            slab=slab,
            target_parameter="elastic_modulus",
            config=config
        )
        
        # Find failed computation traces
        failed_traces = [t for t in result.computation_trace if not t.success]
        assert len(failed_traces) > 0, "Should have at least one failed computation"
        
        # Check that failed traces have specific error messages, not generic ones
        for trace in failed_traces:
            if trace.error is not None:
                # Error should not be the generic "Computation failed" message
                # It should be a specific error from the dispatcher
                assert trace.error != "Computation failed" or trace.cached, \
                    f"Failed trace for {trace.parameter} should have specific error or be cached: {trace.error}"
    
    def test_slab_param_error_message_preserved(self):
        """Error messages from failed slab computations should be preserved."""
        from snowpyt_mechparams.execution.config import ExecutionConfig
        
        executor = PathwayExecutor()
        
        # Create a layer with density and grain form but no elastic modulus or poisson's ratio
        # This will cause slab parameter calculation to fail with a specific error
        layer = Layer(
            depth_top=0,
            thickness=ufloat(30, 1),
            grain_form="RG",
            hand_hardness="1F",
            density_measured=ufloat(200, 15)
        )
        
        slab = Slab(layers=[layer], angle=35.0)
        
        # Execute density calculation first
        density_node = graph.get_node("density")
        pathways = find_parameterizations(graph, density_node)
        
        config = ExecutionConfig(verbose=False)
        density_result = executor.execute_parameterization(
            parameterization=pathways[0],
            slab=slab,
            target_parameter="density",
            config=config
        )
        
        # Now the layer has density but not E or nu
        # Try to execute slab calculations manually targeting D11
        result_slab = density_result.slab
        traces = executor._execute_slab_calculations(result_slab, "D11")
        
        assert len(traces) == 1, "Expected exactly one trace for D11"
        D11_trace = traces[0]
        
        # Verify the trace shows failure with a specific prerequisite error message
        assert not D11_trace.success, "D11 computation should have failed"
        assert D11_trace.error is not None, "Error message should not be None"
        # Should have the specific prerequisite error, not generic "Computation failed"
        assert "prerequisite" in D11_trace.error.lower() or "missing" in D11_trace.error.lower(), \
            f"Error should mention prerequisites: {D11_trace.error}"


class TestMetadataPreservation:
    """Test that slab metadata and attributes are preserved during execution."""
    
    def test_metadata_preserved_in_result_slab(self):
        """Result slab should preserve all metadata from original slab."""
        from snowpyt_mechparams.data_structures import Pit
        from snowpyt_mechparams.execution.config import ExecutionConfig
        
        executor = PathwayExecutor()
        
        # Create a slab with rich metadata (simulating creation from Pit.create_slabs)
        weak_layer = Layer(
            depth_top=50,
            thickness=ufloat(5, 0.5),
            grain_form="FC",
            hand_hardness="F"
        )
        
        layer1 = Layer(
            depth_top=0,
            thickness=ufloat(20, 1),
            grain_form="RG",
            hand_hardness="1F",
            density_measured=ufloat(150, 10)
        )
        
        layer2 = Layer(
            depth_top=20,
            thickness=ufloat(30, 1),
            grain_form="FC",
            hand_hardness="4F",
            density_measured=ufloat(250, 15)
        )
        
        # Create slab with full metadata (as would be created by Pit.create_slabs)
        original_slab = Slab(
            layers=[layer1, layer2],
            angle=38.0,
            weak_layer=weak_layer,
            pit_id="test_pit_12345",
            slab_id="test_pit_12345_slab_0",
            weak_layer_source="ECTP_failure_layer",
            test_result_index=0,
            test_result_properties={"score": "ECTP12", "propagation": True, "depth_top": 50},
            n_test_results_in_pit=2,
            # Optionally pre-existing calculated parameters
            A11=ufloat(1000, 50)
        )
        
        # Execute a parameterization (density calculation)
        density_node = graph.get_node("density")
        pathways = find_parameterizations(graph, density_node)
        pathway = pathways[0]  # Use first pathway
        
        config = ExecutionConfig(verbose=False)
        result = executor.execute_parameterization(
            parameterization=pathway,
            slab=original_slab,
            target_parameter="density",
            config=config
        )
        
        # Verify metadata is preserved in result slab
        result_slab = result.slab
        
        assert result_slab.pit_id == "test_pit_12345"
        assert result_slab.slab_id == "test_pit_12345_slab_0"
        assert result_slab.weak_layer_source == "ECTP_failure_layer"
        assert result_slab.test_result_index == 0
        assert result_slab.test_result_properties == {"score": "ECTP12", "propagation": True, "depth_top": 50}
        assert result_slab.n_test_results_in_pit == 2
        assert result_slab.angle == 38.0
        
        # Verify weak_layer reference is preserved
        assert result_slab.weak_layer is not None
        assert result_slab.weak_layer.depth_top == 50
        assert result_slab.weak_layer.grain_form == "FC"
        
        # Verify pre-existing calculated parameter is preserved
        assert result_slab.A11 is not None
        assert result_slab.A11.nominal_value == 1000
    
    def test_pit_reference_preserved(self):
        """Pit reference should be preserved in result slab."""
        from snowpyt_mechparams.execution.config import ExecutionConfig
        
        executor = PathwayExecutor()
        
        # Create a mock pit (simplified, just to test reference preservation)
        class MockSnowPit:
            pass
        
        mock_snow_pit = MockSnowPit()
        
        # Create a minimal Pit (without using from_snow_pit to avoid complex dependencies)
        layer = Layer(
            depth_top=0,
            thickness=ufloat(30, 1),
            grain_form="RG",
            hand_hardness="1F",
            density_measured=ufloat(200, 15)
        )
        
        slab = Slab(
            layers=[layer],
            angle=35.0,
            pit_id="test_pit_999"
        )
        
        # Execute a parameterization
        density_node = graph.get_node("density")
        pathways = find_parameterizations(graph, density_node)
        pathway = pathways[0]
        
        config = ExecutionConfig(verbose=False)
        result = executor.execute_parameterization(
            parameterization=pathway,
            slab=slab,
            target_parameter="density",
            config=config
        )
        
        # Verify pit_id is preserved
        assert result.slab.pit_id == "test_pit_999"


class TestDataFlowTracking:
    """Test that data_flow edges are properly tracked in methods_used."""
    
    def test_data_flow_recorded_for_direct_measurements(self):
        """methods_used should include 'data_flow' for directly measured parameters."""
        from snowpyt_mechparams.execution.config import ExecutionConfig
        
        executor = PathwayExecutor()
        
        # Create a layer with directly measured density
        layer = Layer(
            depth_top=0,
            thickness=ufloat(30, 1),
            grain_form="RG",
            density_measured=ufloat(250, 15)  # Direct measurement
        )
        
        slab = Slab(layers=[layer], angle=35.0)
        
        # Find pathways for elastic_modulus (which requires density)
        E_node = graph.get_node("elastic_modulus")
        pathways = find_parameterizations(graph, E_node)
        
        # Find a pathway that uses directly measured density (data_flow)
        # The first pathway typically uses measured_density → density via data_flow
        config = ExecutionConfig(verbose=False)
        
        # Test all pathways to ensure data_flow is tracked when used
        found_data_flow = False
        for pathway in pathways:
            result = executor.execute_parameterization(
                parameterization=pathway,
                slab=slab,
                target_parameter="elastic_modulus",
                config=config
            )
            
            # Check if density method is in methods_used
            if "density" in result.methods_used:
                # If density is in the pathway, it should have a method recorded
                density_method = result.methods_used["density"]
                assert density_method is not None, "Density method should not be None"
                assert isinstance(density_method, str), "Density method should be a string"
                
                # If the pathway uses measured density, it should be "data_flow"
                if density_method == "data_flow":
                    found_data_flow = True
                    # Verify the pathway succeeded
                    assert result.success, "Pathway with data_flow should succeed when density is measured"
        
        # Verify we found at least one pathway using data_flow
        assert found_data_flow, "Should find at least one pathway using data_flow for density"
    
    def test_all_elastic_modulus_pathways_have_density_method(self):
        """All elastic modulus pathways should record the density method used."""
        from snowpyt_mechparams.execution.config import ExecutionConfig
        
        executor = PathwayExecutor()
        
        # Create a layer with multiple ways to get density
        layer = Layer(
            depth_top=0,
            thickness=ufloat(30, 1),
            grain_form="RG",
            hand_hardness="1F",
            grain_size_avg=ufloat(0.5, 0.05),
            density_measured=ufloat(250, 15)  # Direct measurement
        )
        
        slab = Slab(layers=[layer], angle=35.0)
        
        # Find all pathways for elastic_modulus
        E_node = graph.get_node("elastic_modulus")
        pathways = find_parameterizations(graph, E_node)
        
        config = ExecutionConfig(verbose=False)
        
        # Test each pathway
        density_methods_found = set()
        for pathway in pathways:
            result = executor.execute_parameterization(
                parameterization=pathway,
                slab=slab,
                target_parameter="elastic_modulus",
                config=config
            )
            
            # Every elastic modulus pathway must go through density
            assert "density" in result.methods_used, \
                f"Pathway {result.pathway_description} should include density method"
            
            density_method = result.methods_used["density"]
            assert density_method is not None, "Density method should not be None"
            assert isinstance(density_method, str), "Density method should be a string"
            
            density_methods_found.add(density_method)
        
        # Should find data_flow among the methods
        assert "data_flow" in density_methods_found, \
            f"Should find data_flow method. Found: {density_methods_found}"
        
        # Should also find other methods (geldsetzer, kim_jamieson, etc.)
        assert len(density_methods_found) > 1, \
            f"Should find multiple density methods. Found: {density_methods_found}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
