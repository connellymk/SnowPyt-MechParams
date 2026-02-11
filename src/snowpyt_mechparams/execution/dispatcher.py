"""
Method dispatcher for parameterization execution.

This module provides the MethodDispatcher class that maps method names from
the parameterization graph to actual calculation function implementations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from uncertainties import ufloat

from snowpyt_mechparams.data_structures import Layer, Slab, UncertainValue
from snowpyt_mechparams.layer_parameters.density import calculate_density
from snowpyt_mechparams.layer_parameters.elastic_modulus import calculate_elastic_modulus
from snowpyt_mechparams.layer_parameters.poissons_ratio import calculate_poissons_ratio
from snowpyt_mechparams.layer_parameters.shear_modulus import calculate_shear_modulus
from snowpyt_mechparams.slab_parameters.A11 import calculate_A11
from snowpyt_mechparams.slab_parameters.B11 import calculate_B11
from snowpyt_mechparams.slab_parameters.D11 import calculate_D11
from snowpyt_mechparams.slab_parameters.A55 import calculate_A55
from snowpyt_mechparams.snowpilot_utils.snowpilot_constants import resolve_grain_form_for_method


class ParameterLevel(Enum):
    """Whether a parameter is computed per-layer or per-slab."""
    LAYER = "layer"
    SLAB = "slab"


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
    "hand_hardness": "hand_hardness",
    "grain_form": "_resolve_grain_form",  # Special: method-specific resolution
    "grain_size": "grain_size_avg",
    "poissons_ratio": "poissons_ratio",
    "elastic_modulus": "elastic_modulus",
    "shear_modulus": "shear_modulus",
}


# Note: Valid grain form codes for each density method are now defined in
# snowpilot_utils.snowpilot_constants.GRAIN_FORM_METHODS and accessed via
# the resolve_grain_form_for_method() utility function.


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
    This function delegates to resolve_grain_form_for_method() in
    snowpilot_utils.snowpilot_constants, which is the single source of truth
    for grain form validation logic.
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

    def __init__(self):
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
            function=lambda hand_hardness, grain_form: calculate_density(
                "geldsetzer", hand_hardness=hand_hardness, grain_form=grain_form
            ),
            required_inputs=["hand_hardness", "grain_form"],
            optional_inputs={}
        ))

        # Kim-Jamieson Table 2 method
        self._register(MethodSpec(
            parameter="density",
            method_name="kim_jamieson_table2",
            level=ParameterLevel.LAYER,
            function=lambda hand_hardness, grain_form: calculate_density(
                "kim_jamieson_table2", hand_hardness=hand_hardness, grain_form=grain_form
            ),
            required_inputs=["hand_hardness", "grain_form"],
            optional_inputs={}
        ))

        # Kim-Jamieson Table 5 method
        self._register(MethodSpec(
            parameter="density",
            method_name="kim_jamieson_table5",
            level=ParameterLevel.LAYER,
            function=lambda hand_hardness, grain_form, grain_size: calculate_density(
                "kim_jamieson_table5",
                hand_hardness=hand_hardness,
                grain_form=grain_form,
                grain_size=grain_size.nominal_value if hasattr(grain_size, 'nominal_value') else grain_size
            ),
            required_inputs=["hand_hardness", "grain_form", "grain_size"],
            optional_inputs={}
        ))

        # === Elastic modulus methods (layer-level) ===

        # Bergfeld method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="bergfeld",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form: calculate_elastic_modulus(
                "bergfeld", density=density, grain_form=grain_form
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # Kochle method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="kochle",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form: calculate_elastic_modulus(
                "kochle", density=density, grain_form=grain_form
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # Wautier method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="wautier",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form: calculate_elastic_modulus(
                "wautier", density=density, grain_form=grain_form
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # Schottner method
        self._register(MethodSpec(
            parameter="elastic_modulus",
            method_name="schottner",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form: calculate_elastic_modulus(
                "schottner", density=density, grain_form=grain_form
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
            function=lambda grain_form: calculate_poissons_ratio(
                "kochle", grain_form=grain_form
            ),
            required_inputs=["grain_form"],
            optional_inputs={}
        ))

        # Srivastava method (density + grain form)
        self._register(MethodSpec(
            parameter="poissons_ratio",
            method_name="srivastava",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form: calculate_poissons_ratio(
                "srivastava", density=density, grain_form=grain_form
            ),
            required_inputs=["density", "grain_form"],
            optional_inputs={}
        ))

        # === Shear modulus methods (layer-level) ===

        # Wautier method
        self._register(MethodSpec(
            parameter="shear_modulus",
            method_name="wautier",
            level=ParameterLevel.LAYER,
            function=lambda density, grain_form: calculate_shear_modulus(
                "wautier", density=density, grain_form=grain_form
            ),
            required_inputs=["density", "grain_form"],
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

    def execute(
        self,
        parameter: str,
        method_name: str,
        layer: Optional[Layer] = None,
        slab: Optional[Slab] = None,
        **extra_inputs
    ) -> Tuple[Optional[UncertainValue], Optional[str]]:
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
        else:
            if slab is None:
                return None, "Slab required for slab-level method"
            inputs = {"slab": slab}

        if inputs is None:
            return None, f"Missing required inputs for {parameter}.{method_name}"

        # Merge with optional inputs and extra inputs
        all_inputs = {**spec.optional_inputs, **inputs, **extra_inputs}

        try:
            result = spec.function(**all_inputs)

            # Check for NaN results
            if result is not None:
                if hasattr(result, 'nominal_value'):
                    if np.isnan(result.nominal_value):
                        return None, f"Method {method_name} returned NaN"
                elif isinstance(result, float) and np.isnan(result):
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
