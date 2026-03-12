"""
Models for calculating mechanical loads and forces on snow slabs.

This module provides methods for calculating various mechanical properties
and forces acting on snow slabs, including static loads, force components,
and stability criteria (WEAC skier stability criterion).
"""

from snowpyt_mechparams.stability_models.static_load import calculate_static_load
from snowpyt_mechparams.stability_models.weac import (
    WeacSkierResult,
    calculate_weac_skier,
)

__all__ = [
    "calculate_static_load",
    "WeacSkierResult",
    "calculate_weac_skier",
]

