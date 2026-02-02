"""
Constants for SnowPilot/CAAML data parsing and grain form mappings.

These constants define the grain form codes accepted by different
density estimation methods.
"""

# Grain form codes organized by method
GRAIN_FORM_METHODS = {
    "geldsetzer": {
        "sub_grain_class": {"PPgp", "RGmx", "FCmx"},
        "basic_grain_class": {"PP", "DF", "RG", "FC", "DH"},
    },
    "kim_jamieson_table2": {
        "sub_grain_class": {"PPgp", "RGxf", "FCxr", "MFcr"},
        "basic_grain_class": {"PP", "DF", "FC", "DH", "RG"},
    },
    "kim_jamieson_table5": {
        "sub_grain_class": {"FCxr", "PPgp"},
        "basic_grain_class": {"FC", "PP", "DF", "MF"},
    },
}

# Valid weak layer definitions
WEAK_LAYER_DEFINITIONS = ["layer_of_concern", "CT_failure_layer", "ECTP_failure_layer"]
