"""
SnowPilot/CAAML XML parser.

This module provides simple parsing utilities for CAAML XML files from the
SnowPilot dataset. For converting parsed data to Layer and Slab objects,
use the Pit class from data_structures.

Workflow
--------
1. Parse CAAML file(s) using parse_caaml_file() or parse_caaml_directory()
2. Create Pit object using Pit.from_snow_pit()
3. Create Slab objects using pit.create_slabs()

Example
-------
    >>> from snowpyt_mechparams.snowpilot import parse_caaml_file
    >>> from snowpyt_mechparams.data_structures import Pit
    >>>
    >>> # Step 1: Parse CAAML file to get snowpylot SnowPit
    >>> snow_pit = parse_caaml_file("profile.xml")
    >>>
    >>> # Step 2: Create Pit from snowpylot SnowPit (extracts layers automatically)
    >>> pit = Pit.from_snow_pit(snow_pit)
    >>>
    >>> # Step 3: Create Slabs from Pit
    >>> slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    >>> print(f"Created {len(slabs)} slabs")
"""

import logging
import os
from typing import Any, List

from snowpylot import caaml_parser

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
