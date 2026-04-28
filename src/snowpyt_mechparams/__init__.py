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
    methods - Registry and implementations for layer and slab methods
    stability_criteria - Roch and WEAC stability criterion implementations

Parameterization Graph
    graph - Registry-generated directed graph of all available methods
    pathway - Functions and dataclasses for finding calculation pathways

Execution Engine
    ExecutionEngine - Execute calculations across all pathways with dynamic programming
    ExecutionResults - Results from pathway execution with cache statistics

Quick Start
-----------
>>> from snowpyt_mechparams import ExecutionEngine
>>> from snowpyt_mechparams.graph import default_graph
>>> from snowpyt_mechparams.models import Slab, Layer
>>>
>>> # Create slab with measured data
>>> layers = [Layer(thickness=30, density_measured=250, grain_form='RG')]
>>> slab = Slab(layers=layers, angle=35)
>>>
>>> # Execute all pathways to calculate D11
>>> engine = ExecutionEngine()
>>> results = engine.execute_all(slab, target_parameter='D11')
>>> print(f"Computed D11 via {results.successful_pathways} pathways")
>>> print(f"Cache hit rate: {results.cache_stats['hit_rate']:.1%}")
"""

# Data structures
from snowpyt_mechparams.models import Layer, Slab

# Constants
from snowpyt_mechparams.constants import (
    HARDNESS_MAPPING,
    RHO_ICE,
    WEAK_LAYER_DEFINITIONS,
)

# SnowPilot parsing (import module, not individual functions)
from snowpyt_mechparams import snowpilot

# Method calculations
from snowpyt_mechparams.methods.layer import (
    calculate_density,
    calculate_elastic_modulus,
    calculate_poissons_ratio,
    calculate_shear_modulus,
)
from snowpyt_mechparams.methods import (
    MethodRegistry,
    MethodSpec,
    ParameterLevel,
    default_registry,
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

# Stability criteria
from snowpyt_mechparams.stability_criteria import (
    RochResult,
    calculate_roch,
    calculate_shear_stress,
    WeacSkierResult,
    calculate_weac_skier,
)

# Graph and pathway modules (imported as modules, not individual items)
from snowpyt_mechparams import graph
from snowpyt_mechparams import pathway

__version__ = "0.4.0"
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
    # Layer parameter calculations
    "calculate_density",
    "calculate_elastic_modulus",
    "calculate_poissons_ratio",
    "calculate_shear_modulus",
    "MethodRegistry",
    "MethodSpec",
    "ParameterLevel",
    "default_registry",
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
    # Stability criteria
    "RochResult",
    "calculate_roch",
    "calculate_shear_stress",
    "WeacSkierResult",
    "calculate_weac_skier",
    # Graph and pathway (as modules)
    "graph",
    "pathway",
]
