"""Dispatch registry-defined methods against Layer and Slab objects."""

from __future__ import annotations

import inspect
from typing import Any, Dict, Optional, Tuple

import numpy as np
from uncertainties import ufloat

from snowpyt_mechparams.constants import resolve_grain_form_for_method
from snowpyt_mechparams.methods import MethodRegistry, default_registry
from snowpyt_mechparams.methods.specs import MethodSpec, ParameterLevel
from snowpyt_mechparams.models import Layer, Slab, UncertainValue

LAYER_INPUT_MAPPING = {
    "density_measured": "density_measured",
    "density": "_resolve_density",
    "hand_hardness_index": "hand_hardness_index",
    "grain_form": "_resolve_grain_form",
    "grain_size": "grain_size_avg",
    "poissons_ratio": "poissons_ratio",
    "elastic_modulus": "elastic_modulus",
    "shear_modulus": "shear_modulus",
}


def _resolve_density(layer: Layer) -> Optional[UncertainValue]:
    """Prefer pathway-computed density, falling back to direct measurement."""
    if layer.density_calculated is not None:
        return layer.density_calculated
    if layer.density_measured is not None:
        value = layer.density_measured
        if isinstance(value, (int, float)):
            return ufloat(float(value), 0.0)
        return value
    return None


def _resolve_grain_form(
    layer: Layer, method_name: Optional[str] = None
) -> Optional[str]:
    """Resolve the grain-form code expected by a method."""
    if not method_name:
        return layer.grain_form
    return resolve_grain_form_for_method(layer.grain_form, method_name)


def _get_layer_input(
    layer: Layer,
    input_name: str,
    method_name: Optional[str] = None,
) -> Optional[Any]:
    """Extract a registry input from a layer."""
    if input_name not in LAYER_INPUT_MAPPING:
        return None

    attr_or_func = LAYER_INPUT_MAPPING[input_name]
    if attr_or_func == "_resolve_density":
        return _resolve_density(layer)
    if attr_or_func == "_resolve_grain_form":
        return _resolve_grain_form(layer, method_name)

    value = getattr(layer, attr_or_func, None)
    if value is not None and input_name in ["density_measured", "grain_size"]:
        if isinstance(value, (int, float)):
            return ufloat(float(value), 0.0)
    return value


class MethodDispatcher:
    """Map graph method names to registry-defined function implementations."""

    def __init__(self, registry: Optional[MethodRegistry] = None) -> None:
        self.registry = registry or default_registry()

    def get_method(self, parameter: str, method_name: str) -> Optional[MethodSpec]:
        """Retrieve a method specification by target and method name."""
        return self.registry.get(parameter, method_name)

    def supports_method_uncertainty(self, parameter: str, method_name: str) -> bool:
        """Return True if the method function accepts include_method_uncertainty."""
        spec = self.get_method(parameter, method_name)
        if spec is None:
            return False
        return (
            "include_method_uncertainty" in inspect.signature(spec.function).parameters
        )

    def execute(
        self,
        parameter: str,
        method_name: str,
        layer: Optional[Layer] = None,
        slab: Optional[Slab] = None,
        **extra_inputs: Any,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Execute a method and return ``(result, error_message)``."""
        spec = self.get_method(parameter, method_name)
        if spec is None:
            return None, f"Unknown method: {parameter}.{method_name}"

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

        all_inputs = {**inputs, **extra_inputs}
        try:
            result = spec.function(**all_inputs)
            if _is_nan_result(result):
                return None, f"Method {method_name} returned NaN"
            return result, None
        except Exception as exc:  # pragma: no cover - defensive boundary
            return None, f"Execution error: {str(exc)}"

    def _gather_layer_inputs(
        self,
        layer: Layer,
        spec: MethodSpec,
    ) -> Optional[Dict[str, Any]]:
        """Gather required inputs from a layer for a method."""
        inputs = {}
        for input_name in spec.required_inputs:
            value = _get_layer_input(layer, input_name, method_name=spec.method_name)
            if value is None:
                return None
            inputs[input_name] = value
        return inputs

    def get_all_methods(self) -> Dict[str, list[str]]:
        """Get all registered methods grouped by target parameter."""
        return self.registry.as_method_dict()


def _is_nan_result(result: Any) -> bool:
    """Return True when a method result carries no numeric information."""
    if result is None:
        return False
    if hasattr(result, "nominal_value"):
        return bool(np.isnan(result.nominal_value))
    if isinstance(result, (float, int)):
        return bool(np.isnan(result))
    return False
