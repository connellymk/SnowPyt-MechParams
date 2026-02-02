"""
SnowPyt-MechParams: Collaborative Python library for estimating mechanical
parameters from snow pit measurements.

This library provides methods to estimate various mechanical properties of snow
from standard snowpit observations including density, grain size, hardness, and
temperature measurements. Developed through collaboration between multiple
academic researchers and institutions in the snow science community.

Main Modules
------------
- data_structures: Core data structures (Layer, Slab)
- models: Mechanical models (static load calculations)
- slab_parameters: Slab mechanical properties (density, modulus, etc.)
- weak_layer_parameters: Weak layer properties (strength, fracture toughness)
- execution: Parameterization pathway execution engine
"""

from snowpyt_mechparams.data_structures import Layer, Slab
from snowpyt_mechparams.constants import HARDNESS_MAPPING, RHO_ICE
from snowpyt_mechparams.slab_parameters.shear_modulus import calculate_shear_modulus
from snowpyt_mechparams.weak_layer_parameters import (
    calculate_sigma_c_minus,
    calculate_sigma_c_plus,
)
from snowpyt_mechparams.execution import (
    ExecutionEngine,
    ExecutionResults,
    PathwayResult,
    PathwayExecutor,
    MethodDispatcher,
)

__version__ = "0.1.0"
__author__ = "Mary Connelly and SnowPyt-MechParams Contributors"
__email__ = "connellymarykate@gmail.com"
__maintainer__ = "SnowPyt-MechParams Contributors"

# Expose common data structures and calculation functions at package level
__all__ = [
    # Data structures
    "Layer",
    "Slab",
    # Constants
    "HARDNESS_MAPPING",
    "RHO_ICE",
    # Calculation functions
    "calculate_shear_modulus",
    "calculate_sigma_c_minus",
    "calculate_sigma_c_plus",
    # Execution engine
    "ExecutionEngine",
    "ExecutionResults",
    "PathwayResult",
    "PathwayExecutor",
    "MethodDispatcher",
]

