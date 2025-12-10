"""
Data structures for snow mechanical parameter calculations.

This module provides the core data structures used throughout the package:
- Layer: Represents a single snow layer with physical properties
- Slab: Represents a collection of layers forming a snow slab
- HARDNESS_MAPPING: Mapping from hand hardness strings to numeric indices
"""

from snowpyt_mechparams.data_structures.data_structures import (
    Layer,
    Slab,
    HARDNESS_MAPPING,
    UncertainValue,
)

__all__ = [
    "Layer",
    "Slab",
    "HARDNESS_MAPPING",
    "UncertainValue",
]

