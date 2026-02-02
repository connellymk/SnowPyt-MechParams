"""
Example script demonstrating the snowpyt_mechparams.snowpilot_utils module.

This shows how to load SnowPilot/CAAML data and convert it to Layer and Slab objects
using the SnowPilot utilities module.
"""

from snowpyt_mechparams.snowpilot_utils import (
    caaml_to_layers,
    caaml_to_slab,
    convert_grain_form,
    parse_caaml_directory,
    parse_caaml_file,
)


def example_parse_directory():
    """Example: Parse all CAAML files in a directory."""
    print("=" * 60)
    print("Example 1: Parse directory of CAAML files")
    print("=" * 60)
    
    # Parse all XML files in the data directory
    profiles = parse_caaml_directory('data')
    
    print(f"✅ Successfully loaded {len(profiles)} profiles")
    print()


def example_convert_to_layers():
    """Example: Convert a CAAML profile to Layer objects."""
    print("=" * 60)
    print("Example 2: Convert CAAML to Layers")
    print("=" * 60)
    
    # Parse one file
    profiles = parse_caaml_directory('data')
    if not profiles:
        print("❌ No profiles found")
        return
    
    profile = profiles[0]
    
    # Convert to layers
    layers = caaml_to_layers(profile, include_density=True)
    
    print(f"✅ Converted profile to {len(layers)} layers")
    if layers:
        print(f"\nFirst layer:")
        print(f"  - Depth: {layers[0].depth_top} cm")
        print(f"  - Thickness: {layers[0].thickness} cm")
        print(f"  - Grain form: {layers[0].grain_form}")
        print(f"  - Hand hardness: {layers[0].hand_hardness}")
    print()


def example_convert_to_slab():
    """Example: Convert a CAAML profile to a Slab object."""
    print("=" * 60)
    print("Example 3: Convert CAAML to Slab")
    print("=" * 60)
    
    # Parse one file
    profiles = parse_caaml_directory('data')
    if not profiles:
        print("❌ No profiles found")
        return
    
    profile = profiles[0]
    
    # Convert to slab (all layers, no weak layer filtering)
    slab_all = caaml_to_slab(profile)
    
    if slab_all:
        print(f"✅ Slab with all layers:")
        print(f"  - Number of layers: {len(slab_all.layers)}")
        print(f"  - Total thickness: {slab_all.total_thickness} cm")
        print(f"  - Slope angle: {slab_all.angle}°")
    
    # Try to get slab above layer of concern
    slab_loc = caaml_to_slab(profile, weak_layer_def="layer_of_concern")
    
    if slab_loc:
        print(f"\n✅ Slab above layer of concern:")
        print(f"  - Number of layers: {len(slab_loc.layers)}")
        print(f"  - Total thickness: {slab_loc.total_thickness} cm")
    else:
        print(f"\n⚠️  No layer of concern found in this profile")
    print()


def example_grain_form_conversion():
    """Example: Convert grain form codes."""
    print("=" * 60)
    print("Example 4: Grain Form Conversion")
    print("=" * 60)
    
    # Parse one file
    profiles = parse_caaml_directory('data')
    if not profiles:
        print("❌ No profiles found")
        return
    
    profile = profiles[0]
    
    # Get layers
    if not hasattr(profile, 'snow_profile') or not profile.snow_profile.layers:
        print("❌ No layers in profile")
        return
    
    layer = profile.snow_profile.layers[0]
    
    if hasattr(layer, 'grain_form_primary') and layer.grain_form_primary:
        print(f"Original grain form:")
        print(f"  - Basic: {getattr(layer.grain_form_primary, 'basic_grain_class_code', None)}")
        print(f"  - Sub: {getattr(layer.grain_form_primary, 'sub_grain_class_code', None)}")
        
        # Convert for different methods
        for method in ["geldsetzer", "kim_jamieson_table2", "kim_jamieson_table5"]:
            code = convert_grain_form(layer.grain_form_primary, method)
            print(f"\n  - {method}: {code}")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 5 + "SnowPyt-MechParams SnowPilot Utils Examples" + " " * 6 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        example_parse_directory()
        example_convert_to_layers()
        example_convert_to_slab()
        example_grain_form_conversion()
        
        print("=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nMake sure:")
        print("  1. You're in the examples/ directory")
        print("  2. The data/ directory exists with CAAML XML files")
        print("  3. snowpyt_mechparams is installed: pip install -e .")


if __name__ == "__main__":
    main()
