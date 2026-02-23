"""Caching system for computation results.

This module provides a dedicated cache for computed parameter values,
implementing dynamic programming to avoid redundant calculations across
pathway executions for the same slab.

Only **density** values are cached. Downstream layer parameters
(elastic_modulus, poissons_ratio, shear_modulus) depend on which density
method was used upstream, so caching them would silently return wrong values
for pathways that use a different density method. Slab parameters (D11, A11,
B11, A55) depend on those downstream values and are therefore also never
cached.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from snowpyt_mechparams.data_structures import UncertainValue


@dataclass
class CacheStats:
    """
    Cache performance statistics.
    
    Tracks hits, misses, and computes hit rate for monitoring
    dynamic programming effectiveness.
    
    Attributes
    ----------
    hits : int
        Number of times a cached value was retrieved
    misses : int
        Number of times a value had to be computed
        
    Examples
    --------
    >>> stats = CacheStats(hits=75, misses=25)
    >>> print(f"Hit rate: {stats.hit_rate:.1%}")
    Hit rate: 75.0%
    """
    hits: int = 0
    misses: int = 0
    
    @property
    def total(self) -> int:
        """Total cache accesses (hits + misses)."""
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a float between 0.0 and 1.0."""
        if self.total == 0:
            return 0.0
        return self.hits / self.total
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for backward compatibility."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hit_rate
        }
    
    def __repr__(self) -> str:
        """Return concise string representation."""
        return f"CacheStats(hits={self.hits}, misses={self.misses}, hit_rate={self.hit_rate:.1%})"


class ComputationCache:
    """
    Cache for computed density values with dynamic programming.

    This cache stores computed density values across pathway executions for
    the same slab, avoiding redundant density calculations when multiple
    pathways share the same density method.

    Only density is cached because it depends solely on layer-intrinsic data
    (hand hardness, grain form, grain size). Downstream parameters
    (elastic_modulus, poissons_ratio, shear_modulus) depend on which density
    value was computed for each pathway and must therefore be computed fresh
    for every pathway.

    Features
    --------
    - Layer-level cache (density only): (layer_index, parameter, method) -> value
    - Provenance tracking (which method computed each parameter)
    - Performance statistics (hits, misses, hit rate)
    - Fast lookups with tuple keys

    The cache should be:
    - Cleared when switching to a new slab
    - Persistent across pathways for the same slab

    Examples
    --------
    Basic usage:

    >>> cache = ComputationCache()
    >>>
    >>> # Set a density value
    >>> cache.set_layer_param(0, "density", "geldsetzer", ufloat(250, 10))
    >>>
    >>> # Get it back (cache hit)
    >>> value = cache.get_layer_param(0, "density", "geldsetzer")
    >>> print(cache.get_stats())
    CacheStats(hits=1, misses=0, hit_rate=100.0%)

    Cache lifecycle:

    >>> cache = ComputationCache()
    >>> # Compute for first pathway
    >>> cache.set_layer_param(0, "density", "geldsetzer", value1)
    >>>
    >>> # Second pathway reuses density (cache hit!)
    >>> cached = cache.get_layer_param(0, "density", "geldsetzer")
    >>>
    >>> # Switch to new slab
    >>> cache.clear()
    """

    def __init__(self, enable_stats: bool = True):
        """
        Initialize the cache.

        Parameters
        ----------
        enable_stats : bool
            Whether to track cache statistics. Default: True.
        """
        # Layer cache: (layer_index, parameter, method) -> value
        # In practice only density entries are stored here.
        self._layer_cache: Dict[Tuple[int, str, str], UncertainValue] = {}

        # Provenance: (layer_index, parameter) -> method_name
        # Records which method computed each parameter
        self._provenance: Dict[Tuple[int, str], str] = {}

        # Statistics
        self._stats = CacheStats() if enable_stats else None
    
    def get_layer_param(
        self,
        layer_index: int,
        parameter: str,
        method: str
    ) -> Optional[UncertainValue]:
        """
        Get a cached layer parameter value.
        
        Parameters
        ----------
        layer_index : int
            Index of the layer (0-based)
        parameter : str
            Parameter name (e.g., "density", "elastic_modulus")
        method : str
            Method name used to compute it (e.g., "geldsetzer")
        
        Returns
        -------
        Optional[UncertainValue]
            Cached value if found, None otherwise
        """
        key = (layer_index, parameter, method)
        value = self._layer_cache.get(key)
        
        # Update statistics
        if self._stats:
            if value is not None:
                self._stats.hits += 1
            else:
                self._stats.misses += 1
        
        return value
    
    def set_layer_param(
        self,
        layer_index: int,
        parameter: str,
        method: str,
        value: UncertainValue
    ) -> None:
        """
        Cache a layer parameter value.
        
        Parameters
        ----------
        layer_index : int
            Index of the layer (0-based)
        parameter : str
            Parameter name (e.g., "density", "elastic_modulus")
        method : str
            Method name used to compute it (e.g., "geldsetzer")
        value : UncertainValue
            Computed value to cache
        """
        key = (layer_index, parameter, method)
        self._layer_cache[key] = value
        
        # Track provenance (which method computed this parameter)
        provenance_key = (layer_index, parameter)
        self._provenance[provenance_key] = method
    
    def get_provenance(
        self,
        layer_index: int,
        parameter: str
    ) -> Optional[str]:
        """
        Get the method that computed a parameter.
        
        Useful for understanding which method was used when multiple
        methods could compute the same parameter.
        
        Parameters
        ----------
        layer_index : int
            Index of the layer
        parameter : str
            Parameter name
        
        Returns
        -------
        Optional[str]
            Method name if parameter was computed, None otherwise
        """
        return self._provenance.get((layer_index, parameter))
    
    def clear(self) -> None:
        """
        Clear all caches and reset statistics.

        Call this when switching to a new slab to ensure cached density values
        don't carry over between different slabs.
        """
        self._layer_cache.clear()
        self._provenance.clear()
        if self._stats:
            self._stats.hits = 0
            self._stats.misses = 0
    
    def get_stats(self) -> CacheStats:
        """
        Get cache performance statistics.
        
        Returns
        -------
        CacheStats
            Statistics object with hits, misses, and hit_rate
        """
        if self._stats is None:
            return CacheStats()
        return self._stats
    
    def __len__(self) -> int:
        """Return total number of cached items (density entries only)."""
        return len(self._layer_cache)

    def __repr__(self) -> str:
        """Return concise string representation."""
        stats = self.get_stats()
        return (f"ComputationCache("
                f"density_entries={len(self._layer_cache)}, "
                f"hits={stats.hits}, "
                f"misses={stats.misses}, "
                f"hit_rate={stats.hit_rate:.1%})")
