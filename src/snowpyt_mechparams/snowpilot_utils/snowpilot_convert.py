"""
CAAML (Snow Profile) data parser and converter.

This module provides functionality to parse CAAML XML files (from SnowPilot
or other sources) and convert them to snowpyt_mechparams data structures
(Layer and Slab objects).
"""

import logging
import os
from typing import Any, List, Optional

from snowpylot import caaml_parser

from snowpyt_mechparams.data_structures import Layer, Slab
from snowpyt_mechparams.snowpilot_utils.snowpilot_constants import GRAIN_FORM_METHODS

logger = logging.getLogger(__name__)


def parse_caaml_file(filepath: str) -> Any:
    """
    Parse a single CAAML XML file.

    Parameters
    ----------
    filepath : str
        Path to the CAAML XML file

    Returns
    -------
    Any
        Parsed CAAML profile object from snowpylot

    Raises
    ------
    Exception
        If the file cannot be parsed
    """
    return caaml_parser(filepath)


def parse_caaml_directory(directory: str, pattern: str = "*.xml") -> List[Any]:
    """
    Parse all CAAML XML files in a directory.

    Parameters
    ----------
    directory : str
        Path to directory containing XML files
    pattern : str, optional
        File pattern to match (default: "*.xml")

    Returns
    -------
    List[Any]
        List of parsed CAAML profile objects

    Notes
    -----
    Files that fail to parse are logged as warnings and skipped.
    """
    all_profiles = []
    failed_files = []

    xml_files = [f for f in os.listdir(directory) if f.endswith(".xml")]

    for file in xml_files:
        try:
            file_path = os.path.join(directory, file)
            profile = caaml_parser(file_path)
            all_profiles.append(profile)
        except Exception as e:
            failed_files.append((file, str(e)))
            logger.warning(f"Failed to parse {file}: {e}")

    logger.info(
        f"Successfully parsed {len(all_profiles)} of {len(xml_files)} files "
        f"({len(failed_files)} failed)"
    )

    return all_profiles


def caaml_to_layers(caaml_profile: Any, include_density: bool = True) -> List[Layer]:
    """
    Convert a CAAML snow profile to a list of Layer objects.

    Parameters
    ----------
    caaml_profile : Any
        Parsed CAAML profile object from parse_caaml_file()
    include_density : bool, optional
        If True, attempts to match and include direct density measurements
        from the profile's density profile (default: True)

    Returns
    -------
    List[Layer]
        List of Layer objects representing the snow layers in the profile

    Notes
    -----
    - depth_top and thickness are extracted from arrays (using [0] index)
    - grain_form is extracted from layer.grain_form_primary (sub-grain class if available,
      otherwise basic grain class)
    - grain_size_avg is extracted from layer.grain_form_primary.grain_size_avg
    - If include_density=True, density values are matched by depth_top and thickness
      and stored in the density_measured field
    """
    layers: List[Layer] = []

    # Check if snow_profile and layers exist
    if (
        not hasattr(caaml_profile, "snow_profile")
        or not hasattr(caaml_profile.snow_profile, "layers")
    ):
        return layers

    if not caaml_profile.snow_profile.layers:
        return layers

    for layer in caaml_profile.snow_profile.layers:
        # Extract depth_top (array to scalar)
        depth_top = layer.depth_top[0] if layer.depth_top else None

        # Extract thickness (array to scalar)
        thickness = layer.thickness[0] if layer.thickness else None

        # Extract hand hardness
        hand_hardness = layer.hardness if hasattr(layer, "hardness") else None

        # Extract grain form from grain_form_primary
        # Store the most specific code available: sub-grain class if present, otherwise basic class
        # This preserves full detail from the CAAML file. The Layer.main_grain_form property
        # can be used to extract just the 2-character basic code when needed.
        grain_form = None
        if hasattr(layer, "grain_form_primary") and layer.grain_form_primary:
            grain_form_sub = getattr(
                layer.grain_form_primary, "sub_grain_class_code", None
            )
            grain_form_basic = getattr(
                layer.grain_form_primary, "basic_grain_class_code", None
            )
            # Prefer sub-grain (more specific), fall back to basic
            grain_form = grain_form_sub if grain_form_sub else grain_form_basic

        # Extract grain size average
        grain_size_avg = None
        if (
            hasattr(layer, "grain_form_primary")
            and layer.grain_form_primary
            and hasattr(layer.grain_form_primary, "grain_size_avg")
        ):
            grain_size_data = layer.grain_form_primary.grain_size_avg
            if grain_size_data:
                # Extract scalar from array if needed
                grain_size_avg = (
                    grain_size_data[0]
                    if isinstance(grain_size_data, (list, tuple))
                    else grain_size_data
                )

        # Optionally match and extract density from density profile
        density_measured = None
        if include_density and hasattr(caaml_profile.snow_profile, "density_profile"):
            for density_obs in caaml_profile.snow_profile.density_profile:
                # Match by depth_top and thickness
                if (
                    density_obs.depth_top == layer.depth_top
                    and density_obs.thickness == layer.thickness
                ):
                    density_measured = density_obs.density
                    break

        # Create Layer object
        layer_obj = Layer(
            depth_top=depth_top,
            thickness=thickness,
            density_measured=density_measured,
            hand_hardness=hand_hardness,
            grain_form=grain_form,
            grain_size_avg=grain_size_avg,
        )

        layers.append(layer_obj)

    return layers


def caaml_to_slab(
    caaml_profile: Any,
    weak_layer_def: Optional[str] = None,
    depth_tolerance: float = 2.0,
) -> Optional[Slab]:
    """
    Convert a CAAML snow profile to a Slab object.

    Parameters
    ----------
    caaml_profile : Any
        Parsed CAAML profile object from parse_caaml_file()
    weak_layer_def : Optional[str]
        Weak layer definition (optional) - one of:
        - None: Returns all layers in the profile (no weak layer filtering)
        - "layer_of_concern": Uses layer with layer_of_concern=True
        - "CT_failure_layer": Uses CT test failure layer with Q1/SC/SP fracture character
        - "ECTP_failure_layer": Uses ECT test failure layer with propagation
    depth_tolerance : float, optional
        Tolerance in cm for matching test depths to layer depths (default: 2.0 cm)

    Returns
    -------
    Optional[Slab]
        Slab object containing layers above the weak layer (or all layers if
        weak_layer_def=None), or None if:
        - No weak layer is found (when weak_layer_def is specified)
        - No valid layers exist above the weak layer
        - The profile contains no valid layers

    Notes
    -----
    - If weak_layer_def=None, returns a slab with all layers (weak_layer=None)
    - If weak_layer_def is specified, the weak_layer field is populated with the
      Layer object that contains the failure depth (i.e., the layer where
      depth_top <= failure_depth < depth_bottom)
    - The slab consists of all layers with depth_top < weak_layer_depth
    - Layers are ordered from top to bottom as they appear in the profile
    - The angle is automatically extracted from profile.core_info.location.slope_angle
      and is NaN if unavailable
    - Density measurements are automatically included when available
    - The depth_tolerance parameter is used by _find_weak_layer_depth for matching
      test depths to layer depths when finding the weak layer depth, but the weak
      layer itself is identified as the layer containing that depth
    - Stability test results (ECT_results, CT_results, PST_results) are extracted
      from the profile and match the snowpylot structure
    - The layer_of_concern field is populated with the Layer object for any layer
      marked as layer_of_concern in the profile, or None if not found

    Examples
    --------
    >>> # Get slab with all layers (no weak layer filtering)
    >>> slab = caaml_to_slab(profile)
    >>>
    >>> # Get slab above the indicated layer of concern
    >>> slab = caaml_to_slab(profile, "layer_of_concern")
    >>>
    >>> # Get slab above CT failure layer
    >>> slab = caaml_to_slab(profile, "CT_failure_layer")
    >>>
    >>> # Get slab above ECTP failure layer
    >>> slab = caaml_to_slab(profile, "ECTP_failure_layer")
    >>>
    >>> if slab:
    ...     print(f"Slab has {len(slab.layers)} layers above weak layer")
    """
    # Get all layers
    all_layers = caaml_to_layers(caaml_profile)

    if not all_layers:
        return None

    # Extract angle from profile
    angle = _extract_slope_angle(caaml_profile)

    # Extract stability test results (matching snowpylot structure)
    ect_results = _extract_stability_test_results(caaml_profile, "ECT")
    ct_results = _extract_stability_test_results(caaml_profile, "CT")
    pst_results = _extract_stability_test_results(caaml_profile, "PST")

    # Extract layer of concern
    layer_of_concern = _extract_layer_of_concern(caaml_profile, all_layers)

    # If no weak layer definition, return all layers with test results
    if weak_layer_def is None:
        return Slab(
            layers=all_layers,
            angle=angle,
            ECT_results=ect_results,
            CT_results=ct_results,
            PST_results=pst_results,
            layer_of_concern=layer_of_concern,
        )

    # Find the weak layer depth
    weak_layer_depth = _find_weak_layer_depth(caaml_profile, weak_layer_def)

    if weak_layer_depth is None:
        return None

    # Find the weak layer object from all_layers
    # The weak layer is the layer that contains the failure depth
    # (i.e., depth_top <= weak_layer_depth < depth_bottom)
    weak_layer = None
    for layer in all_layers:
        if layer.depth_top is not None and layer.depth_bottom is not None:
            if layer.depth_top <= weak_layer_depth < layer.depth_bottom:
                weak_layer = layer
                break

    # Filter layers above the weak layer
    # Layer is above weak layer if its depth_top < weak_layer_depth
    slab_layers = []
    for layer in all_layers:
        if layer.depth_top is not None and layer.depth_top < weak_layer_depth:
            slab_layers.append(layer)

    # Return None if no valid layers above weak layer
    if not slab_layers:
        return None

    return Slab(
        layers=slab_layers,
        angle=angle,
        weak_layer=weak_layer,
        ECT_results=ect_results,
        CT_results=ct_results,
        PST_results=pst_results,
        layer_of_concern=layer_of_concern,
    )


def convert_grain_form(grain_form_obj: Optional[Any], method: str) -> Optional[str]:
    """
    Convert grain form object to code needed for specified method's lookup table.

    Parameters
    ----------
    grain_form_obj : Optional[Any]
        Grain form object from CAAML data
    method : str
        Method name - one of: "geldsetzer", "kim_jamieson_table2", "kim_jamieson_table5"

    Returns
    -------
    Optional[str]
        Grain form code for the specified method's table lookup, or None if
        not mappable

    Raises
    ------
    ValueError
        If method is not recognized
    """
    if grain_form_obj is None:
        return None

    # Select appropriate grain code sets based on method
    method_lower = method.lower()
    if method_lower not in GRAIN_FORM_METHODS:
        valid_methods = ", ".join(GRAIN_FORM_METHODS.keys())
        raise ValueError(
            f"Invalid method '{method}'. Valid options: {valid_methods}"
        )

    sub_codes = GRAIN_FORM_METHODS[method_lower]["sub_grain_class"]
    basic_codes = GRAIN_FORM_METHODS[method_lower]["basic_grain_class"]

    # Check sub_grain_class_code first (more specific)
    sub_code = getattr(grain_form_obj, "sub_grain_class_code", None)
    if sub_code and sub_code in sub_codes:
        return str(sub_code)

    # Fall back to basic_grain_class_code
    basic_code = getattr(grain_form_obj, "basic_grain_class_code", None)
    return str(basic_code) if basic_code in basic_codes else None


# ============================================================================
# Private Helper Functions
# ============================================================================


def _extract_slope_angle(caaml_profile: Any) -> float:
    """
    Helper function to extract slope angle from CAAML profile.

    Parameters
    ----------
    caaml_profile : Any
        Parsed CAAML profile object

    Returns
    -------
    float
        Slope angle in degrees, or NaN if not available
    """
    try:
        slope_angle_data = caaml_profile.core_info.location.slope_angle
        # slope_angle is returned as [value, units] where units are always 'deg'
        if slope_angle_data and len(slope_angle_data) > 0:
            return float(slope_angle_data[0])
        else:
            return float("nan")
    except (AttributeError, IndexError, TypeError, ValueError):
        # Fall back to NaN if slope_angle is not available or cannot be converted
        return float("nan")


def _get_value_safe(obj: Any) -> Optional[float]:
    """
    Safely extract value from object that might be None, scalar, or array-like.

    Parameters
    ----------
    obj : Any
        Value to extract (could be None, scalar, list, tuple, or array)

    Returns
    -------
    Optional[float]
        Scalar value or None
    """
    if obj is None:
        return None
    if isinstance(obj, (list, tuple)):
        return obj[0] if len(obj) > 0 else None
    # Handle numpy arrays if present
    if hasattr(obj, "__len__") and hasattr(obj, "shape"):
        return obj[0] if len(obj) > 0 else None
    return obj


def _find_weak_layer_depth(caaml_profile: Any, weak_layer_def: str) -> Optional[float]:
    """
    Find the depth of the weak layer based on the specified definition.

    Parameters
    ----------
    caaml_profile : Any
        Parsed CAAML profile object
    weak_layer_def : str
        Weak layer definition - one of:
        - "layer_of_concern": Uses layer with layer_of_concern=True
        - "CT_failure_layer": Uses CT test failure layer with Q1/SC/SP fracture character
        - "ECTP_failure_layer": Uses ECT test failure layer with propagation

    Returns
    -------
    Optional[float]
        Depth (from top) of the weak layer in cm, or None if no weak layer found

    Notes
    -----
    - For layer_of_concern: Returns the depth_top of the first layer marked as layer_of_concern
    - For CT_failure_layer: Returns the depth_top from the first CT test with Q1/SC/SP fracture character
    - For ECTP_failure_layer: Returns the depth_top from the first ECT test with propagation
    - If multiple weak layers exist, returns the shallowest (smallest depth_top)
    """
    if not hasattr(caaml_profile, "snow_profile") or not caaml_profile.snow_profile:
        return None

    if weak_layer_def == "layer_of_concern":
        # Find layer marked as layer_of_concern
        if (
            not hasattr(caaml_profile.snow_profile, "layers")
            or not caaml_profile.snow_profile.layers
        ):
            return None

        for layer in caaml_profile.snow_profile.layers:
            if hasattr(layer, "layer_of_concern") and layer.layer_of_concern is True:
                depth = _get_value_safe(layer.depth_top)
                if depth is not None:
                    return depth
        return None

    elif weak_layer_def == "CT_failure_layer":
        # Find CT test failure layer with Q1/SC/SP fracture character
        if not hasattr(caaml_profile, "stability_tests") or not hasattr(
            caaml_profile.stability_tests, "CT"
        ):
            return None

        ct_tests = caaml_profile.stability_tests.CT
        if not ct_tests:
            return None

        for ct in ct_tests:
            if (
                hasattr(ct, "fracture_character")
                and ct.fracture_character in ["Q1", "SC", "SP"]
            ):
                depth = _get_value_safe(ct.depth_top)
                if depth is not None:
                    return depth
        return None

    elif weak_layer_def == "ECTP_failure_layer":
        # Find ECT test failure layer with propagation
        if not hasattr(caaml_profile, "stability_tests") or not hasattr(
            caaml_profile.stability_tests, "ECT"
        ):
            return None

        ect_tests = caaml_profile.stability_tests.ECT
        if not ect_tests:
            return None

        for ect in ect_tests:
            # Check for propagation in both attribute and test_score
            has_propagation = (
                hasattr(ect, "propagation") and ect.propagation is True
            ) or (
                hasattr(ect, "test_score")
                and ect.test_score
                and "ECTP" in str(ect.test_score)
            )
            if has_propagation:
                depth = _get_value_safe(ect.depth_top)
                if depth is not None:
                    return depth
        return None

    else:
        raise ValueError(
            f"Invalid weak_layer_def '{weak_layer_def}'. "
            f"Valid options: 'layer_of_concern', 'CT_failure_layer', 'ECTP_failure_layer'"
        )


def _extract_stability_test_results(caaml_profile: Any, test_type: str) -> Optional[List[Any]]:
    """
    Extract stability test results from CAAML profile.

    Parameters
    ----------
    caaml_profile : Any
        Parsed CAAML profile object
    test_type : str
        Test type - one of: "ECT", "CT", "PST"

    Returns
    -------
    Optional[List[Any]]
        List of test results matching snowpylot structure, or None if not available
    """
    if not hasattr(caaml_profile, "stability_tests") or not caaml_profile.stability_tests:
        return None

    # Map test types to possible snowpylot attribute names
    # Try multiple possible names for PST (PropSawTest)
    test_attr_map = {
        "ECT": ["ECT"],
        "CT": ["CT"],
        "PST": ["PST", "PropSawTest", "PropSaw"],
    }

    if test_type not in test_attr_map:
        return None

    # Try each possible attribute name
    for attr_name in test_attr_map[test_type]:
        if hasattr(caaml_profile.stability_tests, attr_name):
            tests = getattr(caaml_profile.stability_tests, attr_name)
            if tests:
                return list(tests) if isinstance(tests, (list, tuple)) else [tests]
    return None


def _extract_layer_of_concern(caaml_profile: Any, all_layers: List[Layer]) -> Optional[Layer]:
    """
    Extract the layer of concern from CAAML profile and convert to Layer object.

    Parameters
    ----------
    caaml_profile : Any
        Parsed CAAML profile object
    all_layers : List[Layer]
        List of all Layer objects from the profile

    Returns
    -------
    Optional[Layer]
        Layer object for the layer of concern, or None if not found
    """
    if (
        not hasattr(caaml_profile, "snow_profile")
        or not hasattr(caaml_profile.snow_profile, "layers")
        or not caaml_profile.snow_profile.layers
    ):
        return None

    # Find the layer marked as layer_of_concern in CAAML
    for caaml_layer in caaml_profile.snow_profile.layers:
        if hasattr(caaml_layer, "layer_of_concern") and caaml_layer.layer_of_concern is True:
            # Find the corresponding Layer object by matching depth_top
            depth_top = _get_value_safe(caaml_layer.depth_top)
            if depth_top is not None:
                for layer in all_layers:
                    if layer.depth_top is not None and abs(layer.depth_top - depth_top) < 0.01:
                        return layer
    return None
