"""
Execution module for parameterization pathways.

This module provides the execution engine for running parameterization
pathways on snow pit data. It includes:

- ExecutionEngine: High-level API for executing all parameterizations
- PathwayExecutor: Executes a single parameterization pathway
- MethodDispatcher: Maps method names to implementations
- Result classes: Data structures for storing execution results

Example
-------
>>> from algorithm.definitions import graph
>>> from snowpyt_mechparams.execution import ExecutionEngine
>>> from examples.snowpilot_utils import pit_to_slab_above_weak_layer, parse_sample_pits
>>>
>>> # Load data
>>> pits = parse_sample_pits("data")
>>> slab = pit_to_slab_above_weak_layer(pits[0], "layer_of_concern")
>>>
>>> # Execute all pathways
>>> engine = ExecutionEngine(graph)
>>> results = engine.execute_all(slab, target_parameter="elastic_modulus")
>>>
>>> # Iterate results
>>> for pathway_desc, pathway_result in results.results.items():
...     print(f"{pathway_desc}: {pathway_result.success}")
...     for lr in pathway_result.layer_results:
...         print(f"  Layer {lr.layer_index}: E={lr.layer.elastic_modulus}")
"""

from snowpyt_mechparams.execution.results import (
    MethodCall,
    LayerResult,
    SlabResult,
    PathwayResult,
    ExecutionResults
)
from snowpyt_mechparams.execution.dispatcher import (
    MethodDispatcher,
    MethodSpec,
    ParameterLevel
)
from snowpyt_mechparams.execution.executor import PathwayExecutor
from snowpyt_mechparams.execution.engine import ExecutionEngine

__all__ = [
    # Result classes
    "MethodCall",
    "LayerResult",
    "SlabResult",
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
