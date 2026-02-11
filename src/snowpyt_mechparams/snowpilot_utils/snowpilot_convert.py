"""
CAAML (Snow Profile) data parser and converter.

This module provides functionality to parse CAAML XML files (from SnowPilot
or other sources) and convert them to snowpyt_mechparams data structures.

Workflow
--------
1. Parse CAAML file to get snowpylot SnowPit
2. Create Pit object from snowpylot SnowPit
3. Create Slab from Pit

Example
-------
    >>> from snowpyt_mechparams.snowpilot_utils import parse_caaml_file
    >>> from snowpyt_mechparams.data_structures import Pit
    >>>
    >>> # Step 1: Parse CAAML file
    >>> snow_pit = parse_caaml_file("profile.xml")
    >>>
    >>> # Step 2: Create Pit from snowpylot SnowPit
    >>> pit = Pit.from_snow_pit(snow_pit)
    >>>
    >>> # Step 3: Create Slabs from Pit
    >>> slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    >>> print(f"Created {len(slabs)} slabs")

Additional Utilities
--------------------
This module also provides utility functions for:
- Parsing multiple CAAML files from a directory
- Converting grain form codes for different lookup tables
"""

import logging
import os
from typing import Any, List, Optional

from snowpylot import caaml_parser

from snowpyt_mechparams.snowpilot_utils.snowpilot_constants import resolve_grain_form_for_method

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
        SnowPit object from snowpylot

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
        List of SnowPit objects from snowpylot

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




def convert_grain_form(grain_form_obj: Optional[Any], method: str) -> Optional[str]:
    """
    Convert grain form object to code needed for specified method's lookup table.
    
    This function extracts grain form codes from CAAML grain form objects and
    delegates to the centralized resolve_grain_form_for_method() utility to
    determine which code is valid for the specified method.

    Parameters
    ----------
    grain_form_obj : Optional[Any]
        Grain form object from CAAML data (snowpylot). Should have attributes:
        - sub_grain_class_code (e.g., 'RGmx', 'FCxr', 'PPgp')
        - basic_grain_class_code (e.g., 'RG', 'FC', 'PP')
    method : str
        Method name - one of: "geldsetzer", "kim_jamieson_table2", "kim_jamieson_table5"

    Returns
    -------
    Optional[str]
        Grain form code for the specified method's table lookup, or None if
        not mappable
        
    Notes
    -----
    This function extracts string codes from CAAML objects and uses the
    centralized resolve_grain_form_for_method() utility which is the single
    source of truth for grain form validation logic.
    """
    if grain_form_obj is None:
        return None

    # Try sub_grain_class_code first (more specific, e.g., 'RGmx', 'FCxr')
    sub_code = getattr(grain_form_obj, "sub_grain_class_code", None)
    if sub_code:
        result = resolve_grain_form_for_method(str(sub_code), method)
        if result is not None:
            return result

    # Fall back to basic_grain_class_code (e.g., 'RG', 'FC')
    basic_code = getattr(grain_form_obj, "basic_grain_class_code", None)
    if basic_code:
        return resolve_grain_form_for_method(str(basic_code), method)
    
    return None
