"""
SnowPyt-MechParams: Collaborative Python library for estimating mechanical
parameters from snow pit measurements.

This library provides methods to estimate various mechanical properties of snow
from standard snowpit observations including density, grain size, hardness, and
temperature measurements. Developed through collaboration between multiple
academic researchers and institutions in the snow science community.

Main Components
---------------
Data Structures
    Layer, Slab, Pit - Core data structures for snow profiles

Parameter Calculation
    layer_parameters - Methods for layer-level properties (density, E, ν, G)
    slab_parameters - Methods for slab-level plate theory parameters (A11, B11, D11, A55)

Parameterization Graph
    graph - Directed graph of all available calculation methods
    algorithm - Functions to find all calculation pathways

Execution Engine
    ExecutionEngine - Execute calculations across all pathways with dynamic programming
    ExecutionResults - Results from pathway execution with cache statistics

Quick Start
-----------
>>> from snowpyt_mechparams import ExecutionEngine
>>> from snowpyt_mechparams.graph import graph
>>> from snowpyt_mechparams.data_structures import Slab, Layer
>>>
>>> # Create slab with measured data
>>> layers = [Layer(thickness=30, density_measured=250, grain_form='RG')]
>>> slab = Slab(layers=layers, angle=35)
>>>
>>> # Execute all pathways to calculate D11
>>> engine = ExecutionEngine(graph)
>>> results = engine.execute_all(slab, target_parameter='D11')
>>> print(f"Computed D11 via {results.successful_pathways} pathways")
>>> print(f"Cache hit rate: {results.cache_stats['hit_rate']:.1%}")
"""

# Data structures
from snowpyt_mechparams.data_structures import Layer, Slab

# Constants
from snowpyt_mechparams.constants import HARDNESS_MAPPING, RHO_ICE, WEAK_LAYER_DEFINITIONS

# SnowPilot parsing (import module, not individual functions)
from snowpyt_mechparams import snowpilot

# Layer parameter calculations
from snowpyt_mechparams.layer_parameters.shear_modulus import calculate_shear_modulus

# Weak layer parameters
from snowpyt_mechparams.weak_layer_parameters import (
    calculate_sigma_c_minus,
    calculate_sigma_c_plus,
)

# Execution engine
from snowpyt_mechparams.execution import (
    ExecutionEngine,
    ExecutionConfig,
    ExecutionResults,
    PathwayResult,
    ComputationTrace,
    ComputationCache,
    CacheStats,
    PathwayExecutor,
    MethodDispatcher,
)

# Graph and algorithm modules (imported as modules, not individual items)
from snowpyt_mechparams import graph
from snowpyt_mechparams import algorithm

__version__ = "0.3.0"
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
    "WEAK_LAYER_DEFINITIONS",
    # SnowPilot parsing
    "snowpilot",
    # Calculation functions
    "calculate_shear_modulus",
    "calculate_sigma_c_minus",
    "calculate_sigma_c_plus",
    # Execution engine
    "ExecutionEngine",
    "ExecutionConfig",
    "ExecutionResults",
    "PathwayResult",
    "ComputationTrace",
    "ComputationCache",
    "CacheStats",
    "PathwayExecutor",
    "MethodDispatcher",
    # Graph and algorithm (as modules)
    "graph",
    "algorithm",
]

