# Utility functions for snowpilot data
from typing import Any, Optional


def convert_grain_form(grain_form_obj: Optional[Any]) -> Optional[str]:
    """
    Convert grain form object to code needed for Geldsetzer table.

    Parameters:
    grain_form_obj: Grain form object from CAAML data

    Returns:
    str: Grain form code for Geldsetzer table lookup, or None if not mappable
    """
    # Handle None grain form objects
    if grain_form_obj is None:
        return None

    # Check if sub_grain_class_code exists and is in our target codes
    if (hasattr(grain_form_obj, 'sub_grain_class_code') and
        grain_form_obj.sub_grain_class_code and
        grain_form_obj.sub_grain_class_code in ["PPgp", "RGmx", "FCmx"]):
        return str(grain_form_obj.sub_grain_class_code)

    # Otherwise, return basic grain class code if available
    if (hasattr(grain_form_obj, 'basic_grain_class_code') and
            grain_form_obj.basic_grain_class_code):
        return str(grain_form_obj.basic_grain_class_code)

    return None
