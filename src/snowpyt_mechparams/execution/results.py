"""
Result data structures for parameterization execution.

This module contains dataclasses for storing the results of executing
parameterization pathways on snow pit data.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from snowpyt_mechparams.data_structures import Layer, Slab, UncertainValue


@dataclass
class MethodCall:
    """
    Records a single method invocation in a calculation pathway.

    Attributes
    ----------
    parameter : str
        Target parameter (e.g., "density", "elastic_modulus")
    method_name : str
        Method used (e.g., "geldsetzer", "bergfeld")
    inputs : Dict[str, Any]
        Input parameter names and values used
    output : Optional[UncertainValue]
        Computed value (None if failed)
    success : bool
        Whether calculation succeeded
    failure_reason : Optional[str]
        Why it failed (e.g., "missing grain_form")
    """
    parameter: str
    method_name: str
    inputs: Dict[str, Any]
    output: Optional[UncertainValue]
    success: bool
    failure_reason: Optional[str] = None


@dataclass
class LayerResult:
    """
    Contains a layer with computed values plus the pathway trace.

    Attributes
    ----------
    layer : Layer
        Deep copy of the layer with computed values populated
    method_calls : List[MethodCall]
        Ordered list of calculations performed on this layer
    layer_index : int
        Position in original slab (0-indexed, 0 = top)
    """
    layer: Layer
    method_calls: List[MethodCall]
    layer_index: int


@dataclass
class SlabResult:
    """
    Contains a slab with computed values plus the pathway trace.

    Attributes
    ----------
    slab : Slab
        Deep copy of slab with layers containing computed values
    layer_results : List[LayerResult]
        Per-layer computation details
    slab_method_calls : List[MethodCall]
        Slab-level calculations (A11, B11, D11, A55)
    A11 : Optional[UncertainValue]
        Extensional stiffness (N/mm)
    B11 : Optional[UncertainValue]
        Bending-extension coupling stiffness (N)
    D11 : Optional[UncertainValue]
        Bending stiffness (N*mm)
    A55 : Optional[UncertainValue]
        Shear stiffness (N/mm)
    """
    slab: Slab
    layer_results: List[LayerResult]
    slab_method_calls: List[MethodCall] = field(default_factory=list)
    A11: Optional[UncertainValue] = None
    B11: Optional[UncertainValue] = None
    D11: Optional[UncertainValue] = None
    A55: Optional[UncertainValue] = None


@dataclass
class PathwayResult:
    """
    Results from executing a single parameterization pathway.

    Attributes
    ----------
    pathway_id : str
        Unique identifier (e.g., "density:geldsetzer->elastic_modulus:bergfeld")
    pathway_description : str
        Human-readable description of the pathway
    methods_used : Dict[str, str]
        Mapping of parameter -> method_name used in this pathway
    layer_results : List[LayerResult]
        Layer objects with computed values
    slab_result : Optional[SlabResult]
        Slab with computed values (if slab-level requested)
    success : bool
        True if at least some values were computed
    warnings : List[str]
        Non-fatal issues encountered during execution
    """
    pathway_id: str
    pathway_description: str
    methods_used: Dict[str, str]
    layer_results: List[LayerResult]
    slab_result: Optional[SlabResult]
    success: bool
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExecutionResults:
    """
    Top-level results container for all parameterization pathways.

    This is the main return type from ExecutionEngine.execute_all().
    Results are stored in a dictionary keyed by pathway description.

    Attributes
    ----------
    target_parameter : str
        The parameter that was computed (e.g., "elastic_modulus")
    source_slab : Slab
        Original input slab (unmodified)
    results : Dict[str, PathwayResult]
        Mapping of pathway_description -> PathwayResult
    total_pathways : int
        Total number of pathways attempted
    successful_pathways : int
        Number of pathways that succeeded (at least partial results)
    failed_pathways : int
        Number of pathways that completely failed

    Examples
    --------
    >>> results = engine.execute_all(slab, "elastic_modulus")
    >>> for pathway_desc, pathway_result in results.results.items():
    ...     print(f"{pathway_desc}: {pathway_result.success}")
    """
    target_parameter: str
    source_slab: Slab
    results: Dict[str, PathwayResult]
    total_pathways: int
    successful_pathways: int
    failed_pathways: int = 0

    def __post_init__(self) -> None:
        """Calculate failed_pathways if not provided."""
        if self.failed_pathways == 0:
            self.failed_pathways = self.total_pathways - self.successful_pathways

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
        for result in self.results.values():
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
        return {k: v for k, v in self.results.items() if v.success}

    def get_all_methods_used(self) -> Dict[str, set]:
        """
        Get all unique methods used for each parameter across all pathways.

        Returns
        -------
        Dict[str, set]
            Mapping of parameter -> set of method names
        """
        methods: Dict[str, set] = {}
        for result in self.results.values():
            for param, method in result.methods_used.items():
                if param not in methods:
                    methods[param] = set()
                methods[param].add(method)
        return methods
