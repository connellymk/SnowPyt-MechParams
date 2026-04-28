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
- **Slab Parameters**: Computes slab parameters with prerequisite checks
- **Cache Statistics**: Tracks hit/miss rates for performance analysis
- **Provenance Tracking**: Records which method computed each parameter

The executor assumes each ``Parameterization`` it receives represents a
genuinely distinct set of ``(parameter, method)`` choices.
``find_parameterizations`` guarantees this by deduplicating via
``_method_fingerprint`` before returning, so the executor never needs to
skip or merge pathway results.

Cache Strategy
--------------
The executor caches only **density** values at the layer level.

1. **Layer-level cache (density only)**: (layer_index, "density", method) -> value
   - Density depends solely on layer-intrinsic data (hand hardness, grain form,
     grain size). The same density method on the same layer always produces the
     same result regardless of which downstream methods (E, ν, G) are used.
   - Safe to share across pathways: the key ``(layer_idx, "density", method)``
     fully identifies the computation.

2. **Provenance tracking**: (layer_index, parameter) -> method_name
   - Records which method was used for each parameter.
   - Useful for understanding calculation paths.

Downstream layer parameters — elastic_modulus, poissons_ratio, and
shear_modulus — are **never cached**. Their results depend on which upstream
pathway was computed for this specific layer. In particular, shear_modulus now
depends on elastic_modulus and poissons_ratio, which may themselves depend on
different density methods across pathways. Caching these downstream values with
the key ``(layer_idx, parameter, method)`` would miss that upstream context,
causing the first pathway's E/ν/G values (and their uncertainty budgets) to be
returned for every subsequent pathway that uses the same method name but a
different upstream pathway. Always computing fresh ensures each pathway
receives the correct uncertainty budget.

Slab parameters (D11, A11, B11, A55) are **never cached** for the same
reason: they depend on the pathway-specific E/ν/G layer values. A cache key
of ``(parameter, method)`` would not encode which upstream pathway computed
the layer inputs, collapsing different uncertainty budgets into one.

The density cache persists across pathway executions for the same slab but is
cleared when moving to a new slab via clear_cache().
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from snowpyt_mechparams.pathway import Parameterization
from snowpyt_mechparams.models import Layer, Slab, UncertainValue
from snowpyt_mechparams.execution.cache import ComputationCache
from snowpyt_mechparams.execution.context import ExecutionContext
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher, _get_layer_input
from snowpyt_mechparams.execution.planner import ExecutionPlanner
from snowpyt_mechparams.execution.results import ComputationTrace, PathwayResult
from snowpyt_mechparams.methods import MethodRegistry

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
        cache: Optional[ComputationCache] = None,
        registry: Optional[MethodRegistry] = None,
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
        self.dispatcher = dispatcher or MethodDispatcher(registry)
        self.registry = self.dispatcher.registry
        self.planner = ExecutionPlanner(self.registry)
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
        config: "ExecutionConfig",
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
        methods_used = self.extract_methods_from_parameterization(parameterization)

        # Build pathway description and ID
        pathway_description = self.build_pathway_description(methods_used)
        pathway_id = self.build_pathway_id(methods_used)

        # Track all computations in a flat list
        computation_trace: List[ComputationTrace] = []
        warnings: List[str] = []

        # Determine execution order once
        execution_order = self.planner.layer_order(methods_used)

        # Build result layers using copy-on-write pattern
        # Only copy layers that need modification
        needs_computation = bool(execution_order)
        context = ExecutionContext(slab, copy_layers=needs_computation)

        for layer_idx, working_layer in context.iter_layers():
            if needs_computation:
                self._clear_layer_pathway_outputs(working_layer)

                # Execute computations on this layer
                for param in execution_order:
                    if param not in methods_used:
                        continue

                    method_name = methods_used[param]

                    # Get or compute (with caching)
                    value, was_cached, error_msg = self._get_or_compute_layer_param(
                        working_layer, layer_idx, param, method_name, config
                    )

                    # Get inputs for tracing
                    inputs_summary = {}
                    if not was_cached:
                        inputs_summary = self._get_inputs_summary(
                            working_layer, param, method_name
                        )
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
                        error=error_msg,  # Use actual error message from dispatcher
                        inputs_summary=inputs_summary,
                    )
                    computation_trace.append(trace)

        # Create result slab with computed layers
        # Use dataclasses.replace to preserve all slab attributes (metadata, weak_layer, etc.)
        # while only updating the layers list
        result_slab = context.materialize()

        # Execute slab-level calculations only when the target is a slab parameter.
        # A11, B11, D11, A55 are target parameters like any other — compute only
        # the one that was requested.
        if target_parameter in self.planner.slab_targets:
            self._clear_slab_pathway_outputs(result_slab)
            slab_traces = self._execute_slab_calculations(
                result_slab,
                target_parameter,
                methods_used,
            )
            computation_trace.extend(slab_traces)

        # Determine overall success.
        #
        # For slab-level targets, _execute_slab_calculations
        # emits exactly one trace for the requested parameter.  The filter
        # t.parameter == target_parameter isolates that trace.
        #
        # For layer-level targets (density, elastic_modulus, poissons_ratio,
        # shear_modulus) a pathway specifies exactly ONE method per parameter.
        # That method is applied independently to each layer in the slab, but
        # the SAME method is used for every layer — never srivastava for one
        # layer and kochle for another within the same pathway.
        # A partial success (method succeeded on some layers but failed on
        # others) is therefore treated as pathway failure: if the method cannot
        # produce a value for every layer, the pathway as a whole has failed.

        if target_parameter in self.planner.slab_targets:
            success = any(
                t.success and t.parameter == target_parameter for t in computation_trace
            )
        else:
            layer_target_traces = [
                t
                for t in computation_trace
                if t.parameter == target_parameter and t.layer_index is not None
            ]
            success = bool(layer_target_traces) and all(
                t.success for t in layer_target_traces
            )

        return PathwayResult(
            pathway_id=pathway_id,
            pathway_description=pathway_description,
            methods_used=methods_used,
            slab=result_slab,
            computation_trace=computation_trace,
            success=success,
            warnings=warnings,
        )

    def extract_methods_from_parameterization(
        self, parameterization: Parameterization
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
                # edge_name is None for data_flow edges
                if segment.edge_name:
                    # Has an explicit method name (e.g., "geldsetzer", "bergfeld")
                    methods[segment.to_node] = segment.edge_name
                else:
                    # edge_name is None - this is a data_flow edge
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

                # edge_name is None for data_flow edges
                if segment.edge_name:
                    # Has an explicit method name (e.g., "geldsetzer", "bergfeld")
                    methods[segment.to_node] = segment.edge_name
                else:
                    # edge_name is None - this is a data_flow edge
                    methods[segment.to_node] = "data_flow"

        return methods

    def build_pathway_description(self, methods_used: Dict[str, str]) -> str:
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
        # Preserve registry order while keeping each target only once.
        order = list(dict.fromkeys(spec.target for spec in self.registry.all()))
        parts = []
        for param in order:
            if param in methods_used:
                parts.append(f"{param}={methods_used[param]}")
        return " | ".join(parts)

    def build_pathway_id(self, methods_used: Dict[str, str]) -> str:
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
        method: str,
        config: Optional["ExecutionConfig"] = None,
    ) -> Tuple[Optional[UncertainValue], bool, Optional[str]]:
        """
        Get parameter from cache or compute it.

        Only ``density`` values are cached across pathways. Downstream
        parameters (elastic_modulus, poissons_ratio, shear_modulus) are always
        computed fresh because their values — including the uncertainty budget
        — differ depending on the upstream pathway. Caching them under
        ``(layer_idx, parameter, method)`` would silently return the first
        pathway's result for every subsequent pathway that uses the same method
        name but different upstream inputs, collapsing distinct uncertainty
        budgets into one incorrect value.

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
        Tuple[Optional[UncertainValue], bool, Optional[str]]
            (value, was_cached, error_message) - The computed/cached value, whether it came from cache,
            and error message if computation failed (None if successful or cached)
        """
        if parameter == "measured_layer_thickness" and method == "data_flow":
            return layer.thickness, False, None

        spec = self.registry.require(parameter, method)
        is_cacheable = spec.cache_scope == "layer"

        if is_cacheable:
            cached_value = self.cache.get_layer_param(layer_index, parameter, method)
            if cached_value is not None:
                self._set_layer_parameter(layer, parameter, method, cached_value)
                return cached_value, True, None

        # Compute
        extra = {}
        if config is not None and self.dispatcher.supports_method_uncertainty(
            parameter, method
        ):
            extra["include_method_uncertainty"] = config.include_method_uncertainty
        value, error = self.dispatcher.execute(
            parameter=parameter,
            method_name=method,
            layer=layer,
            slab=None,
            **extra,
        )

        if value is not None:
            if is_cacheable:
                self.cache.set_layer_param(layer_index, parameter, method, value)
            self._set_layer_parameter(layer, parameter, method, value)

        return value, False, error

    def _set_layer_parameter(
        self, layer: Layer, parameter: str, method: str, value: UncertainValue
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
        spec = self.registry.require(parameter, method)
        setattr(layer, spec.output_attr, value)

    def _clear_layer_pathway_outputs(self, layer: Layer) -> None:
        """Reset computed layer outputs before executing a pathway.

        Although ExecutionContext copies each source layer via dataclasses.replace,
        the copy inherits any pre-computed values (density_calculated, elastic_modulus,
        etc.) that were already set on the source layer. Clearing them here ensures
        each pathway computes all outputs from scratch and cannot silently reuse a
        stale value left over from a prior run stored on the input slab.
        """
        for spec in self.registry.all():
            if spec.target in self.planner.layer_targets:
                setattr(layer, spec.output_attr, None)

    def _clear_slab_pathway_outputs(self, slab: Slab) -> None:
        """Clear computed slab outputs that are recomputed per pathway."""
        for spec in self.registry.all():
            if spec.target in self.planner.slab_targets:
                setattr(slab, spec.output_attr, None)

    def _get_inputs_summary(
        self, layer: Layer, parameter: str, method_name: str
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
            value = _get_layer_input(layer, input_name, method_name=method_name)
            if value is not None:
                # Simplify ufloat for display
                if hasattr(value, "nominal_value"):
                    inputs[input_name] = (
                        f"{value.nominal_value:.2f} +/- {value.std_dev:.2f}"
                    )
                else:
                    inputs[input_name] = str(value)
        return inputs

    def _get_or_compute_slab_param(
        self, slab: Slab, parameter: str, method: str
    ) -> Tuple[Optional[UncertainValue], bool, Optional[str]]:
        """
        Compute a slab parameter (never cached).

        Slab parameters such as D11, A11, B11, and A55 are computed from the
        layer-level elastic_modulus, poissons_ratio, and shear_modulus values
        that are already set on *this pathway's* working slab copy. Those layer
        values differ between pathways (e.g. wautier vs. schottner produce
        different E values), so a slab parameter computed for one pathway is
        not valid for another.

        The layer-level cache key ``(layer_idx, parameter, method)`` correctly
        identifies reusable sub-computations. Slab parameters have no such
        stable identity across pathways — caching them would silently return
        the *first* pathway's result for all subsequent pathways on the same
        slab, collapsing uncertainty and nominal values to a single incorrect
        value.

        Parameters
        ----------
        slab : Slab
            The slab object with pathway-specific layer properties already set
        parameter : str
            Slab parameter to compute (A11, B11, D11, or A55)
        method : str
            Method to use (typically "weissgraeber_rosendahl")

        Returns
        -------
        Tuple[Optional[UncertainValue], bool, Optional[str]]
            (value, was_cached=False, error_message)
        """
        # Slab parameters are NEVER cached: each pathway produces different
        # layer-level E/ν/G values, and the slab cache key does not encode
        # which upstream methods were used. Always compute fresh.
        value, error = self.dispatcher.execute(
            parameter=parameter, method_name=method, slab=slab
        )

        if value is not None:
            spec = self.registry.require(parameter, method)
            setattr(slab, spec.output_attr, value)

        return value, False, error

    def _execute_slab_calculations(
        self,
        slab: Slab,
        target_parameter: str,
        methods_used: Optional[Dict[str, str]] = None,
    ) -> List[ComputationTrace]:
        """
        Execute the slab-level calculation for a single target parameter.

        Parameters
        ----------
        slab : Slab
            The slab with computed layer values
        target_parameter : str
            Which slab parameter to compute

        Returns
        -------
        List[ComputationTrace]
            Single-item list with the trace for the requested parameter
        """
        if methods_used is None:
            methods_used = self._default_slab_methods_for(target_parameter)
            if not methods_used:
                return []

        traces: List[ComputationTrace] = []
        for parameter in self.planner.slab_order(target_parameter, methods_used):
            method_name = methods_used[parameter]
            spec = self.registry.require(parameter, method_name)
            missing = self._missing_slab_prerequisites(slab, spec.source_nodes)
            if missing:
                traces.append(
                    ComputationTrace(
                        parameter=parameter,
                        method_name=method_name,
                        layer_index=None,
                        output=None,
                        success=False,
                        cached=False,
                        error=f"Missing prerequisites: need {', '.join(missing)}",
                    )
                )
                if parameter == target_parameter:
                    return traces
                continue

            value, was_cached, error_msg = self._get_or_compute_slab_param(
                slab,
                parameter,
                method_name,
            )
            traces.append(
                ComputationTrace(
                    parameter=parameter,
                    method_name=method_name,
                    layer_index=None,
                    output=value,
                    success=value is not None,
                    cached=was_cached,
                    error=error_msg,
                )
            )
            if value is None and parameter == target_parameter:
                return traces

        return traces

    def _default_slab_methods_for(self, target_parameter: str) -> Dict[str, str]:
        """Return default slab methods for a target and its slab prerequisites."""
        methods: Dict[str, str] = {}

        def add(parameter: str) -> None:
            if parameter in methods:
                return
            spec = self.registry.default_method_for(parameter)
            if spec is None:
                return
            for source in spec.source_nodes:
                if source in self.planner.slab_targets:
                    add(source)
            methods[parameter] = spec.method_name

        add(target_parameter)
        return methods

    def _missing_slab_prerequisites(
        self,
        slab: Slab,
        source_nodes: Tuple[str, ...],
    ) -> List[str]:
        """Return human-readable missing prerequisites for a slab method."""
        missing: List[str] = []
        for source in source_nodes:
            if source == "measured_layer_thickness":
                if not all(layer.thickness is not None for layer in slab.layers):
                    missing.append("thickness on all layers")
            elif source == "measured_slope_angle":
                if slab.angle is None:
                    missing.append("slope angle")
            elif source == "density":
                if not all(
                    layer.density_calculated is not None for layer in slab.layers
                ):
                    missing.append("computed density on all layers")
            elif source == "elastic_modulus":
                if not all(layer.elastic_modulus is not None for layer in slab.layers):
                    missing.append("E on all layers")
            elif source == "poissons_ratio":
                if not all(layer.poissons_ratio is not None for layer in slab.layers):
                    missing.append("nu on all layers")
            elif source == "shear_modulus":
                if not all(layer.shear_modulus is not None for layer in slab.layers):
                    missing.append("G on all layers")
            elif source in self.planner.slab_targets:
                spec = self.registry.default_method_for(source)
                attr = spec.output_attr if spec is not None else source
                if getattr(slab, attr, None) is None:
                    missing.append(source)
        return missing
