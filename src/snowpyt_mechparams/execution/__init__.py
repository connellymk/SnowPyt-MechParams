"""
Execution module for parameterization pathways.

This module provides the execution engine for running parameterization
pathways on snow pit data. It includes:

- ExecutionEngine: High-level API for executing all parameterizations
- PathwayExecutor: Executes a single parameterization pathway
- MethodDispatcher: Maps method names to implementations
- ExecutionConfig: Configuration for execution behavior
- Result classes: Data structures for storing execution results

Example
-------
>>> from snowpyt_mechparams.execution import ExecutionEngine, ExecutionConfig
>>> from snowpyt_mechparams.models import Slab, Layer
>>>
>>> # Create slab
>>> slab = Slab(
...     layers=[Layer(thickness=30, hand_hardness="4F", grain_form="RG")],
...     angle=35,
... )
>>>
>>> # Execute (config is optional)
>>> engine = ExecutionEngine()
>>> results = engine.execute_all(slab, "density")
>>>
>>> # Iterate results
>>> for pathway_desc, pathway_result in results.pathways.items():
...     print(f"{pathway_desc}: {pathway_result.success}")
"""

from snowpyt_mechparams.execution.cache import ComputationCache, CacheStats
from snowpyt_mechparams.execution.config import ExecutionConfig
from snowpyt_mechparams.execution.context import ExecutionContext
from snowpyt_mechparams.execution.planner import ExecutionPlanner
from snowpyt_mechparams.execution.results import (
    ComputationTrace,
    PathwayResult,
    ExecutionResults,
)
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher
from snowpyt_mechparams.execution.executor import PathwayExecutor
from snowpyt_mechparams.execution.engine import ExecutionEngine
from snowpyt_mechparams.methods import MethodSpec, ParameterLevel

__all__ = [
    # Cache
    "ComputationCache",
    "CacheStats",
    # Configuration
    "ExecutionConfig",
    "ExecutionContext",
    "ExecutionPlanner",
    # Result classes (v2 - simplified)
    "ComputationTrace",
    "PathwayResult",
    "ExecutionResults",
    # Dispatcher classes
    "MethodDispatcher",
    "MethodSpec",
    "ParameterLevel",
    # Executor classes
    "PathwayExecutor",
    "ExecutionEngine",
]
