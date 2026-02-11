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
        
        # Simulate some cache activity
        executor._cache_hits = 10
        executor._cache_misses = 5
        executor._layer_cache[(0, "density", "data_flow")] = ufloat(250, 10)
        
        # Clear cache
        executor.clear_cache()
        
        # Verify everything is reset
        assert executor._cache_hits == 0
        assert executor._cache_misses == 0
        assert len(executor._layer_cache) == 0
        assert len(executor._slab_cache) == 0


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
        result1 = executor.execute_parameterization(
            parameterization=kochle_pathway,
            slab=slab,
            target_parameter="poissons_ratio",
            include_plate_theory=False
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
            include_plate_theory=False
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
        
        # Execute slab calculations
        from snowpyt_mechparams.execution.results import LayerResult
        layer_results = [
            LayerResult(layer=layer1, method_calls=[], layer_index=0),
            LayerResult(layer=layer2, method_calls=[], layer_index=1)
        ]
        
        slab_result = executor._execute_slab_calculations(slab, layer_results)
        
        # All slab parameters should be computed
        assert slab_result.A11 is not None
        assert slab_result.B11 is not None
        assert slab_result.D11 is not None
        assert slab_result.A55 is not None
        
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
        
        from snowpyt_mechparams.execution.results import LayerResult
        layer_results = [
            LayerResult(layer=layer, method_calls=[], layer_index=0)
        ]
        
        slab_result = executor._execute_slab_calculations(slab, layer_results)
        
        # All slab parameters should be None
        assert slab_result.A11 is None
        assert slab_result.B11 is None
        assert slab_result.D11 is None
        assert slab_result.A55 is None
        
        # Check that method calls show failure reasons
        a11_call = [c for c in slab_result.slab_method_calls if c.parameter == "A11"][0]
        assert not a11_call.success
        assert "prerequisites" in a11_call.failure_reason.lower()


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
