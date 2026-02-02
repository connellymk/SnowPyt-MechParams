"""
Data structures for snow mechanical parameter calculations.

This module provides the core data structures used throughout the package:
- Layer: Represents a single snow layer with physical properties
- Slab: Represents a collection of layers forming a snow slab
- UncertainValue: Type alias for values that can be floats or uncertain numbers

Note: HARDNESS_MAPPING is now in snowpyt_mechparams.constants but is re-exported
here for backwards compatibility.
"""

from snowpyt_mechparams.data_structures.data_structures import (
    Layer,
    Slab,
    UncertainValue,
)
from snowpyt_mechparams.constants import HARDNESS_MAPPING

__all__ = [
    "Layer",
    "Slab",
    "UncertainValue",
    "HARDNESS_MAPPING",  # Re-exported for backwards compatibility
]

