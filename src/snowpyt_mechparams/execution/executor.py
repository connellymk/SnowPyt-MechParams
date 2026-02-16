"""
Pathway executor for parameterization execution.

This module provides the PathwayExecutor class that executes parameterization
pathways on Layer/Slab objects. The executor implements dynamic programming
by caching computed values across pathway executions for the same slab,
significantly reducing redundant calculations.

Key Features
------------
- **Dynamic Programming**: Persistent cache across pathways for same slab
- **Layer Properties**: Handles thickness as direct data flow (no calculation)
- **Slab Parameters**: Computes A11, B11, D11, A55 with prerequisite checks
- **Cache Statistics**: Tracks hit/miss rates for performance analysis
- **Provenance Tracking**: Records which method computed each parameter

Cache Strategy
--------------
The executor maintains three types of caches:

1. **Layer-level cache**: (layer_index, parameter, method) -> value
   - Caches computed layer parameters across pathways
   - Cleared between different slabs

2. **Slab-level cache**: (parameter, method) -> value
   - Caches computed slab parameters
   - Cleared between different slabs

3. **Provenance tracking**: (layer_index, parameter) -> method_name
   - Records which method was used for each parameter
   - Useful for understanding calculation paths

The cache persists across pathway executions for the same slab but is
cleared when moving to a new slab via clear_cache().
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from snowpyt_mechparams.algorithm import Parameterization
from snowpyt_mechparams.data_structures import Layer, Slab, UncertainValue
from snowpyt_mechparams.execution.cache import ComputationCache
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher, ParameterLevel
from snowpyt_mechparams.execution.results import (
    ComputationTrace, PathwayResult
)

if TYPE_CHECKING:
    from snowpyt_mechparams.execution.config import ExecutionConfig


class PathwayExecutor:
    """
    Executes parameterization pathways on Layer/Slab objects.

    This class walks through Parameterization objects and executes each method
    in the pathway, computing values for layers and slabs. Uses a dedicated
    ComputationCache for dynamic programming across pathways.

    Attributes
    ----------
    dispatcher : MethodDispatcher
        The method dispatcher for executing calculations
    cache : ComputationCache
        Cache for storing computed values across pathways

    Notes
    -----
    The cache persists across pathway executions for the same slab,
    enabling dynamic programming. Call clear_cache() when switching
    to a new slab.
    """

    def __init__(
        self,
        dispatcher: Optional[MethodDispatcher] = None,
        cache: Optional[ComputationCache] = None
    ):
        """
        Initialize the PathwayExecutor.

        Parameters
        ----------
        dispatcher : Optional[MethodDispatcher]
            Method dispatcher to use. If None, creates a new one.
        cache : Optional[ComputationCache]
            Computation cache to use. If None, creates a new one.
        """
        self.dispatcher = dispatcher or MethodDispatcher()
        self.cache = cache or ComputationCache()
    
    def clear_cache(self) -> None:
        """
        Clear the computation cache.
        
        Call this when switching to a new slab to ensure cached values
        don't carry over between different slabs.
        """
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, float]:
        """
        Get cache performance statistics.
        
        Returns
        -------
        Dict[str, float]
            Dictionary with keys 'hits', 'misses', 'hit_rate'
        """
        return self.cache.get_stats().to_dict()

    def execute_parameterization(
        self,
        parameterization: Parameterization,
        slab: Slab,
        target_parameter: str,
        config: 'ExecutionConfig'
    ) -> PathwayResult:
        """
        Execute a single parameterization pathway on a slab.

        This method does NOT clear the cache, allowing dynamic programming
        across multiple pathway executions for the same slab. Call clear_cache()
        when switching to a new slab.

        Parameters
        ----------
        parameterization : Parameterization
            The pathway to execute (from find_parameterizations)
        slab : Slab
            The input slab with measured values
        target_parameter : str
            The target parameter to compute (e.g., "elastic_modulus")
        config : ExecutionConfig
            Configuration controlling execution behavior

        Returns
        -------
        PathwayResult
            Results containing computed layers/slab and pathway trace

        Notes
        -----
        The cache persists across pathway executions to enable dynamic
        programming. When multiple pathways share common subpaths, the
        cached values avoid redundant calculations.
        """
        # DO NOT clear cache - this enables dynamic programming across pathways
        # Only clear cache when switching to a new slab (via clear_cache())

        # Extract the methods used from the parameterization
        methods_used = self._extract_methods_from_parameterization(parameterization)

        # Build pathway description and ID
        pathway_description = self._build_pathway_description(methods_used)
        pathway_id = self._build_pathway_id(methods_used)

        # Track all computations in a flat list
        computation_trace: List[ComputationTrace] = []
        warnings: List[str] = []

        # Determine execution order once
        execution_order = self._determine_execution_order(target_parameter, methods_used)

        # Build result layers using copy-on-write pattern
        # Only copy layers that need modification
        result_layers: List[Layer] = []

        for layer_idx, original_layer in enumerate(slab.layers):
            # Check if this layer needs any computation
            needs_computation = any(param in methods_used for param in execution_order)
            
            if needs_computation:
                # This layer needs computation - create a shallow copy
                # (Using dataclass replace is faster than deepcopy)
                from dataclasses import replace
                working_layer = replace(original_layer)
                
                # Execute computations on this layer
                for param in execution_order:
                    if param not in methods_used:
                        continue
                    
                    method_name = methods_used[param]
                    
                    # Get or compute (with caching)
                    value, was_cached = self._get_or_compute_layer_param(
                        working_layer, layer_idx, param, method_name
                    )
                    
                    # Get inputs for tracing
                    inputs_summary = {}
                    if not was_cached:
                        inputs_summary = self._get_inputs_summary(working_layer, param, method_name)
                    else:
                        inputs_summary = {"cached": True}
                    
                    # Create trace
                    trace = ComputationTrace(
                        parameter=param,
                        method_name=method_name,
                        layer_index=layer_idx,
                        output=value,
                        success=value is not None,
                        cached=was_cached,
                        error=None if value is not None else "Computation failed",
                        inputs_summary=inputs_summary
                    )
                    computation_trace.append(trace)
                
                result_layers.append(working_layer)
            else:
                # No computation needed - reuse original layer
                result_layers.append(original_layer)

        # Create result slab with computed layers
        # Shallow copy the slab with new layers (fast!)
        result_slab = Slab(
            layers=result_layers,
            angle=slab.angle
        )

        # Execute slab-level calculations if target requires them
        # The algorithm only includes slab parameters in the parameterization
        # if they're needed to reach the target, so we always execute them
        slab_traces = self._execute_slab_calculations_v2(result_slab)
        computation_trace.extend(slab_traces)

        # Determine overall success
        # Success if at least one computation of the target parameter succeeded
        success = any(
            t.success and t.parameter == target_parameter 
            for t in computation_trace
        )

        return PathwayResult(
            pathway_id=pathway_id,
            pathway_description=pathway_description,
            methods_used=methods_used,
            slab=result_slab,
            computation_trace=computation_trace,
            success=success,
            warnings=warnings
        )

    def _extract_methods_from_parameterization(
        self,
        parameterization: Parameterization
    ) -> Dict[str, str]:
        """
        Extract parameter -> method mapping from a Parameterization.

        Walks through the branches and merge points to identify
        which method is used for each parameter.

        Parameters
        ----------
        parameterization : Parameterization
            The parameterization to extract from

        Returns
        -------
        Dict[str, str]
            Mapping of parameter name to method name
        """
        methods: Dict[str, str] = {}

        # Process branches
        for branch in parameterization.branches:
            for segment in branch.segments:
                # Skip measured_ nodes (they're inputs, not outputs)
                if segment.to_node.startswith("measured_"):
                    continue
                # Skip merge nodes
                if segment.to_node.startswith("merge_"):
                    continue
                # Skip snow_pit
                if segment.to_node == "snow_pit":
                    continue

                # The to_node is the parameter, edge_name is the method
                if segment.edge_name and segment.edge_name != "data_flow":
                    methods[segment.to_node] = segment.edge_name
                elif segment.edge_name == "data_flow":
                    methods[segment.to_node] = "data_flow"

        # Process merge point continuations
        for branch_indices, merge_node, continuation in parameterization.merge_points:
            for segment in continuation:
                # Skip measured_ nodes
                if segment.to_node.startswith("measured_"):
                    continue
                # Skip merge nodes
                if segment.to_node.startswith("merge_"):
                    continue
                # Skip snow_pit
                if segment.to_node == "snow_pit":
                    continue

                if segment.edge_name and segment.edge_name != "data_flow":
                    methods[segment.to_node] = segment.edge_name
                elif segment.edge_name == "data_flow":
                    methods[segment.to_node] = "data_flow"

        return methods

    def _build_pathway_description(self, methods_used: Dict[str, str]) -> str:
        """
        Build a human-readable description of the pathway.

        Parameters
        ----------
        methods_used : Dict[str, str]
            Mapping of parameter to method name

        Returns
        -------
        str
            Human-readable pathway description
        """
        # Order: density -> elastic_modulus -> poissons_ratio -> shear_modulus
        order = ["density", "elastic_modulus", "poissons_ratio", "shear_modulus"]
        parts = []
        for param in order:
            if param in methods_used:
                parts.append(f"{param}={methods_used[param]}")
        return " | ".join(parts)

    def _build_pathway_id(self, methods_used: Dict[str, str]) -> str:
        """
        Build a unique identifier for the pathway.

        Parameters
        ----------
        methods_used : Dict[str, str]
            Mapping of parameter to method name

        Returns
        -------
        str
            Unique pathway identifier
        """
        sorted_items = sorted(methods_used.items())
        return "->".join(f"{p}:{m}" for p, m in sorted_items)

    def _get_or_compute_layer_param(
        self,
        layer: Layer,
        layer_index: int,
        parameter: str,
        method: str
    ) -> Tuple[Optional[UncertainValue], bool]:
        """
        Get parameter from cache or compute it.

        Handles special cases for layer properties (thickness) which are
        direct data flow and require no calculation.

        Parameters
        ----------
        layer : Layer
            The layer object
        layer_index : int
            Index of this layer
        parameter : str
            Parameter to compute
        method : str
            Method to use

        Returns
        -------
        Tuple[Optional[UncertainValue], bool]
            (value, was_cached) - The computed/cached value and whether it came from cache
        """
        # Special handling for layer properties (direct data flow)
        if parameter == "layer_thickness":
            # Direct from layer.thickness - no calculation needed
            return layer.thickness, False

        # Check cache first
        cached_value = self.cache.get_layer_param(layer_index, parameter, method)
        if cached_value is not None:
            # Update the layer with cached value
            self._set_layer_parameter(layer, parameter, cached_value)
            return cached_value, True

        # Compute and store
        value, error = self.dispatcher.execute(
            parameter=parameter,
            method_name=method,
            layer=layer
        )

        if value is not None:
            self.cache.set_layer_param(layer_index, parameter, method, value)
            # Update the layer
            self._set_layer_parameter(layer, parameter, value)

        return value, False

    def _determine_execution_order(
        self,
        target_parameter: str,
        methods_used: Dict[str, str]
    ) -> List[str]:
        """
        Determine the order in which parameters should be computed.

        Based on the dependency graph:
        - density has no dependencies (measured or calculated from hardness/grain)
        - elastic_modulus depends on density
        - poissons_ratio may depend on density (srivastava) or not (kochle)
        - shear_modulus depends on density

        Parameters
        ----------
        target_parameter : str
            The ultimate target parameter
        methods_used : Dict[str, str]
            Mapping of parameter to method name

        Returns
        -------
        List[str]
            Ordered list of parameters to compute
        """
        # Always compute in dependency order
        order = []

        # Density first (if in pathway)
        if "density" in methods_used:
            order.append("density")

        # Then the others (they may depend on density)
        for param in ["elastic_modulus", "poissons_ratio", "shear_modulus"]:
            if param in methods_used:
                order.append(param)

        return order

    def _set_layer_parameter(
        self,
        layer: Layer,
        parameter: str,
        value: UncertainValue
    ) -> None:
        """
        Set a computed parameter value on a layer.

        Parameters
        ----------
        layer : Layer
            The layer to update
        parameter : str
            The parameter name
        value : UncertainValue
            The computed value
        """
        if parameter == "density":
            layer.density_calculated = value
        elif parameter == "elastic_modulus":
            layer.elastic_modulus = value
        elif parameter == "poissons_ratio":
            layer.poissons_ratio = value
        elif parameter == "shear_modulus":
            layer.shear_modulus = value

    def _get_inputs_summary(
        self,
        layer: Layer,
        parameter: str,
        method_name: str
    ) -> Dict[str, Any]:
        """
        Get a summary of inputs used for a calculation (for tracing).

        Parameters
        ----------
        layer : Layer
            The layer to extract inputs from
        parameter : str
            The target parameter
        method_name : str
            The method name

        Returns
        -------
        Dict[str, Any]
            Dictionary of input values (for traceability)
        """
        spec = self.dispatcher.get_method(parameter, method_name)
        if spec is None:
            return {}

        inputs = {}
        for input_name in spec.required_inputs:
            from snowpyt_mechparams.execution.dispatcher import _get_layer_input
            value = _get_layer_input(layer, input_name, method_name=method_name)
            if value is not None:
                # Simplify ufloat for display
                if hasattr(value, 'nominal_value'):
                    inputs[input_name] = f"{value.nominal_value:.2f} +/- {value.std_dev:.2f}"
                else:
                    inputs[input_name] = str(value)
        return inputs

    def _get_or_compute_slab_param(
        self,
        slab: Slab,
        parameter: str,
        method: str
    ) -> Tuple[Optional[UncertainValue], bool]:
        """
        Get slab parameter from cache or compute it.

        Parameters
        ----------
        slab : Slab
            The slab object with computed layer properties
        parameter : str
            Slab parameter to compute (A11, B11, D11, or A55)
        method : str
            Method to use (typically "weissgraeber_rosendahl")

        Returns
        -------
        Tuple[Optional[UncertainValue], bool]
            (value, was_cached) - The computed/cached value and whether it came from cache
        """
        # Check cache
        cached_value = self.cache.get_slab_param(parameter, method)
        if cached_value is not None:
            # Update the slab with cached value
            setattr(slab, parameter, cached_value)
            return cached_value, True

        # Compute
        value, error = self.dispatcher.execute(
            parameter=parameter,
            method_name=method,
            slab=slab
        )

        if value is not None:
            self.cache.set_slab_param(parameter, method, value)
            # Update the slab
            setattr(slab, parameter, value)

        return value, False

    def _execute_slab_calculations_v2(
        self,
        slab: Slab
    ) -> List[ComputationTrace]:
        """
        Execute slab-level calculations and return computation traces.

        This is the new simplified version that returns a flat list of 
        ComputationTrace objects instead of a nested SlabResult.

        Parameters
        ----------
        slab : Slab
            The slab with computed layer values

        Returns
        -------
        List[ComputationTrace]
            List of slab-level computation traces
        """
        traces: List[ComputationTrace] = []

        # Check prerequisites for each slab parameter
        all_layers_have_thickness = all(
            layer.thickness is not None
            for layer in slab.layers
        )

        # A11, B11, D11: Require E and ν on all layers
        can_compute_A11_B11_D11 = (
            all_layers_have_thickness and
            all(layer.elastic_modulus is not None for layer in slab.layers) and
            all(layer.poissons_ratio is not None for layer in slab.layers)
        )

        # A55: Requires G on all layers
        can_compute_A55 = (
            all_layers_have_thickness and
            all(layer.shear_modulus is not None for layer in slab.layers)
        )

        # Compute A11 if possible
        if can_compute_A11_B11_D11:
            value, was_cached = self._get_or_compute_slab_param(
                slab, "A11", "weissgraeber_rosendahl"
            )
            traces.append(ComputationTrace(
                parameter="A11",
                method_name="weissgraeber_rosendahl",
                layer_index=None,  # Slab-level
                output=value,
                success=value is not None,
                cached=was_cached,
                error=None if value is not None else "Computation failed"
            ))
        else:
            traces.append(ComputationTrace(
                parameter="A11",
                method_name="weissgraeber_rosendahl",
                layer_index=None,
                output=None,
                success=False,
                cached=False,
                error="Missing prerequisites: need E, ν, and thickness on all layers"
            ))

        # Compute B11 if possible
        if can_compute_A11_B11_D11:
            value, was_cached = self._get_or_compute_slab_param(
                slab, "B11", "weissgraeber_rosendahl"
            )
            traces.append(ComputationTrace(
                parameter="B11",
                method_name="weissgraeber_rosendahl",
                layer_index=None,
                output=value,
                success=value is not None,
                cached=was_cached,
                error=None if value is not None else "Computation failed"
            ))
        else:
            traces.append(ComputationTrace(
                parameter="B11",
                method_name="weissgraeber_rosendahl",
                layer_index=None,
                output=None,
                success=False,
                cached=False,
                error="Missing prerequisites: need E, ν, and thickness on all layers"
            ))

        # Compute D11 if possible
        if can_compute_A11_B11_D11:
            value, was_cached = self._get_or_compute_slab_param(
                slab, "D11", "weissgraeber_rosendahl"
            )
            traces.append(ComputationTrace(
                parameter="D11",
                method_name="weissgraeber_rosendahl",
                layer_index=None,
                output=value,
                success=value is not None,
                cached=was_cached,
                error=None if value is not None else "Computation failed"
            ))
        else:
            traces.append(ComputationTrace(
                parameter="D11",
                method_name="weissgraeber_rosendahl",
                layer_index=None,
                output=None,
                success=False,
                cached=False,
                error="Missing prerequisites: need E, ν, and thickness on all layers"
            ))

        # Compute A55 if possible
        if can_compute_A55:
            value, was_cached = self._get_or_compute_slab_param(
                slab, "A55", "weissgraeber_rosendahl"
            )
            traces.append(ComputationTrace(
                parameter="A55",
                method_name="weissgraeber_rosendahl",
                layer_index=None,
                output=value,
                success=value is not None,
                cached=was_cached,
                error=None if value is not None else "Computation failed"
            ))
        else:
            traces.append(ComputationTrace(
                parameter="A55",
                method_name="weissgraeber_rosendahl",
                layer_index=None,
                output=None,
                success=False,
                cached=False,
                error="Missing prerequisites: need G and thickness on all layers"
            ))

        return traces
