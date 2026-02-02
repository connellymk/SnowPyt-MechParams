# SnowPilot Utilities Module

This module provides utilities for loading and converting SnowPilot/CAAML snow profile data into `snowpyt_mechparams` data structures.

## Modules

### `snowpilot_convert.py`
Functions for parsing SnowPilot/CAAML (Snow Profile) XML files and converting them to `Layer` and `Slab` objects.

**Main Functions:**
- `parse_caaml_file(filepath)` - Parse a single CAAML XML file
- `parse_caaml_directory(directory)` - Parse all CAAML files in a directory
- `caaml_to_layers(caaml_profile)` - Convert CAAML profile to list of Layer objects
- `caaml_to_slab(caaml_profile, weak_layer_def)` - Convert CAAML profile to Slab object
- `convert_grain_form(grain_form_obj, method)` - Convert grain form to method-specific code

### `snowpilot_constants.py`
Constants used for SnowPilot/CAAML data parsing, including grain form code mappings for different density estimation methods.

## Usage Example

```python
from snowpyt_mechparams.snowpilot_utils import parse_caaml_directory, caaml_to_slab

# Parse all CAAML files in a directory
profiles = parse_caaml_directory('data')

# Convert profiles to slabs
for profile in profiles:
    # Get slab above the layer of concern
    slab = caaml_to_slab(profile, weak_layer_def="layer_of_concern")
    
    if slab:
        print(f"Found slab with {len(slab.layers)} layers")
        print(f"Total thickness: {slab.total_thickness} cm")
        print(f"Slope angle: {slab.angle}°")
```

## Weak Layer Definitions

When using `caaml_to_slab()`, you can specify how to identify the weak layer:

- `None` - Returns all layers (no weak layer filtering)
- `"layer_of_concern"` - Uses layer marked as layer_of_concern in the profile
- `"CT_failure_layer"` - Uses CT test failure layer with Q1/SC/SP fracture character
- `"ECTP_failure_layer"` - Uses ECT test failure layer with propagation

## Grain Form Conversion

The `convert_grain_form()` function converts grain form codes to method-specific codes for density estimation:

```python
from snowpyt_mechparams.snowpilot_utils import convert_grain_form

# Convert grain form for Geldsetzer method
grain_code = convert_grain_form(grain_form_obj, "geldsetzer")

# Supported methods:
# - "geldsetzer"
# - "kim_jamieson_table2"
# - "kim_jamieson_table5"
```

## Dependencies

This module requires:
- `snowpylot` - CAAML parser (maintained by the same team)
- `snowpyt_mechparams.data_structures` - Layer and Slab classes

## Future Extensions

This module can be extended to support other data formats:
- CSV files
- JSON formats
- Other snow profile standards
