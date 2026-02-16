"""Simplified result structures for execution engine (v2).

This module provides a streamlined hierarchy of result classes:
- ComputationTrace: Records a single computation
- PathwayResult: Results for one pathway on one slab
- ExecutionResults: Results from all pathways

This replaces the old 5-level hierarchy (MethodCall → LayerResult → 
SlabResult → PathwayResult → ExecutionResults) with a cleaner 3-level structure.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from snowpyt_mechparams.data_structures import Slab, UncertainValue


@dataclass
class ComputationTrace:
    """
    Records a single computation (method call) in a pathway.
    
    This replaces the old MethodCall, LayerResult, and SlabResult with a
    unified structure that works for both layer and slab computations.
    
    Attributes
    ----------
    parameter : str
        Target parameter (e.g., "density", "elastic_modulus", "A11")
    method_name : str
        Method used (e.g., "geldsetzer", "bergfeld", "weissgraeber_rosendahl")
    layer_index : Optional[int]
        Layer index for layer-level calculations (None for slab-level)
    output : Optional[UncertainValue]
        Computed value (None if computation failed)
    success : bool
        Whether computation succeeded
    cached : bool
        Whether result came from cache (dynamic programming)
    error : Optional[str]
        Error message if computation failed
    inputs_summary : Dict[str, Any]
        Summary of inputs used (for debugging and traceability)
        
    Examples
    --------
    Layer-level computation:
    
    >>> trace = ComputationTrace(
    ...     parameter="density",
    ...     method_name="geldsetzer",
    ...     layer_index=0,
    ...     output=ufloat(250, 10),
    ...     success=True,
    ...     cached=False
    ... )
    
    Slab-level computation:
    
    >>> trace = ComputationTrace(
    ...     parameter="D11",
    ...     method_name="weissgraeber_rosendahl",
    ...     layer_index=None,  # Slab-level
    ...     output=ufloat(1500, 50),
    ...     success=True,
    ...     cached=True
    ... )
    """
    parameter: str
    method_name: str
    layer_index: Optional[int]  # None for slab-level
    output: Optional[UncertainValue]
    success: bool
    cached: bool = False
    error: Optional[str] = None
    inputs_summary: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_layer_level(self) -> bool:
        """Check if this is a layer-level computation."""
        return self.layer_index is not None
    
    @property
    def is_slab_level(self) -> bool:
        """Check if this is a slab-level computation."""
        return self.layer_index is None
    
    def __repr__(self) -> str:
        """Return concise string representation."""
        level = f"L{self.layer_index}" if self.is_layer_level else "SLAB"
        status = "✓" if self.success else "✗"
        cached_str = " [cached]" if self.cached else ""
        return (f"ComputationTrace({level} {self.parameter}.{self.method_name} "
                f"{status}{cached_str})")


@dataclass
class PathwayResult:
    """
    Results from executing a single parameterization pathway.
    
    This simplified version absorbs the old LayerResult and SlabResult
    into a single structure, storing the computed slab (which contains
    all layer computations) and a flat list of all computation traces.
    
    Attributes
    ----------
    pathway_id : str
        Unique identifier (e.g., "density:geldsetzer->elastic_modulus:bergfeld")
    pathway_description : str
        Human-readable description
    methods_used : Dict[str, str]
        Mapping of parameter -> method_name used in this pathway
    slab : Slab
        Slab with all computed values (both layer and slab level).
        The layers in this slab have computed parameters populated.
    computation_trace : List[ComputationTrace]
        Ordered list of all computations performed (layer and slab)
    success : bool
        True if pathway produced at least some results
    warnings : List[str]
        Non-fatal issues encountered during execution
        
    Examples
    --------
    >>> result = PathwayResult(
    ...     pathway_id="density:geldsetzer->elastic_modulus:bergfeld",
    ...     pathway_description="density=geldsetzer | elastic_modulus=bergfeld",
    ...     methods_used={"density": "geldsetzer", "elastic_modulus": "bergfeld"},
    ...     slab=computed_slab,
    ...     computation_trace=traces,
    ...     success=True
    ... )
    
    Access layer results:
    
    >>> for layer in result.slab.layers:
    ...     print(f"Density: {layer.density_calculated}")
    
    Access computation history:
    
    >>> for trace in result.get_layer_traces():
    ...     print(f"Layer {trace.layer_index}: {trace.parameter} = {trace.output}")
    """
    pathway_id: str
    pathway_description: str
    methods_used: Dict[str, str]
    slab: Slab  # Contains layers with computed values
    computation_trace: List[ComputationTrace]
    success: bool
    warnings: List[str] = field(default_factory=list)
    
    def get_layer_traces(self) -> List[ComputationTrace]:
        """Get only layer-level computation traces."""
        return [t for t in self.computation_trace if t.is_layer_level]
    
    def get_slab_traces(self) -> List[ComputationTrace]:
        """Get only slab-level computation traces."""
        return [t for t in self.computation_trace if t.is_slab_level]
    
    def get_successful_traces(self) -> List[ComputationTrace]:
        """Get only successful computation traces."""
        return [t for t in self.computation_trace if t.success]
    
    def get_failed_traces(self) -> List[ComputationTrace]:
        """Get only failed computation traces."""
        return [t for t in self.computation_trace if not t.success]
    
    def get_traces_for_parameter(self, parameter: str) -> List[ComputationTrace]:
        """Get all traces for a specific parameter."""
        return [t for t in self.computation_trace if t.parameter == parameter]
    
    def get_cache_hit_count(self) -> int:
        """Count how many computations were cached."""
        return sum(1 for t in self.computation_trace if t.cached)
    
    def __repr__(self) -> str:
        """Return concise string representation."""
        status = "SUCCESS" if self.success else "FAILED"
        n_traces = len(self.computation_trace)
        n_cached = self.get_cache_hit_count()
        return (f"PathwayResult({self.pathway_description} [{status}] "
                f"{n_traces} computations, {n_cached} cached)")


@dataclass
class ExecutionResults:
    """
    Top-level results container for all pathway executions.
    
    This is the main return type from ExecutionEngine.execute_all().
    Results are stored in a dictionary keyed by pathway description.
    
    Attributes
    ----------
    target_parameter : str
        The parameter that was computed (e.g., "elastic_modulus")
    source_slab : Slab
        Original input slab (unmodified)
    pathways : Dict[str, PathwayResult]
        Mapping of pathway_description -> PathwayResult
    cache_stats : Dict[str, float]
        Cache performance statistics (hits, misses, hit_rate)
        
    Examples
    --------
    >>> results = engine.execute_all(slab, "elastic_modulus")
    >>> print(f"{results.successful_pathways}/{results.total_pathways} succeeded")
    >>> print(f"Cache hit rate: {results.cache_stats['hit_rate']:.1%}")
    >>>
    >>> # Iterate over successful pathways
    >>> for desc, pathway in results.get_successful_pathways().items():
    ...     print(f"{desc}: {pathway.slab.layers[0].elastic_modulus}")
    """
    target_parameter: str
    source_slab: Slab
    pathways: Dict[str, PathwayResult]
    cache_stats: Dict[str, float] = field(default_factory=dict)
    
    @property
    def total_pathways(self) -> int:
        """Total number of pathways attempted."""
        return len(self.pathways)
    
    @property
    def successful_pathways(self) -> int:
        """Number of pathways that succeeded."""
        return sum(1 for p in self.pathways.values() if p.success)
    
    @property
    def failed_pathways(self) -> int:
        """Number of pathways that failed."""
        return self.total_pathways - self.successful_pathways
    
    @property
    def results(self) -> Dict[str, PathwayResult]:
        """Alias for 'pathways' for backward compatibility."""
        return self.pathways
    
    def get_pathway_by_id(self, pathway_id: str) -> Optional[PathwayResult]:
        """
        Find a pathway result by its unique ID.
        
        Parameters
        ----------
        pathway_id : str
            The pathway ID to search for
            
        Returns
        -------
        Optional[PathwayResult]
            The matching pathway result, or None if not found
        """
        for result in self.pathways.values():
            if result.pathway_id == pathway_id:
                return result
        return None
    
    def get_successful_pathways(self) -> Dict[str, PathwayResult]:
        """
        Get only the pathways that succeeded.
        
        Returns
        -------
        Dict[str, PathwayResult]
            Dictionary of successful pathway results
        """
        return {k: v for k, v in self.pathways.items() if v.success}
    
    def get_failed_pathways(self) -> Dict[str, PathwayResult]:
        """
        Get only the pathways that failed.
        
        Returns
        -------
        Dict[str, PathwayResult]
            Dictionary of failed pathway results
        """
        return {k: v for k, v in self.pathways.items() if not v.success}
    
    def get_all_computation_traces(self) -> List[ComputationTrace]:
        """
        Get all computation traces from all pathways.
        
        Returns
        -------
        List[ComputationTrace]
            All computation traces across all pathways
        """
        traces = []
        for pathway in self.pathways.values():
            traces.extend(pathway.computation_trace)
        return traces
    
    def get_all_methods_used(self) -> Dict[str, set]:
        """
        Get all unique methods used for each parameter across all pathways.
        
        Returns
        -------
        Dict[str, set]
            Mapping of parameter -> set of method names
        """
        methods: Dict[str, set] = {}
        for result in self.pathways.values():
            for param, method in result.methods_used.items():
                if param not in methods:
                    methods[param] = set()
                methods[param].add(method)
        return methods
    
    def __repr__(self) -> str:
        """Return concise string representation."""
        return (f"ExecutionResults({self.target_parameter}: "
                f"{self.successful_pathways}/{self.total_pathways} succeeded, "
                f"cache_hit_rate={self.cache_stats.get('hit_rate', 0):.1%})")
