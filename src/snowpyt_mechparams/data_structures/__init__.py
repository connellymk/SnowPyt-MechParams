"""
Data structures for snow mechanical parameter calculations.

This module provides the core data structures used throughout the package:
- Layer: Represents a single snow layer with physical properties
- Slab: Represents a collection of layers forming a snow slab
- Pit: Represents a snow pit profile with layers and stability test data
- UncertainValue: Type alias for values that can be floats or uncertain numbers

Note: HARDNESS_MAPPING is now in snowpyt_mechparams.constants but is re-exported
here for backwards compatibility.
"""

from snowpyt_mechparams.data_structures.layer import Layer, UncertainValue
from snowpyt_mechparams.data_structures.slab import Slab
from snowpyt_mechparams.data_structures.pit import Pit
from snowpyt_mechparams.constants import HARDNESS_MAPPING

__all__ = [
    "Layer",
    "Pit",
    "Slab",
    "UncertainValue",
    "HARDNESS_MAPPING",  # Re-exported for backwards compatibility
]
