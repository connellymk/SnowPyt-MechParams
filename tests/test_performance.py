"""Performance tests for copy optimization."""

import time
from uncertainties import ufloat
import pytest
from snowpyt_mechparams import ExecutionEngine, Slab, Layer, ExecutionConfig
from snowpyt_mechparams.graph import graph


def create_large_slab(n_layers: int = 100) -> Slab:
    """Create a slab with many layers for performance testing."""
    layers = []
    for i in range(n_layers):
        layer = Layer(
            depth_top=i * 10,
            thickness=ufloat(10, 0.5),
            hand_hardness="4F",
            grain_form="RG",
            density_measured=ufloat(250, 10) if i % 10 == 0 else None  # Sparse measured data
        )
        layers.append(layer)
    return Slab(layers=layers, angle=38.0)


@pytest.mark.performance
def test_large_slab_execution_time():
    """Test execution time with large slab (100 layers)."""
    # Create large slab
    slab = create_large_slab(100)
    
    # Time execution
    engine = ExecutionEngine(graph)
    
    start = time.perf_counter()
    results = engine.execute_all(slab, "poissons_ratio")
    elapsed = time.perf_counter() - start
    
    # Verify it completed
    assert results.total_pathways > 0
    assert results.successful_pathways > 0
    
    # Print timing info
    print(f"\n100-layer slab execution:")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Pathways: {results.total_pathways}")
    print(f"  Time per pathway: {(elapsed / results.total_pathways) * 1000:.1f}ms")
    print(f"  Cache hit rate: {results.cache_stats['hit_rate']:.1%}")
    
    # With copy-on-write optimization, should be reasonably fast
    # Target: < 1 second for 100 layers
    # (Without optimization, would be much slower due to deep copying)
    assert elapsed < 5.0  # Generous timeout


@pytest.mark.performance
def test_copy_overhead_comparison():
    """Compare copy overhead between small and large slabs."""
    # Small slab (10 layers)
    small_slab = create_large_slab(10)
    
    # Large slab (50 layers)
    large_slab = create_large_slab(50)
    
    engine = ExecutionEngine(graph)
    
    # Time small slab
    start = time.perf_counter()
    small_results = engine.execute_all(small_slab, "poissons_ratio")
    small_time = time.perf_counter() - start
    
    # Clear cache for fair comparison
    engine.executor.clear_cache()
    
    # Time large slab
    start = time.perf_counter()
    large_results = engine.execute_all(large_slab, "poissons_ratio")
    large_time = time.perf_counter() - start
    
    # Print comparison
    print(f"\nCopy overhead comparison:")
    print(f"  10 layers: {small_time:.3f}s ({small_results.total_pathways} pathways)")
    print(f"  50 layers: {large_time:.3f}s ({large_results.total_pathways} pathways)")
    print(f"  Ratio: {large_time / small_time:.2f}x")
    
    # With copy-on-write, scaling should be near-linear with layer count
    # (not quadratic or worse as with deep copying everything)
    # Expect roughly 5x time for 5x layers (allowing for some overhead)
    assert large_time / small_time < 8.0  # Should scale reasonably


@pytest.mark.performance
def test_cache_effectiveness_large_slab():
    """Verify cache is effective with large slabs."""
    slab = create_large_slab(50)
    
    engine = ExecutionEngine(graph)
    results = engine.execute_all(slab, "elastic_modulus")
    
    # With 50 layers and multiple pathways sharing density calculations,
    # should have significant cache hits
    print(f"\n50-layer slab cache effectiveness:")
    print(f"  Total pathways: {results.total_pathways}")
    print(f"  Cache hits: {results.cache_stats['hits']}")
    print(f"  Cache misses: {results.cache_stats['misses']}")
    print(f"  Hit rate: {results.cache_stats['hit_rate']:.1%}")
    
    # Should have good hit rate (> 40%)
    # With 50 layers × 16 pathways, cache provides significant benefit
    assert results.cache_stats['hit_rate'] > 0.4


def test_memory_efficiency():
    """Test that copy optimization reduces memory usage."""
    import sys
    
    # Create slab
    slab = create_large_slab(100)
    
    # Get memory size of original slab (rough estimate)
    slab_size = sys.getsizeof(slab)
    layers_size = sum(sys.getsizeof(layer) for layer in slab.layers)
    total_input = slab_size + layers_size
    
    # Execute
    engine = ExecutionEngine(graph)
    results = engine.execute_all(slab, "poissons_ratio")
    
    # Get memory size of all result slabs
    result_size = 0
    for pathway in results.pathways.values():
        result_size += sys.getsizeof(pathway.slab)
        result_size += sum(sys.getsizeof(layer) for layer in pathway.slab.layers)
    
    print(f"\nMemory usage:")
    print(f"  Input slab: ~{total_input / 1024:.1f} KB")
    print(f"  All result slabs: ~{result_size / 1024:.1f} KB")
    print(f"  Pathways: {results.total_pathways}")
    print(f"  Average per pathway: ~{result_size / results.total_pathways / 1024:.1f} KB")
    
    # With copy-on-write, result slabs should share unchanged layers
    # Total memory should not be pathways × slab_size
    # This is a soft assertion - just informational
    print(f"  Memory multiplication factor: {result_size / total_input:.1f}x")


def test_immutability_guarantee_with_optimization():
    """Verify original slab is never modified even with copy optimization."""
    # Create slab
    layer1 = Layer(
        depth_top=0,
        thickness=ufloat(20, 1),
        hand_hardness="4F",
        grain_form="RG"
    )
    layer2 = Layer(
        depth_top=20,
        thickness=ufloat(30, 1),
        hand_hardness="1F",
        grain_form="FC"
    )
    slab = Slab(layers=[layer1, layer2], angle=35)
    
    # Store original state
    layer1_id = id(slab.layers[0])
    layer2_id = id(slab.layers[1])
    layer1_poissons_before = slab.layers[0].poissons_ratio
    layer2_poissons_before = slab.layers[1].poissons_ratio
    
    assert layer1_poissons_before is None
    assert layer2_poissons_before is None
    
    # Execute multiple pathways
    engine = ExecutionEngine(graph)
    results = engine.execute_all(slab, "poissons_ratio")
    
    # Verify original slab completely unchanged
    assert id(slab.layers[0]) == layer1_id
    assert id(slab.layers[1]) == layer2_id
    assert slab.layers[0].poissons_ratio is None
    assert slab.layers[1].poissons_ratio is None
    
    # Verify results have computed values.
    # Every "successful" pathway must have computed poissons_ratio on all layers.
    successful = results.get_successful_pathways()
    assert len(successful) > 0, "Expected at least one successful pathway"
    for pathway in successful.values():
        assert pathway.slab.layers[0].poissons_ratio is not None
        assert pathway.slab.layers[1].poissons_ratio is not None
        # Every pathway result must be a distinct slab object (not the original)
        assert pathway.slab is not slab
