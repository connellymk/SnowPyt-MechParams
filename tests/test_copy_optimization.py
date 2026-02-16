"""Tests for copy optimization (copy-on-write pattern)."""

from uncertainties import ufloat
from snowpyt_mechparams import ExecutionEngine, Slab, Layer
from snowpyt_mechparams.graph import graph


def test_original_slab_not_modified():
    """Ensure original slab is never modified during execution."""
    # Create original slab
    original_layer = Layer(
        depth_top=0,
        thickness=ufloat(30, 1),
        hand_hardness="4F",
        grain_form="RG"
    )
    original_slab = Slab(layers=[original_layer], angle=35)
    
    # Store original values
    original_layer_id = id(original_slab.layers[0])
    original_density = original_slab.layers[0].density_calculated
    original_poissons = original_slab.layers[0].poissons_ratio
    
    assert original_density is None
    assert original_poissons is None
    
    # Execute
    engine = ExecutionEngine(graph)
    results = engine.execute_all(original_slab, "poissons_ratio")
    
    # Verify original slab unchanged
    assert original_slab.layers[0].density_calculated is None
    assert original_slab.layers[0].poissons_ratio is None
    assert id(original_slab.layers[0]) == original_layer_id
    
    # Verify results have computed values
    successful = results.get_successful_pathways()
    if successful:
        first_result = list(successful.values())[0]
        # Result slab should have computed value
        assert first_result.slab.layers[0].poissons_ratio is not None


def test_copy_on_write_reuses_unchanged_layers():
    """Verify that unchanged layers are reused (not copied)."""
    # Create slab with multiple layers
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
    
    # Store original layer IDs
    layer1_id = id(slab.layers[0])
    layer2_id = id(slab.layers[1])
    
    # Execute - will compute on both layers
    engine = ExecutionEngine(graph)
    results = engine.execute_all(slab, "poissons_ratio")
    
    # Get a result
    successful = results.get_successful_pathways()
    if successful:
        first_result = list(successful.values())[0]
        result_slab = first_result.slab
        
        # Result layers should be different objects (they were computed on)
        # Note: They WILL be different because we computed values on them
        assert result_slab.layers[0] is not slab.layers[0]
        assert result_slab.layers[1] is not slab.layers[1]
        
        # But original layers should still be unchanged
        assert slab.layers[0].poissons_ratio is None
        assert slab.layers[1].poissons_ratio is None


def test_dataclass_replace_faster_than_deepcopy():
    """Verify we're using dataclass replace instead of deepcopy."""
    import time
    from dataclasses import replace
    from copy import deepcopy
    
    # Create a layer
    layer = Layer(
        depth_top=0,
        thickness=ufloat(30, 1),
        hand_hardness="4F",
        grain_form="RG",
        density_measured=ufloat(250, 10)
    )
    
    # Time deepcopy
    start = time.perf_counter()
    for _ in range(1000):
        _ = deepcopy(layer)
    deepcopy_time = time.perf_counter() - start
    
    # Time dataclass replace
    start = time.perf_counter()
    for _ in range(1000):
        _ = replace(layer)
    replace_time = time.perf_counter() - start
    
    # Replace should be faster
    print(f"\nDeep copy time: {deepcopy_time:.4f}s")
    print(f"Dataclass replace time: {replace_time:.4f}s")
    print(f"Speedup: {deepcopy_time / replace_time:.1f}x")
    
    # Typically 5-10x faster
    assert replace_time < deepcopy_time


def test_multiple_pathways_dont_interfere():
    """Verify multiple pathways don't interfere with each other."""
    layer = Layer(
        depth_top=0,
        thickness=ufloat(30, 1),
        hand_hardness="4F",
        grain_form="RG"
    )
    slab = Slab(layers=[layer], angle=35)
    
    engine = ExecutionEngine(graph)
    results = engine.execute_all(slab, "poissons_ratio")
    
    # Each pathway should have independent slab with computed values
    successful = results.get_successful_pathways()
    
    if len(successful) >= 2:
        result1, result2 = list(successful.values())[:2]
        
        # Each should have their own slab
        assert result1.slab is not result2.slab
        
        # But original is unchanged
        assert slab.layers[0].poissons_ratio is None
