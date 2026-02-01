"""
Pathway executor for parameterization execution.

This module provides the PathwayExecutor class that executes a single
parameterization pathway on Layer/Slab objects.
"""

import sys
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

# Add algorithm directory to path for imports
sys.path.insert(0, '/Users/marykate/Desktop/Snow/SnowPyt-MechParams/algorithm')
from parameterization_algorithm import Parameterization, PathSegment, Branch

from snowpyt_mechparams.data_structures import Layer, Slab, UncertainValue
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher, ParameterLevel
from snowpyt_mechparams.execution.results import (
    MethodCall, LayerResult, SlabResult, PathwayResult
)


class PathwayExecutor:
    """
    Executes parameterization pathways on Layer/Slab objects.

    This class walks through a Parameterization object and executes
    each method in the pathway, computing values for layers and slabs.

    Attributes
    ----------
    dispatcher : MethodDispatcher
        The method dispatcher for executing calculations
    _cache : Dict[Tuple[int, str, str], UncertainValue]
        Cache for dynamic programming (layer_index, parameter, method) -> result
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
        self._cache: Dict[Tuple[int, str, str], UncertainValue] = {}

    def execute_parameterization(
        self,
        parameterization: Parameterization,
        slab: Slab,
        target_parameter: str,
        include_plate_theory: bool = True
    ) -> PathwayResult:
        """
        Execute a single parameterization pathway on a slab.

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
        """
        # Clear cache for fresh execution
        self._cache.clear()

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

            # Check cache first (dynamic programming)
            cache_key = (layer_index, param, method_name)
            if cache_key in self._cache:
                result = self._cache[cache_key]
                self._set_layer_parameter(working_layer, param, result)
                method_calls.append(MethodCall(
                    parameter=param,
                    method_name=method_name,
                    inputs={"cached": True},
                    output=result,
                    success=True
                ))
                continue

            # Get inputs for tracing
            inputs_used = self._get_inputs_used(working_layer, param, method_name)

            # Execute the method
            result, error = self.dispatcher.execute(
                parameter=param,
                method_name=method_name,
                layer=working_layer
            )

            if result is not None:
                # Cache the result
                self._cache[cache_key] = result
                # Update the layer
                self._set_layer_parameter(working_layer, param, result)

            method_calls.append(MethodCall(
                parameter=param,
                method_name=method_name,
                inputs=inputs_used,
                output=result,
                success=result is not None,
                failure_reason=error
            ))

        return LayerResult(
            layer=working_layer,
            method_calls=method_calls,
            layer_index=layer_index
        )

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

        These require that layers have elastic_modulus and poissons_ratio
        computed (for A11, B11, D11) and shear_modulus (for A55).

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
        """
        slab_method_calls = []

        # Calculate A11
        A11_result, A11_error = self.dispatcher.execute(
            parameter="A11",
            method_name="weissgraeber_rosendahl",
            slab=slab
        )
        slab_method_calls.append(MethodCall(
            parameter="A11",
            method_name="weissgraeber_rosendahl",
            inputs={"slab": "computed"},
            output=A11_result,
            success=A11_result is not None,
            failure_reason=A11_error
        ))

        # Calculate B11
        B11_result, B11_error = self.dispatcher.execute(
            parameter="B11",
            method_name="weissgraeber_rosendahl",
            slab=slab
        )
        slab_method_calls.append(MethodCall(
            parameter="B11",
            method_name="weissgraeber_rosendahl",
            inputs={"slab": "computed"},
            output=B11_result,
            success=B11_result is not None,
            failure_reason=B11_error
        ))

        # Calculate D11
        D11_result, D11_error = self.dispatcher.execute(
            parameter="D11",
            method_name="weissgraeber_rosendahl",
            slab=slab
        )
        slab_method_calls.append(MethodCall(
            parameter="D11",
            method_name="weissgraeber_rosendahl",
            inputs={"slab": "computed"},
            output=D11_result,
            success=D11_result is not None,
            failure_reason=D11_error
        ))

        # Calculate A55
        A55_result, A55_error = self.dispatcher.execute(
            parameter="A55",
            method_name="weissgraeber_rosendahl",
            slab=slab
        )
        slab_method_calls.append(MethodCall(
            parameter="A55",
            method_name="weissgraeber_rosendahl",
            inputs={"slab": "computed"},
            output=A55_result,
            success=A55_result is not None,
            failure_reason=A55_error
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
