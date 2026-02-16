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
        value, was_cached = executor._get_or_compute_layer_param(
            layer=layer,
            layer_index=0,
            parameter="layer_thickness",
            method="data_flow"
        )
        
        # Should return the thickness directly
        assert value == layer.thickness
        assert was_cached == False  # No caching for direct properties


class TestDynamicProgramming:
    """Test dynamic programming across pathways."""
    
    def test_cache_persists_across_calls(self):
        """Cache should persist across execute_parameterization calls."""
        executor = PathwayExecutor()
        
        # Create a simple slab
        # Use poissons_ratio pathways (simpler - just grain_form, no density dependency for kochle)
        layer = Layer(
            thickness=ufloat(30, 1),
            grain_form="RG"
        )
        slab = Slab(layers=[layer], angle=35)
        
        # Get pathways for poissons_ratio (simpler - kochle uses only grain_form)
        nu_node = graph.get_node("poissons_ratio")
        pathways = find_parameterizations(graph, nu_node)
        
        # Find the kochle pathway (no density dependency)
        kochle_pathway = [p for p in pathways if 'kochle' in str(p)][0]
        
        # Execute first time
        from snowpyt_mechparams.execution.config import ExecutionConfig
        config = ExecutionConfig(verbose=False)
        
        result1 = executor.execute_parameterization(
            parameterization=kochle_pathway,
            slab=slab,
            target_parameter="poissons_ratio",
            config=config
        )
        
        # Check that we had some cache misses (first execution)
        stats1 = executor.get_cache_stats()
        assert stats1['misses'] > 0
        assert stats1['hits'] == 0  # Nothing cached yet
        
        # Execute second time (same pathway - should hit cache)
        result2 = executor.execute_parameterization(
            parameterization=kochle_pathway,
            slab=slab,
            target_parameter="poissons_ratio",
            config=config
        )
        
        # Check that we had cache hits this time
        stats2 = executor.get_cache_stats()
        assert stats2['hits'] > stats1['hits']  # More hits now
        assert stats2['hit_rate'] > 0.0  # Some hits occurred


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
        
        # Execute slab calculations using the new v2 method
        slab_traces = executor._execute_slab_calculations_v2(slab)
        
        # Should have traces for A11, B11, D11, A55
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
        
        # Execute slab calculations using the new v2 method
        slab_traces = executor._execute_slab_calculations_v2(slab)
        
        # Should have traces for A11, B11, D11, A55
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
    """Test slab-level parameter caching."""
    
    def test_slab_params_cached(self):
        """Slab parameters should be cached after first computation."""
        executor = PathwayExecutor()
        
        # Create a slab with all necessary properties
        layer = Layer(
            thickness=ufloat(30, 1),
            elastic_modulus=ufloat(2.0, 0.2),
            poissons_ratio=ufloat(0.3, 0.02),
            shear_modulus=ufloat(0.7, 0.1)
        )
        slab = Slab(layers=[layer], angle=35)
        
        # Compute D11 first time
        value1, cached1 = executor._get_or_compute_slab_param(
            slab, "D11", "weissgraeber_rosendahl"
        )
        
        assert value1 is not None
        assert cached1 == False  # First computation
        
        # Compute D11 second time
        value2, cached2 = executor._get_or_compute_slab_param(
            slab, "D11", "weissgraeber_rosendahl"
        )
        
        assert value2 is not None
        assert cached2 == True  # Retrieved from cache
        assert value1 == value2  # Same value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
