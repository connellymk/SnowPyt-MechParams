"""
Domain model classes for snow mechanical parameter calculations.

This module provides the core data models used throughout the package:
- Layer: Represents a single snow layer with physical properties
- WeakLayer: Holds fracture/strength parameters for the WEAC skier criterion
- Slab: Represents a collection of layers forming a snow slab
- Pit: Represents a snow pit profile with layers and stability test data
- UncertainValue: Type alias for values that can be floats or uncertain numbers

For parsing snowpylot SnowPit objects into Pit instances, see pit_parser.parse_pit()
(also accessible via the Pit.from_snow_pit() convenience classmethod).

Notes
-----
HARDNESS_MAPPING is in snowpyt_mechparams.constants but re-exported here for
backwards compatibility. UncertainValue is defined in _types.py but re-exported
from this package for convenience.
"""

from snowpyt_mechparams.models._types import UncertainValue
from snowpyt_mechparams.models.layer import Layer
from snowpyt_mechparams.models.weak_layer import WeakLayer
from snowpyt_mechparams.models.slab import Slab
from snowpyt_mechparams.models.pit import Pit, WeakLayerDef
from snowpyt_mechparams.constants import HARDNESS_MAPPING

__all__ = [
    "Layer",
    "WeakLayer",
    "Pit",
    "WeakLayerDef",
    "Slab",
    "UncertainValue",
    "HARDNESS_MAPPING",  # Re-exported for backwards compatibility
]
