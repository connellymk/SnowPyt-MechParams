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
        
        # Extract grain form from grain_form_primary
        grain_form = None
        if hasattr(layer, 'grain_form_primary') and layer.grain_form_primary:
            grain_form = getattr(layer.grain_form_primary, 'basic_grain_class_code', None)
        
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
            grain_size_avg=grain_size_avg
        )
        
        layers.append(layer_obj)
    
    return layers


def pit_to_slab(pit: Any) -> Optional[Slab]:
    """
    Convert a snowpilot pit object to a Slab object.

    Parameters:
    pit: Parsed pit object from caaml_parser

    Returns:
    Slab object containing all layers from the pit, or None if the pit contains no valid layers

    Notes:
    - Returns None if the pit contains no valid layers (allows graceful skipping in loops)
    - The angle is automatically extracted from pit.core_info.location.slope_angle
      and defaults to 0.0 if unavailable
    - Density measurements are automatically included from the pit's density profile
      when available
    - Layers are ordered from top to bottom as they appear in the pit
    - See pit_to_layers() for details on how layer data is extracted
    
    Example:
    >>> pit = caaml_parser('path/to/snowpit.xml')
    >>> slab = pit_to_slab(pit)
    >>> if slab:
    >>>     print(f"Slab has {len(slab.layers)} layers at {slab.angle}°")
    """
    # Extract angle from pit
    try:
        slope_angle_data = pit.core_info.location.slope_angle
        # slope_angle is returned as [value, units] where units are always 'deg'
        if slope_angle_data and len(slope_angle_data) > 0:
            angle = slope_angle_data[0]
        else:
            angle = 0.0
    except (AttributeError, IndexError, TypeError):
        # Fall back to 0.0 if slope_angle is not available
        angle = 0.0
    
    # Always include density when available
    layers = pit_to_layers(pit, include_density=True)
    
    # Return None if no valid layers (allows graceful skipping in loops)
    if not layers:
        return None
    
    return Slab(layers=layers, angle=angle)
