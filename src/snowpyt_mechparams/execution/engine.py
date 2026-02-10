"""
Execution engine for parameterization execution.

This module provides the ExecutionEngine class, which is the high-level API
for executing all parameterizations on a slab with dynamic programming.

The engine manages cache lifecycle across pathway executions, ensuring that:
1. Cache persists across pathways for the same slab (dynamic programming)
2. Cache is cleared between different slabs
3. Cache statistics are collected and reported

This significantly reduces computation time when multiple pathways share
common subpaths (e.g., multiple methods to calculate elastic modulus all
using the same density calculation).
"""

from typing import Optional

from snowpyt_mechparams.algorithm import find_parameterizations
from snowpyt_mechparams.data_structures import Slab
from snowpyt_mechparams.execution.dispatcher import MethodDispatcher
from snowpyt_mechparams.execution.executor import PathwayExecutor
from snowpyt_mechparams.execution.results import ExecutionResults, PathwayResult
from snowpyt_mechparams.graph.structures import Graph, Node


class ExecutionEngine:
    """
    High-level API for executing all parameterizations on a slab.

    This class coordinates finding parameterizations and executing them,
    providing a simple interface for computing all possible parameter
    combinations.

    Attributes
    ----------
    graph : Graph
        The parameter dependency graph
    executor : PathwayExecutor
        The pathway executor for running individual parameterizations

    Examples
    --------
    >>> from algorithm.definitions import graph
    >>> from snowpyt_mechparams.execution import ExecutionEngine
    >>>
    >>> engine = ExecutionEngine(graph)
    >>> results = engine.execute_all(slab, "elastic_modulus")
    >>>
    >>> for pathway_desc, result in results.results.items():
    ...     print(f"{pathway_desc}: {result.success}")
    """

    def __init__(
        self,
        graph: Graph,
        dispatcher: Optional[MethodDispatcher] = None
    ):
        """
        Initialize the ExecutionEngine.

        Parameters
        ----------
        graph : Graph
            The parameter dependency graph
        dispatcher : Optional[MethodDispatcher]
            Method dispatcher to use. If None, creates a new one.
        """
        self.graph = graph
        self.executor = PathwayExecutor(dispatcher)

    def execute_all(
        self,
        slab: Slab,
        target_parameter: str,
        include_plate_theory: bool = True
    ) -> ExecutionResults:
        """
        Execute all possible parameterizations for a target parameter.

        This method finds all possible calculation pathways for the target
        parameter and executes each one on the provided slab. The executor's
        cache persists across pathway executions for the same slab, enabling
        dynamic programming.

        Parameters
        ----------
        slab : Slab
            The input slab with measured values
        target_parameter : str
            The target parameter node name (e.g., "elastic_modulus")
        include_plate_theory : bool
            Whether to also compute A11, B11, D11, A55

        Returns
        -------
        ExecutionResults
            Dictionary-like container with pathway_description -> PathwayResult,
            including cache statistics showing dynamic programming efficiency

        Raises
        ------
        ValueError
            If target_parameter is not found in the graph

        Notes
        -----
        The executor cache is cleared at the start of this method to ensure
        fresh execution for each slab. The cache then persists across all
        pathway executions, avoiding redundant calculations when pathways
        share common subpaths.
        """
        # Clear cache for this slab (fresh execution)
        self.executor.clear_cache()

        # Get the target node
        target_node = self.graph.get_node(target_parameter)
        if target_node is None:
            raise ValueError(f"Unknown target parameter: {target_parameter}")

        # Find all parameterizations
        parameterizations = find_parameterizations(self.graph, target_node)

        # Execute each parameterization (cache persists across pathways)
        results = {}
        successful = 0
        failed = 0

        for param in parameterizations:
            result = self.executor.execute_parameterization(
                parameterization=param,
                slab=slab,
                target_parameter=target_parameter,
                include_plate_theory=include_plate_theory
            )

            results[result.pathway_description] = result

            if result.success:
                successful += 1
            else:
                failed += 1

        # Get cache statistics
        cache_stats = self.executor.get_cache_stats()

        return ExecutionResults(
            target_parameter=target_parameter,
            source_slab=slab,
            results=results,
            total_pathways=len(parameterizations),
            successful_pathways=successful,
            failed_pathways=failed,
            cache_stats=cache_stats  # NEW: Include cache performance
        )

    def execute_single(
        self,
        slab: Slab,
        target_parameter: str,
        methods: dict,
        include_plate_theory: bool = True
    ) -> Optional[PathwayResult]:
        """
        Execute a single specific parameterization pathway.

        This method allows executing a specific combination of methods
        rather than all possible combinations.

        Parameters
        ----------
        slab : Slab
            The input slab with measured values
        target_parameter : str
            The target parameter node name
        methods : dict
            Mapping of parameter -> method to use
            (e.g., {"density": "geldsetzer", "elastic_modulus": "bergfeld"})
        include_plate_theory : bool
            Whether to also compute A11, B11, D11, A55

        Returns
        -------
        Optional[PathwayResult]
            The pathway result if successful, None if the pathway was not found

        Notes
        -----
        This method finds the parameterization that matches the specified
        methods and executes only that one. If no matching parameterization
        is found, returns None.
        """
        # Get the target node
        target_node = self.graph.get_node(target_parameter)
        if target_node is None:
            raise ValueError(f"Unknown target parameter: {target_parameter}")

        # Find all parameterizations
        parameterizations = find_parameterizations(self.graph, target_node)

        # Find the matching parameterization
        for param in parameterizations:
            extracted = self.executor._extract_methods_from_parameterization(param)
            if self._methods_match(extracted, methods):
                return self.executor.execute_parameterization(
                    parameterization=param,
                    slab=slab,
                    target_parameter=target_parameter,
                    include_plate_theory=include_plate_theory
                )

        return None

    def _methods_match(
        self,
        extracted: dict,
        requested: dict
    ) -> bool:
        """
        Check if extracted methods match the requested methods.

        Parameters
        ----------
        extracted : dict
            Methods extracted from a parameterization
        requested : dict
            Methods requested by the user

        Returns
        -------
        bool
            True if all requested methods match
        """
        for param, method in requested.items():
            if param not in extracted:
                return False
            if extracted[param] != method:
                return False
        return True

    def list_available_pathways(
        self,
        target_parameter: str
    ) -> list:
        """
        List all available parameterization pathways for a target parameter.

        Parameters
        ----------
        target_parameter : str
            The target parameter node name

        Returns
        -------
        list
            List of dictionaries describing each pathway
        """
        target_node = self.graph.get_node(target_parameter)
        if target_node is None:
            raise ValueError(f"Unknown target parameter: {target_parameter}")

        parameterizations = find_parameterizations(self.graph, target_node)

        pathways = []
        for param in parameterizations:
            methods = self.executor._extract_methods_from_parameterization(param)
            description = self.executor._build_pathway_description(methods)
            pathway_id = self.executor._build_pathway_id(methods)
            pathways.append({
                "id": pathway_id,
                "description": description,
                "methods": methods
            })

        return pathways
