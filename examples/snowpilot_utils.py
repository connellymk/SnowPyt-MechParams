# Utility functions for snowpilot data
import os
import sys
from typing import Any, List, Optional

from snowpylot import caaml_parser  # type: ignore

# Add the src directory to import snowpyt_mechparams
_src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if _src_path not in sys.path:
    sys.path.append(_src_path)

from snowpyt_mechparams.data_structures.data_structures import Layer, Slab  # type: ignore

# Constants for grain form codes by method

# Geldsetzer (2000) method codes
GELDSETZER_SUB_GRAIN_CLASS_CODES = {"PPgp", "RGmx", "FCmx"}
GELDSETZER_BASIC_GRAIN_CLASS_CODES = {"PP", "DF", "RG", "FC", "DH"}

# Kim & Jamieson (2014) table 2 method codes
KIM_JAMIESON_TABLE2_SUB_GRAIN_CLASS_CODES = {"PPgp", "RGxf", "FCxr", "MFcr"}
KIM_JAMIESON_TABLE2_BASIC_GRAIN_CLASS_CODES = {"PP", "DF", "FC", "DH", "RG"}

# Kim & Jamieson (2014) table 5 method codes
KIM_JAMIESON_TABLE5_SUB_GRAIN_CLASS_CODES = {"FCxr", "PPgp"}
KIM_JAMIESON_TABLE5_BASIC_GRAIN_CLASS_CODES = {"FC", "PP", "DF", "MF"}


def convert_grain_form(grain_form_obj: Optional[Any], method: str) -> Optional[str]:
    """
    Convert grain form object to code needed for specified method's lookup table.

    Parameters:
    grain_form_obj: Grain form object from CAAML data
    method: Method name - either "geldsetzer" or "kim"

    Returns:
    str: Grain form code for the specified method's table lookup, or None if
         not mappable

    Raises:
    ValueError: If method is not "geldsetzer" or "kim"
    """
    if grain_form_obj is None:
        return None

    # Select appropriate grain code sets based on method
    if method.lower() == "geldsetzer":
        sub_codes = GELDSETZER_SUB_GRAIN_CLASS_CODES
        basic_codes = GELDSETZER_BASIC_GRAIN_CLASS_CODES
    elif method.lower() == "kim_jamieson_table2":
        sub_codes = KIM_JAMIESON_TABLE2_SUB_GRAIN_CLASS_CODES
        basic_codes = KIM_JAMIESON_TABLE2_BASIC_GRAIN_CLASS_CODES
    elif method.lower() == "kim_jamieson_table5":
        sub_codes = KIM_JAMIESON_TABLE5_SUB_GRAIN_CLASS_CODES
        basic_codes = KIM_JAMIESON_TABLE5_BASIC_GRAIN_CLASS_CODES
    else:
        raise ValueError(
            f"Invalid method '{method}'. Valid options: 'geldsetzer', 'kim'"
        )

    # Check sub_grain_class_code first (more specific)
    sub_code = getattr(grain_form_obj, 'sub_grain_class_code', None)
    if sub_code and sub_code in sub_codes:
        return str(sub_code)

    # Fall back to basic_grain_class_code
    basic_code = getattr(grain_form_obj, 'basic_grain_class_code', None)
    return str(basic_code) if basic_code in basic_codes else None


def parse_sample_pits(folder_path: str = 'data') -> List[Any]:
    """
    Parse all XML snowpit files from a specified folder.

    Parameters:
    folder_path: Path to folder containing XML files (defaults to 'data')

    Returns:
    List of parsed pit objects
    """
    all_pits = []
    failed_files = []

    xml_files = [f for f in os.listdir(folder_path) if f.endswith('.xml')]

    for file in xml_files:
        try:
            file_path = os.path.join(folder_path, file)
            pit = caaml_parser(file_path)
            all_pits.append(pit)
        except Exception as e:
            failed_files.append((file, str(e)))
            print(f"Warning: Failed to parse {file}: {e}")

    print(f"Successfully parsed {len(all_pits)} files")
    print(f"Failed to parse {len(failed_files)} files")

    return all_pits


def pit_to_layers(pit: Any, include_density: bool = True) -> List[Layer]:
    """
    Convert a snowpilot pit object to a list of Layer objects.

    Parameters:
    pit: Parsed pit object from caaml_parser
    include_density: If True, attempts to match and include direct density measurements
                     from the pit's density profile (defaults to True)

    Returns:
    List of Layer objects representing the snow layers in the pit

    Notes:
    - depth_top and thickness are extracted from arrays (using [0] index)
    - grain_form is extracted from layer.grain_form_primary.basic_grain_class_code
    - grain_size_avg is extracted from layer.grain_form_primary.grain_size_avg
    - If include_density=True, density values are matched by depth_top and thickness
      and stored in the density_measured field
    """
    layers: List[Layer] = []
    
    # Check if snow_profile and layers exist
    if not hasattr(pit, 'snow_profile') or not hasattr(pit.snow_profile, 'layers'):
        return layers
    
    if not pit.snow_profile.layers:
        return layers
    
    for layer in pit.snow_profile.layers:
        # Extract depth_top (array to scalar)
        depth_top = layer.depth_top[0] if layer.depth_top else None
        
        # Extract thickness (array to scalar)
        thickness = layer.thickness[0] if layer.thickness else None
        
        # Extract hand hardness
        hand_hardness = layer.hardness if hasattr(layer, 'hardness') else None
        
        # Extract grain form from grain_form_primary (both basic and sub codes)
        grain_form = None
        grain_form_sub = None
        if hasattr(layer, 'grain_form_primary') and layer.grain_form_primary:
            grain_form = getattr(layer.grain_form_primary, 'basic_grain_class_code', None)
            grain_form_sub = getattr(layer.grain_form_primary, 'sub_grain_class_code', None)
        
        # Extract grain size average
        grain_size_avg = None
        if hasattr(layer, 'grain_form_primary') and layer.grain_form_primary and hasattr(layer.grain_form_primary, 'grain_size_avg'):
            grain_size_data = layer.grain_form_primary.grain_size_avg
            if grain_size_data:
                # Extract scalar from array if needed
                grain_size_avg = grain_size_data[0] if isinstance(grain_size_data, (list, tuple)) else grain_size_data
        
        # Optionally match and extract density from density profile
        density_measured = None
        if include_density and hasattr(pit.snow_profile, 'density_profile'):
            for density_obs in pit.snow_profile.density_profile:
                # Match by depth_top and thickness
                if density_obs.depth_top == layer.depth_top and density_obs.thickness == layer.thickness:
                    density_measured = density_obs.density
                    break
        
        # Create Layer object
        layer_obj = Layer(
            depth_top=depth_top,
            thickness=thickness,
            density_measured=density_measured,
            hand_hardness=hand_hardness,
            grain_form=grain_form,
            grain_form_sub=grain_form_sub,
            grain_size_avg=grain_size_avg
        )
        
        layers.append(layer_obj)
    
    return layers


def _extract_angle(pit: Any) -> float:
    """
    Helper function to extract slope angle from pit.
    
    Parameters:
    pit: Parsed pit object from caaml_parser
    
    Returns:
    Slope angle in degrees, or NaN if not available
    """
    try:
        slope_angle_data = pit.core_info.location.slope_angle
        # slope_angle is returned as [value, units] where units are always 'deg'
        if slope_angle_data and len(slope_angle_data) > 0:
            return float(slope_angle_data[0])
        else:
            return float('nan')
    except (AttributeError, IndexError, TypeError, ValueError):
        # Fall back to NaN if slope_angle is not available or cannot be converted
        return float('nan')


def get_value_safe(obj: Any) -> Optional[float]:
    """
    Safely extract value from object that might be None, scalar, or array-like.
    Helper function for weak layer identification.
    
    Parameters:
    obj: Value to extract (could be None, scalar, list, tuple, or array)
    
    Returns:
    Scalar value or None
    """
    if obj is None:
        return None
    if isinstance(obj, (list, tuple)):
        return obj[0] if len(obj) > 0 else None
    # Handle numpy arrays if present
    if hasattr(obj, '__len__') and hasattr(obj, 'shape'):
        return obj[0] if len(obj) > 0 else None
    return obj


def find_weak_layer_depth(pit: Any, weak_layer_def: str) -> Optional[float]:
    """
    Find the depth of the weak layer based on the specified definition.
    
    Parameters:
    pit: Parsed pit object from caaml_parser
    weak_layer_def: Weak layer definition - one of:
        - "layer_of_concern": Uses layer with layer_of_concern=True
        - "CT_failure_layer": Uses CT test failure layer with Q1/SC/SP fracture character
        - "ECTP_failure_layer": Uses ECT test failure layer with propagation
    
    Returns:
    Depth (from top) of the weak layer in cm, or None if no weak layer found
    
    Notes:
    - For layer_of_concern: Returns the depth_top of the first layer marked as layer_of_concern
    - For CT_failure_layer: Returns the depth_top from the first CT test with Q1/SC/SP fracture character
    - For ECTP_failure_layer: Returns the depth_top from the first ECT test with propagation
    - If multiple weak layers exist, returns the shallowest (smallest depth_top)
    """
    if not hasattr(pit, 'snow_profile') or not pit.snow_profile:
        return None
    
    if weak_layer_def == "layer_of_concern":
        # Find layer marked as layer_of_concern
        if not hasattr(pit.snow_profile, 'layers') or not pit.snow_profile.layers:
            return None
        
        for layer in pit.snow_profile.layers:
            if hasattr(layer, 'layer_of_concern') and layer.layer_of_concern is True:
                depth = get_value_safe(layer.depth_top)
                if depth is not None:
                    return depth
        return None
    
    elif weak_layer_def == "CT_failure_layer":
        # Find CT test failure layer with Q1/SC/SP fracture character
        if not hasattr(pit, 'stability_tests') or not hasattr(pit.stability_tests, 'CT'):
            return None
        
        ct_tests = pit.stability_tests.CT
        if not ct_tests:
            return None
        
        for ct in ct_tests:
            if hasattr(ct, 'fracture_character') and ct.fracture_character in ['Q1', 'SC', 'SP']:
                depth = get_value_safe(ct.depth_top)
                if depth is not None:
                    return depth
        return None
    
    elif weak_layer_def == "ECTP_failure_layer":
        # Find ECT test failure layer with propagation
        if not hasattr(pit, 'stability_tests') or not hasattr(pit.stability_tests, 'ECT'):
            return None
        
        ect_tests = pit.stability_tests.ECT
        if not ect_tests:
            return None
        
        for ect in ect_tests:
            # Check for propagation in both attribute and test_score
            has_propagation = (
                (hasattr(ect, 'propagation') and ect.propagation is True) or
                (hasattr(ect, 'test_score') and ect.test_score and 'ECTP' in str(ect.test_score))
            )
            if has_propagation:
                depth = get_value_safe(ect.depth_top)
                if depth is not None:
                    return depth
        return None
    
    else:
        raise ValueError(
            f"Invalid weak_layer_def '{weak_layer_def}'. "
            f"Valid options: 'layer_of_concern', 'CT_failure_layer', 'ECTP_failure_layer'"
        )


def pit_to_slab_above_weak_layer(
    pit: Any, 
    weak_layer_def: Optional[str] = None,
    depth_tolerance: float = 2.0
) -> Optional[Slab]:
    """
    Convert a snowpilot pit object to a Slab object.
    
    Parameters:
    pit: Parsed pit object from caaml_parser
    weak_layer_def: Weak layer definition (optional) - one of:
        - None: Returns all layers in the pit (no weak layer filtering)
        - "layer_of_concern": Uses layer with layer_of_concern=True
        - "CT_failure_layer": Uses CT test failure layer with Q1/SC/SP fracture character
        - "ECTP_failure_layer": Uses ECT test failure layer with propagation
    depth_tolerance: Tolerance in cm for matching test depths to layer depths (default: 2.0 cm)
    
    Returns:
    Slab object containing layers above the weak layer (or all layers if weak_layer_def=None),
    or None if:
        - No weak layer is found (when weak_layer_def is specified)
        - No valid layers exist above the weak layer
        - The pit contains no valid layers
    
    Notes:
    - If weak_layer_def=None, returns a slab with all layers
    - The slab consists of all layers with depth_top < weak_layer_depth
    - Layers are ordered from top to bottom as they appear in the pit
    - The angle is automatically extracted from pit.core_info.location.slope_angle
      and is NaN if unavailable
    - Density measurements are automatically included when available
    - For stability test definitions (CT/ECTP), depth_tolerance is used to match
      test depths to layer depths (accounts for measurement precision)
    
    Examples:
    >>> # Get slab with all layers (no weak layer filtering)
    >>> slab = pit_to_slab_above_weak_layer(pit)
    >>> 
    >>> # Get slab above the indicated layer of concern
    >>> slab = pit_to_slab_above_weak_layer(pit, "layer_of_concern")
    >>> 
    >>> # Get slab above CT failure layer
    >>> slab = pit_to_slab_above_weak_layer(pit, "CT_failure_layer")
    >>> 
    >>> # Get slab above ECTP failure layer
    >>> slab = pit_to_slab_above_weak_layer(pit, "ECTP_failure_layer")
    >>> 
    >>> if slab:
    >>>     print(f"Slab has {len(slab.layers)} layers above weak layer")
    """
    # Get all layers
    all_layers = pit_to_layers(pit, include_density=True)
    
    if not all_layers:
        return None
    
    # Extract angle from pit
    angle = _extract_angle(pit)
    
    # If no weak layer definition, return all layers
    if weak_layer_def is None:
        return Slab(layers=all_layers, angle=angle)
    
    # Find the weak layer depth
    weak_layer_depth = find_weak_layer_depth(pit, weak_layer_def)
    
    if weak_layer_depth is None:
        return None
    
    # Filter layers above the weak layer
    # Layer is above weak layer if its depth_top < weak_layer_depth
    slab_layers = []
    for layer in all_layers:
        if layer.depth_top is not None and layer.depth_top < weak_layer_depth:
            slab_layers.append(layer)
    
    # Return None if no valid layers above weak layer
    if not slab_layers:
        return None
    
    return Slab(layers=slab_layers, angle=angle)
