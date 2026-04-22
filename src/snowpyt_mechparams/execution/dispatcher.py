"""
Method dispatcher for parameterization execution.

This module provides the MethodDispatcher class that maps method names from
the parameterization graph to actual calculation function implementations.
"""

import inspect
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from uncertainties import ufloat, umath

from snowpyt_mechparams.constants import resolve_grain_form_for_method
from snowpyt_mechparams.models import Layer, Slab, UncertainValue
from snowpyt_mechparams.layer_parameters.density import calculate_density
from snowpyt_mechparams.layer_parameters.elastic_modulus import calculate_elastic_modulus
from snowpyt_mechparams.layer_parameters.poissons_ratio import calculate_poissons_ratio
from snowpyt_mechparams.layer_parameters.shear_modulus import calculate_shear_modulus
from snowpyt_mechparams.slab_parameters.extensional_stiffness import calculate_A11
from snowpyt_mechparams.slab_parameters.bending_extension_coupling import calculate_B11
from snowpyt_mechparams.slab_parameters.bending_stiffness import calculate_D11
from snowpyt_mechparams.slab_parameters.shear_stiffness import calculate_A55
from snowpyt_mechparams.constants import g


class ParameterLevel(Enum):
    """Whether a parameter is computed per-layer, per-slab, or by a legacy graph level."""
    LAYER = "layer"
    SLAB = "slab"
    WEAK_LAYER = "weak_layer"
    STABILITY = "stability_model"


@dataclass
class MethodSpec:
    """
    Specification for a calculation method.

    Attributes
    ----------
    parameter : str
        Target parameter name (e.g., "density", "elastic_modulus")
    method_name : str
        Method name (matches graph edge names)
    level : ParameterLevel
        Whether this is a layer-level or slab-level calculation
    function : Callable
        The actual implementation function
    required_inputs : List[str]
        Input parameter names required from the layer/slab
    optional_inputs : Dict[str, Any]
        Optional parameters with default values
    """
    parameter: str
    method_name: str
    level: ParameterLevel
    function: Callable
    required_inputs: List[str]
    optional_inputs: Dict[str, Any]


# Mapping from graph input names to Layer attribute names
LAYER_INPUT_MAPPING = {
    "density_measured": "density_measured",
    "density": "_resolve_density",  # Special: prefer calculated, fallback to measured
    "hand_hardness_index": "hand_hardness_index",
    "grain_form": "_resolve_grain_form",  # Special: method-specific resolution
    "grain_size": "grain_size_avg",
    "poissons_ratio": "poissons_ratio",
    "elastic_modulus": "elastic_modulus",
    "shear_modulus": "shear_modulus",
}


# Note: Valid grain form codes for each density method are defined in
# constants.GRAIN_FORM_METHODS and accessed via the resolve_grain_form_for_method()
# utility function.


def _resolve_density(layer: Layer) -> Optional[UncertainValue]:
    """
    Resolve the density value to use for calculations.

    Priority:
    1. density_calculated (if set by a previous step in the pathway)
    2. density_measured (direct measurement)

    Parameters
    ----------
    layer : Layer
        The layer to extract density from

    Returns
    -------
    Optional[UncertainValue]
        The resolved density value, or None if not available
    """
    if layer.density_calculated is not None:
        return layer.density_calculated
    if layer.density_measured is not None:
        # Wrap in ufloat if not already
        val = layer.density_measured
        if isinstance(val, (int, float)):
            return ufloat(float(val), 0.0)
        return val
    return None


def _resolve_grain_form(layer: Layer, method_name: Optional[str] = None) -> Optional[str]:
    """
    Resolve the grain form code to use for calculations.

    For density methods, uses method-specific grain code sets to determine
    whether to use sub-grain class code (more specific) or basic grain class code.
    
    The grain_form attribute can contain either:
    - A 2-character basic grain class code (e.g., 'RG', 'FC')
    - A longer sub-grain class code (e.g., 'RGmx', 'FCxr')

    Parameters
    ----------
    layer : Layer
        The layer to extract grain form from
    method_name : Optional[str]
        The method name to determine which grain codes are valid.
        If None, returns the layer's grain form as-is.

    Returns
    -------
    Optional[str]
        The resolved grain form code, or None if not available or cannot be
        mapped to the method's valid codes
        
    Notes
    -----
    This function delegates to resolve_grain_form_for_method() in constants.py,
    which is the single source of truth for grain form validation logic.
    """
    if not method_name:
        return layer.grain_form
    
    # Use the centralized utility function
    return resolve_grain_form_for_method(layer.grain_form, method_name)


def _get_layer_input(
    layer: Layer,
    input_name: str,
    method_name: Optional[str] = None
) -> Optional[Any]:
    """
    Extract an input value from a Layer object.

    Parameters
    ----------
    layer : Layer
        The layer to extract from
    input_name : str
        The name of the input to extract
    method_name : Optional[str]
        The method name, used for method-specific resolution (e.g., grain form)

    Returns
    -------
    Optional[Any]
        The extracted value, or None if not available
    """
    if input_name not in LAYER_INPUT_MAPPING:
        return None

    attr_or_func = LAYER_INPUT_MAPPING[input_name]

    if attr_or_func == "_resolve_density":
        return _resolve_density(layer)

    if attr_or_func == "_resolve_grain_form":
        return _resolve_grain_form(layer, method_name)

    value = getattr(layer, attr_or_func, None)

    # Convert numeric types to ufloat if needed (for consistency)
    if value is not None and input_name in ["density_measured", "grain_size"]:
        if isinstance(value, (int, float)):
            return ufloat(float(value), 0.0)

    return value


def _calculate_slab_weight(slab: Slab) -> Optional[UncertainValue]:
    """Return slab weight per unit area from layer densities and thicknesses."""
    total = None
    for layer in slab.layers:
        density = _resolve_density(layer)
        if density is None or layer.thickness is None:
            return None
        layer_weight = density * (layer.thickness / 100.0) * g
        total = layer_weight if total is None else total + layer_weight
    return total


def _calculate_slab_weight_shear(slab: Slab) -> Optional[UncertainValue]:
    """Project slab weight onto the slope-parallel direction."""
    slab_weight = getattr(slab, "slab_weight", None)
    if slab_weight is None:
        slab_weight = _calculate_slab_weight(slab)
    if slab_weight is None or slab.angle is None:
        return None
    return slab_weight * umath.sin(slab.angle * math.pi / 180.0)


def _calculate_slab_weight_with_elasticity(slab: Slab) -> Optional[UncertainValue]:
    """
    Return slope-parallel slab weight when all elastic layer inputs are present.

    The value remains W_s; the target records that density, thickness, slope
    angle, elastic modulus, and Poisson's ratio are all available along the
    pathway.
    """
    if not all(layer.elastic_modulus is not None for layer in slab.layers):
        return None
    if not all(layer.poissons_ratio is not None for layer in slab.layers):
        return None
    slab_weight_shear = getattr(slab, "slab_weight_shear", None)
    if slab_weight_shear is None:
        slab_weight_shear = _calculate_slab_weight_shear(slab)
    return slab_weight_shear


class MethodDispatcher:
    """
    Central registry mapping graph method names to implementations.

    This class maintains the mapping between method names used in the
    parameterization graph and the actual Python functions that implement
    those methods.

    Attributes
    ----------
    _registry : Dict[Tuple[str, str], MethodSpec]
        Internal registry mapping (parameter, method_name) to MethodSpec
    """

    def __init__(self) -> None:
        self._registry: Dict[Tuple[str, str], MethodSpec] = {}
        self._register_all_methods()

    def _register(self, spec: MethodSpec) -> None:
        """Register a method specification."""
        key = (spec.parameter, spec.method_name)
        self._registry[key] = spec

    def _register_all_methods(self) -> None:
        """Register all available calculation methods."""
        # === Density methods (layer-level) ===

        # Direct measurement (data_flow edge)
        self._register(MethodSpec(
            parameter="density",
            method_name="data_flow",
            level=ParameterLevel.LAYER,
            function=lambda density_measured: density_measured,
            required_inputs=["density_measured"],
            optional_inputs={}
        ))

        # Geldsetzer method
        self._register(MethodSpec(
            parameter="density",
            method_name="geldsetzer",
            level=ParameterLevel.LAYER,
            function=lambda hand_hardness_index, grain_form, include_method_uncertainty=True: calculate_density(
                "geldsetzer", hand_hardness_index=hand_hardness_index, grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["hand_hardness_index", "grain_form"],
            optional_inputs={}
        ))

        # Kim-Jamieson Table 2 method
        self._register(MethodSpec(
            parameter="density",
            method_name="kim_jamieson_table2",
            level=ParameterLevel.LAYER,
            function=lambda hand_hardness_index, grain_form, include_method_uncertainty=True: calculate_density(
                "kim_jamieson_table2", hand_hardness_index=hand_hardness_index, grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["hand_hardness_index", "grain_form"],
            optional_inputs={}
        ))

        # Kim-Jamieson Table 5 method
        self._register(MethodSpec(
            parameter="density",
            method_name="kim_jamieson_table5",
            level=ParameterLevel.LAYER,
            function=lambda hand_hardness_index, grain_form, grain_size, include_method_uncertainty=True: calculate_density(
                "kim_jamieson_table5",
                hand_hardness_index=hand_hardness_index,
                grain_form=grain_form,
                grain_size=grain_size,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["hand_hardness_index", "grain_form", "grain_size"],
            optional_inputs={}
        ))

        # === Elastic modulus methods (layer-level) ===

        # Bergfeld method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="bergfeld",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "bergfeld", density=density, grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # Kochle method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="kochle",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "kochle", density=density, grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # Wautier method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="wautier",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "wautier", density=density, grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # Schottner method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="schottner",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_elastic_modulus(
                "schottner", density=density, grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # === Poisson's ratio methods (layer-level) ===

        # Kochle method (grain form only)
        self._register(MethodSpec(
            parameter="poissons_ratio",
            method_name="kochle",
            level=ParameterLevel.LAYER,
            function=lambda grain_form, include_method_uncertainty=True: calculate_poissons_ratio(
                "kochle", grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["grain_form"],
            optional_inputs={}
        ))

        # Srivastava method (density + grain form)
        self._register(MethodSpec(
            parameter="poissons_ratio",
            method_name="srivastava",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form, include_method_uncertainty=True: calculate_poissons_ratio(
                "srivastava", density=density, grain_form=grain_form,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # === Shear modulus methods (layer-level) ===

        # Lamé relationship
        self._register(MethodSpec(
            parameter="shear_modulus",
            method_name="lame_relationship",
            level=ParameterLevel.LAYER,
            function=lambda elastic_modulus, poissons_ratio, include_method_uncertainty=True: calculate_shear_modulus(
                "lame_relationship",
                elastic_modulus=elastic_modulus,
                poissons_ratio=poissons_ratio,
                include_method_uncertainty=include_method_uncertainty
            ),
            required_inputs=["elastic_modulus", "poissons_ratio"],
            optional_inputs={}
        ))

        # === Plate theory methods (slab-level) ===

        # A11 - Extensional stiffness
        self._register(MethodSpec(
            parameter="A11",
            method_name="weissgraeber_rosendahl",
            level=ParameterLevel.SLAB,
            function=lambda slab: calculate_A11("weissgraeber_rosendahl", slab=slab),
            required_inputs=["slab"],
            optional_inputs={}
        ))

        # B11 - Bending-extension coupling
        self._register(MethodSpec(
            parameter="B11",
            method_name="weissgraeber_rosendahl",
            level=ParameterLevel.SLAB,
            function=lambda slab: calculate_B11("weissgraeber_rosendahl", slab=slab),
            required_inputs=["slab"],
            optional_inputs={}
        ))

        # D11 - Bending stiffness
        self._register(MethodSpec(
            parameter="D11",
            method_name="weissgraeber_rosendahl",
            level=ParameterLevel.SLAB,
            function=lambda slab: calculate_D11("weissgraeber_rosendahl", slab=slab),
            required_inputs=["slab"],
            optional_inputs={}
        ))

        # A55 - Shear stiffness
        self._register(MethodSpec(
            parameter="A55",
            method_name="weissgraeber_rosendahl",
            level=ParameterLevel.SLAB,
            function=lambda slab: calculate_A55("weissgraeber_rosendahl", slab=slab),
            required_inputs=["slab"],
            optional_inputs={}
        ))

        # === Slab weight coverage targets (slab-level) ===

        self._register(MethodSpec(
            parameter="slab_weight",
            method_name="sum_layer_weight",
            level=ParameterLevel.SLAB,
            function=lambda slab: _calculate_slab_weight(slab),
            required_inputs=["slab"],
            optional_inputs={}
        ))

        self._register(MethodSpec(
            parameter="slab_weight_shear",
            method_name="slope_parallel_component",
            level=ParameterLevel.SLAB,
            function=lambda slab: _calculate_slab_weight_shear(slab),
            required_inputs=["slab"],
            optional_inputs={}
        ))

        self._register(MethodSpec(
            parameter="slab_weight_with_elasticity",
            method_name="combine_shear_weight_and_elasticity",
            level=ParameterLevel.SLAB,
            function=lambda slab: _calculate_slab_weight_with_elasticity(slab),
            required_inputs=["slab"],
            optional_inputs={}
        ))


    def get_method(self, parameter: str, method_name: str) -> Optional[MethodSpec]:
        """
        Retrieve a method specification by parameter and method name.

        Parameters
        ----------
        parameter : str
            The target parameter (e.g., "density")
        method_name : str
            The method name (e.g., "geldsetzer")

        Returns
        -------
        Optional[MethodSpec]
            The method specification, or None if not found
        """
        return self._registry.get((parameter, method_name))

    def supports_method_uncertainty(self, parameter: str, method_name: str) -> bool:
        """
        Return True if the registered function for *(parameter, method_name)*
        accepts ``include_method_uncertainty`` as a parameter.

        Determined by inspecting the function signature in the registry,
        so it stays in sync with the dispatcher automatically.

        Parameters
        ----------
        parameter : str
            The target parameter (e.g., "density", "elastic_modulus")
        method_name : str
            The method name (e.g., "geldsetzer", "data_flow")

        Returns
        -------
        bool
        """
        spec = self._registry.get((parameter, method_name))
        if spec is None:
            return False
        return "include_method_uncertainty" in inspect.signature(spec.function).parameters

    def execute(
        self,
        parameter: str,
        method_name: str,
        layer: Optional[Layer] = None,
        slab: Optional[Slab] = None,
        **extra_inputs: Any,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Execute a method and return (result, error_message).

        Parameters
        ----------
        parameter : str
            The target parameter (e.g., "density")
        method_name : str
            The method name (e.g., "geldsetzer")
        layer : Optional[Layer]
            Layer object for layer-level methods
        slab : Optional[Slab]
            Slab object for slab-level methods
        **extra_inputs
            Additional inputs to pass to the method

        Returns
        -------
        Tuple[Optional[UncertainValue], Optional[str]]
            (result, None) if successful, (None, error_message) if failed
        """
        spec = self.get_method(parameter, method_name)
        if spec is None:
            return None, f"Unknown method: {parameter}.{method_name}"

        # Gather inputs based on level
        if spec.level == ParameterLevel.LAYER:
            if layer is None:
                return None, "Layer required for layer-level method"
            inputs = self._gather_layer_inputs(layer, spec)
        elif spec.level == ParameterLevel.WEAK_LAYER:
            # Legacy hook retained for downstream extensions.
            if slab is None:
                return None, "Slab required for weak-layer method"
            inputs = {"slab": slab}
        else:
            # Slab-level methods receive the full slab.
            if slab is None:
                return None, "Slab required for slab-level method"
            inputs = {"slab": slab}

        if inputs is None:
            return None, f"Missing required inputs for {parameter}.{method_name}"

        # Merge with optional inputs and extra inputs
        all_inputs = {**spec.optional_inputs, **inputs, **extra_inputs}

        try:
            result = spec.function(**all_inputs)

            # A ufloat(nan, nan) return value means the method failed (e.g. unsupported
            # grain form, missing data). Treat any NaN nominal value as a failure so
            # callers never see a non-None result that carries no information.
            if result is not None:
                if hasattr(result, 'nominal_value'):
                    if np.isnan(result.nominal_value):
                        return None, f"Method {method_name} returned NaN"
                elif isinstance(result, (float, int)) and np.isnan(result):
                    return None, f"Method {method_name} returned NaN"

            return result, None
        except Exception as e:
            return None, f"Execution error: {str(e)}"

    def _gather_layer_inputs(
        self,
        layer: Layer,
        spec: MethodSpec
    ) -> Optional[Dict[str, Any]]:
        """
        Gather required inputs from a Layer for a method.

        Parameters
        ----------
        layer : Layer
            The layer to extract inputs from
        spec : MethodSpec
            The method specification

        Returns
        -------
        Optional[Dict[str, Any]]
            Dictionary of input values, or None if any required input is missing
        """
        inputs = {}
        for input_name in spec.required_inputs:
            value = _get_layer_input(layer, input_name, method_name=spec.method_name)
            if value is None:
                return None
            inputs[input_name] = value
        return inputs

    def get_all_methods(self) -> Dict[str, List[str]]:
        """
        Get all registered methods grouped by parameter.

        Returns
        -------
        Dict[str, List[str]]
            Dictionary mapping parameter names to lists of method names
        """
        methods: Dict[str, List[str]] = {}
        for (param, method_name), spec in self._registry.items():
            if param not in methods:
                methods[param] = []
            methods[param].append(method_name)
        return methods
