# Utility functions for snowpilot data
from typing import Any, Optional

# Constants for grain form codes by method

# Geldsetzer (2000) method codes
GELDSETZER_SUB_GRAIN_CLASS_CODES = {"PPgp", "RGmx", "FCmx"}
GELDSETZER_BASIC_GRAIN_CLASS_CODES = {"PP", "DF", "RG", "FC", "DH"}

# Kim & Jamieson (2014) method codes
KIM_SUB_GRAIN_CLASS_CODES = {"PPgp", "RGxf", "FCxr", "MFcr"}
KIM_BASIC_GRAIN_CLASS_CODES = {"PP", "DF", "FC", "DH", "RG"}


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
    elif method.lower() == "kim":
        sub_codes = KIM_SUB_GRAIN_CLASS_CODES
        basic_codes = KIM_BASIC_GRAIN_CLASS_CODES
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
