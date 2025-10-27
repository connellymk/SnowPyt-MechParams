# Utility functions for snowpilot data
import os
from typing import Any, List, Optional

from snowpylot import caaml_parser  # type: ignore

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
