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

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from snowpyt_mechparams.algorithm import Parameterization, PathSegment, Branch
from snowpyt_mechparams.data_structures import Layer, Slab, UncertainValue
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher, ParameterLevel
from snowpyt_mechparams.execution.results import (
    MethodCall, LayerResult, SlabResult, PathwayResult
)


class PathwayExecutor:
    """
    Executes parameterization pathways on Layer/Slab objects.

    This class walks through Parameterization objects and executes each method
    in the pathway, computing values for layers and slabs. Implements dynamic
    programming by caching computed values across pathways for the same slab.

    Attributes
    ----------
    dispatcher : MethodDispatcher
        The method dispatcher for executing calculations
    _layer_cache : Dict[Tuple[int, str, str], UncertainValue]
        Layer-level cache: (layer_index, parameter, method) -> value
    _slab_cache : Dict[Tuple[str, str], UncertainValue]
        Slab-level cache: (parameter, method) -> value
    _layer_provenance : Dict[Tuple[int, str], str]
        Provenance tracking: (layer_index, parameter) -> method_name
    _cache_hits : int
        Number of cache hits (for statistics)
    _cache_misses : int
        Number of cache misses (for statistics)

    Notes
    -----
    The cache persists across pathway executions for the same slab,
    enabling dynamic programming. Call clear_cache() when switching
    to a new slab.
    """

    def __init__(self, dispatcher: Optional[MethodDispatcher] = None):
        """
        Initialize the PathwayExecutor.

        Parameters
        ----------
        dispatcher : Optional[MethodDispatcher]
            Method dispatcher to use. If None, creates a new one.
        """
        self.dispatcher = dispatcher or MethodDispatcher()
        
        # Layer-level cache: (layer_index, parameter, method) -> value
        self._layer_cache: Dict[Tuple[int, str, str], UncertainValue] = {}
        
        # Slab-level cache: (parameter, method) -> value
        self._slab_cache: Dict[Tuple[str, str], UncertainValue] = {}
        
        # Provenance tracking: (layer_index, parameter) -> method_name
        self._layer_provenance: Dict[Tuple[int, str], str] = {}
        
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
    
    def clear_cache(self) -> None:
        """
        Clear all caches and statistics.
        
        Call this when switching to a new slab to ensure caches don't
        carry over between different slabs.
        """
        self._layer_cache.clear()
        self._slab_cache.clear()
        self._layer_provenance.clear()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_cache_stats(self) -> Dict[str, float]:
        """
        Get cache performance statistics.
        
        Returns
        -------
        Dict[str, float]
            Dictionary with keys 'hits', 'misses', 'hit_rate'
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0
        
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': hit_rate
        }

    def execute_parameterization(
        self,
        parameterization: Parameterization,
        slab: Slab,
        target_parameter: str,
        include_plate_theory: bool = True
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
        include_plate_theory : bool
            Whether to also compute A11, B11, D11, A55 after layer params

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

        # Deep copy the slab so we don't modify the original
        working_slab = deepcopy(slab)

        # Extract the methods used from the parameterization
        methods_used = self._extract_methods_from_parameterization(parameterization)

        # Build pathway description and ID
        pathway_description = self._build_pathway_description(methods_used)
        pathway_id = self._build_pathway_id(methods_used)

        # Execute layer-level calculations
        layer_results = []
        warnings = []

        for layer_idx, layer in enumerate(working_slab.layers):
            layer_result = self._execute_layer_pathway(
                layer=layer,
                layer_index=layer_idx,
                methods_used=methods_used,
                target_parameter=target_parameter
            )
            layer_results.append(layer_result)

            # Update the working slab's layer with computed values
            working_slab.layers[layer_idx] = layer_result.layer

        # Execute slab-level calculations if requested
        slab_result = None
        if include_plate_theory:
            slab_result = self._execute_slab_calculations(working_slab, layer_results)

        # Determine overall success
        # Success if at least one layer has the target parameter computed
        success = self._check_success(layer_results, target_parameter)

        return PathwayResult(
            pathway_id=pathway_id,
            pathway_description=pathway_description,
            methods_used=methods_used,
            layer_results=layer_results,
            slab_result=slab_result,
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

    def _execute_layer_pathway(
        self,
        layer: Layer,
        layer_index: int,
        methods_used: Dict[str, str],
        target_parameter: str
    ) -> LayerResult:
        """
        Execute the pathway for a single layer.

        This method walks through the dependency chain and computes
        each parameter in order, respecting the methods_used mapping.

        Parameters
        ----------
        layer : Layer
            The layer to compute values for (will be modified)
        layer_index : int
            Index of this layer in the slab
        methods_used : Dict[str, str]
            Mapping of parameter to method name
        target_parameter : str
            The target parameter to compute

        Returns
        -------
        LayerResult
            Layer with computed values and method call trace
        """
        working_layer = deepcopy(layer)
        method_calls = []

        # Determine execution order based on dependencies
        # density -> elastic_modulus (needs density)
        # density -> poissons_ratio (some methods need density)
        # density -> shear_modulus (needs density)
        execution_order = self._determine_execution_order(target_parameter, methods_used)

        for param in execution_order:
            if param not in methods_used:
                continue

            method_name = methods_used[param]

            # Use get_or_compute helper for caching and statistics
            result, was_cached = self._get_or_compute_layer_param(
                working_layer,
                layer_index,
                param,
                method_name
            )

            # Get inputs for tracing
            inputs_used = self._get_inputs_used(working_layer, param, method_name) if not was_cached else {"cached": True}

            method_calls.append(MethodCall(
                parameter=param,
                method_name=method_name,
                inputs=inputs_used,
                output=result,
                success=result is not None,
                failure_reason=None if result is not None else "Computation failed"
            ))

        return LayerResult(
            layer=working_layer,
            method_calls=method_calls,
            layer_index=layer_index
        )

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

        cache_key = (layer_index, parameter, method)

        # Check cache first
        if cache_key in self._layer_cache:
            self._cache_hits += 1
            value = self._layer_cache[cache_key]
            # Update the layer with cached value
            self._set_layer_parameter(layer, parameter, value)
            return value, True

        # Compute and store
        self._cache_misses += 1
        value, error = self.dispatcher.execute(
            parameter=parameter,
            method_name=method,
            layer=layer
        )

        if value is not None:
            self._layer_cache[cache_key] = value
            self._layer_provenance[(layer_index, parameter)] = method
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

    def _get_inputs_used(
        self,
        layer: Layer,
        parameter: str,
        method_name: str
    ) -> Dict[str, Any]:
        """
        Get the inputs that were used for a calculation (for tracing).

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
            value = _get_layer_input(layer, input_name)
            if value is not None:
                # Simplify ufloat for display
                if hasattr(value, 'nominal_value'):
                    inputs[input_name] = f"{value.nominal_value:.2f} +/- {value.std_dev:.2f}"
                else:
                    inputs[input_name] = value
        return inputs

    def _execute_slab_calculations(
        self,
        slab: Slab,
        layer_results: List[LayerResult]
    ) -> SlabResult:
        """
        Execute slab-level calculations (plate theory parameters).

        Slab parameters require all layers to have certain properties:
        - A11, B11, D11: thickness + elastic_modulus + poissons_ratio
        - A55: thickness + shear_modulus

        This method checks prerequisites before attempting each calculation.

        Parameters
        ----------
        slab : Slab
            The slab with computed layer values
        layer_results : List[LayerResult]
            The layer results from layer-level execution

        Returns
        -------
        SlabResult
            Slab result with plate theory parameters

        Notes
        -----
        Uses caching to avoid redundant calculations if slab parameters
        were already computed in a previous pathway.
        """
        slab_method_calls = []

        # Check layer properties availability (always available if layer exists)
        all_layers_have_thickness = all(
            lr.layer.thickness is not None
            for lr in layer_results
        )

        # Check if we can compute each slab parameter

        # A11, B11, D11: Require E and ν on all layers, plus thickness
        can_compute_A11_B11_D11 = (
            all_layers_have_thickness and
            all(lr.layer.elastic_modulus is not None for lr in layer_results) and
            all(lr.layer.poissons_ratio is not None for lr in layer_results)
        )

        # A55: Requires G on all layers, plus thickness
        can_compute_A55 = (
            all_layers_have_thickness and
            all(lr.layer.shear_modulus is not None for lr in layer_results)
        )

        # Compute A11 if possible
        if can_compute_A11_B11_D11:
            A11_result, A11_was_cached = self._get_or_compute_slab_param(
                slab, "A11", "weissgraeber_rosendahl"
            )
            slab_method_calls.append(MethodCall(
                parameter="A11",
                method_name="weissgraeber_rosendahl",
                inputs={"cached": True} if A11_was_cached else {"slab": "computed"},
                output=A11_result,
                success=A11_result is not None,
                failure_reason=None if A11_result is not None else "Computation failed"
            ))
        else:
            A11_result = None
            slab_method_calls.append(MethodCall(
                parameter="A11",
                method_name="weissgraeber_rosendahl",
                inputs={},
                output=None,
                success=False,
                failure_reason="Missing prerequisites: need E, ν, and thickness on all layers"
            ))

        # Compute B11 if possible
        if can_compute_A11_B11_D11:
            B11_result, B11_was_cached = self._get_or_compute_slab_param(
                slab, "B11", "weissgraeber_rosendahl"
            )
            slab_method_calls.append(MethodCall(
                parameter="B11",
                method_name="weissgraeber_rosendahl",
                inputs={"cached": True} if B11_was_cached else {"slab": "computed"},
                output=B11_result,
                success=B11_result is not None,
                failure_reason=None if B11_result is not None else "Computation failed"
            ))
        else:
            B11_result = None
            slab_method_calls.append(MethodCall(
                parameter="B11",
                method_name="weissgraeber_rosendahl",
                inputs={},
                output=None,
                success=False,
                failure_reason="Missing prerequisites: need E, ν, and thickness on all layers"
            ))

        # Compute D11 if possible
        if can_compute_A11_B11_D11:
            D11_result, D11_was_cached = self._get_or_compute_slab_param(
                slab, "D11", "weissgraeber_rosendahl"
            )
            slab_method_calls.append(MethodCall(
                parameter="D11",
                method_name="weissgraeber_rosendahl",
                inputs={"cached": True} if D11_was_cached else {"slab": "computed"},
                output=D11_result,
                success=D11_result is not None,
                failure_reason=None if D11_result is not None else "Computation failed"
            ))
        else:
            D11_result = None
            slab_method_calls.append(MethodCall(
                parameter="D11",
                method_name="weissgraeber_rosendahl",
                inputs={},
                output=None,
                success=False,
                failure_reason="Missing prerequisites: need E, ν, and thickness on all layers"
            ))

        # Compute A55 if possible
        if can_compute_A55:
            A55_result, A55_was_cached = self._get_or_compute_slab_param(
                slab, "A55", "weissgraeber_rosendahl"
            )
            slab_method_calls.append(MethodCall(
                parameter="A55",
                method_name="weissgraeber_rosendahl",
                inputs={"cached": True} if A55_was_cached else {"slab": "computed"},
                output=A55_result,
                success=A55_result is not None,
                failure_reason=None if A55_result is not None else "Computation failed"
            ))
        else:
            A55_result = None
            slab_method_calls.append(MethodCall(
                parameter="A55",
                method_name="weissgraeber_rosendahl",
                inputs={},
                output=None,
                success=False,
                failure_reason="Missing prerequisites: need G and thickness on all layers"
            ))

        return SlabResult(
            slab=slab,
            layer_results=layer_results,
            slab_method_calls=slab_method_calls,
            A11=A11_result,
            B11=B11_result,
            D11=D11_result,
            A55=A55_result
        )

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
        cache_key = (parameter, method)

        # Check cache
        if cache_key in self._slab_cache:
            self._cache_hits += 1
            value = self._slab_cache[cache_key]
            # Update the slab with cached value
            setattr(slab, parameter, value)
            return value, True

        # Compute
        self._cache_misses += 1
        value, error = self.dispatcher.execute(
            parameter=parameter,
            method_name=method,
            slab=slab
        )

        if value is not None:
            self._slab_cache[cache_key] = value
            # Update the slab
            setattr(slab, parameter, value)

        return value, False

    def _check_success(
        self,
        layer_results: List[LayerResult],
        target_parameter: str
    ) -> bool:
        """
        Check if the pathway execution was successful.

        Success is defined as at least one layer having the target
        parameter computed.

        Parameters
        ----------
        layer_results : List[LayerResult]
            The layer results from execution
        target_parameter : str
            The target parameter to check

        Returns
        -------
        bool
            True if at least one layer has the target parameter computed
        """
        for lr in layer_results:
            layer = lr.layer
            value = None
            if target_parameter == "density":
                value = layer.density_calculated
            elif target_parameter == "elastic_modulus":
                value = layer.elastic_modulus
            elif target_parameter == "poissons_ratio":
                value = layer.poissons_ratio
            elif target_parameter == "shear_modulus":
                value = layer.shear_modulus

            if value is not None:
                return True

        return False
