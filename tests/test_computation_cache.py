"""Tests for ComputationCache."""

from uncertainties import ufloat
from snowpyt_mechparams.execution import ComputationCache, CacheStats


def test_cache_initialization():
    """Test cache initializes empty."""
    cache = ComputationCache()
    
    assert len(cache) == 0
    stats = cache.get_stats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.hit_rate == 0.0


def test_layer_param_cache_miss():
    """Test cache miss for layer parameter."""
    cache = ComputationCache()
    
    # First access is a miss
    value = cache.get_layer_param(0, "density", "geldsetzer")
    assert value is None
    
    stats = cache.get_stats()
    assert stats.hits == 0
    assert stats.misses == 1


def test_layer_param_cache_hit():
    """Test cache hit for layer parameter."""
    cache = ComputationCache()
    
    # Set a value
    test_value = ufloat(250, 10)
    cache.set_layer_param(0, "density", "geldsetzer", test_value)
    
    # Get it back (hit)
    value = cache.get_layer_param(0, "density", "geldsetzer")
    assert value == test_value
    
    stats = cache.get_stats()
    assert stats.hits == 1
    assert stats.misses == 0
    assert stats.hit_rate == 1.0


def test_layer_param_different_methods():
    """Test that different methods are cached separately."""
    cache = ComputationCache()
    
    # Set values with different methods
    value1 = ufloat(250, 10)
    value2 = ufloat(260, 15)
    
    cache.set_layer_param(0, "density", "geldsetzer", value1)
    cache.set_layer_param(0, "density", "kim_jamieson_table2", value2)
    
    # Should get back different values
    assert cache.get_layer_param(0, "density", "geldsetzer") == value1
    assert cache.get_layer_param(0, "density", "kim_jamieson_table2") == value2


def test_layer_param_different_layers():
    """Test that different layers are cached separately."""
    cache = ComputationCache()
    
    # Set values for different layers
    value1 = ufloat(250, 10)
    value2 = ufloat(300, 12)
    
    cache.set_layer_param(0, "density", "geldsetzer", value1)
    cache.set_layer_param(1, "density", "geldsetzer", value2)
    
    # Should get back different values
    assert cache.get_layer_param(0, "density", "geldsetzer") == value1
    assert cache.get_layer_param(1, "density", "geldsetzer") == value2


def test_provenance_tracking():
    """Test that provenance is tracked."""
    cache = ComputationCache()
    
    # Set a value
    value = ufloat(250, 10)
    cache.set_layer_param(0, "density", "geldsetzer", value)
    
    # Check provenance
    method = cache.get_provenance(0, "density")
    assert method == "geldsetzer"


def test_cache_clear():
    """Test clearing the cache."""
    cache = ComputationCache()

    # Set density values
    cache.set_layer_param(0, "density", "geldsetzer", ufloat(250, 10))
    cache.set_layer_param(1, "density", "geldsetzer", ufloat(280, 12))

    # Access to generate stats
    cache.get_layer_param(0, "density", "geldsetzer")

    assert len(cache) == 2
    assert cache.get_stats().hits == 1

    # Clear
    cache.clear()

    assert len(cache) == 0
    assert cache.get_stats().hits == 0
    assert cache.get_stats().misses == 0


def test_cache_stats_hit_rate():
    """Test hit rate calculation."""
    cache = ComputationCache()
    
    # Set a value
    cache.set_layer_param(0, "density", "geldsetzer", ufloat(250, 10))
    
    # 1 hit, 2 misses
    cache.get_layer_param(0, "density", "geldsetzer")  # hit
    cache.get_layer_param(1, "density", "geldsetzer")  # miss
    cache.get_layer_param(0, "elastic_modulus", "bergfeld")  # miss
    
    stats = cache.get_stats()
    assert stats.hits == 1
    assert stats.misses == 2
    assert stats.total == 3
    assert abs(stats.hit_rate - 1/3) < 0.001


def test_cache_stats_to_dict():
    """Test converting cache stats to dict."""
    cache = ComputationCache()
    
    # Generate some stats
    cache.set_layer_param(0, "density", "geldsetzer", ufloat(250, 10))
    cache.get_layer_param(0, "density", "geldsetzer")  # hit
    cache.get_layer_param(1, "density", "geldsetzer")  # miss
    
    stats_dict = cache.get_stats().to_dict()
    
    assert 'hits' in stats_dict
    assert 'misses' in stats_dict
    assert 'hit_rate' in stats_dict
    assert stats_dict['hits'] == 1
    assert stats_dict['misses'] == 1
    assert stats_dict['hit_rate'] == 0.5


def test_cache_repr():
    """Test cache string representation."""
    cache = ComputationCache()

    # Set a density value and generate a hit
    cache.set_layer_param(0, "density", "geldsetzer", ufloat(250, 10))
    cache.get_layer_param(0, "density", "geldsetzer")  # hit

    repr_str = repr(cache)

    assert "ComputationCache" in repr_str
    assert "density_entries=1" in repr_str
    assert "hits=1" in repr_str
    assert "misses=0" in repr_str


def test_cache_stats_zero_total():
    """Test hit rate with zero total accesses."""
    stats = CacheStats()
    
    assert stats.total == 0
    assert stats.hit_rate == 0.0  # Should handle division by zero
