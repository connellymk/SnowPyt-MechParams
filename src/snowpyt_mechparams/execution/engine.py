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
from snowpyt_mechparams.execution.cache import ComputationCache
from snowpyt_mechparams.execution.config import ExecutionConfig
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
        dispatcher: Optional[MethodDispatcher] = None,
        cache: Optional[ComputationCache] = None
    ):
        """
        Initialize the ExecutionEngine.

        Parameters
        ----------
        graph : Graph
            The parameter dependency graph
        dispatcher : Optional[MethodDispatcher]
            Method dispatcher to use. If None, creates a new one.
        cache : Optional[ComputationCache]
            Shared cache for all executions. If None, creates a new one.
            
        Notes
        -----
        The cache is shared across all execute_all() calls, but is cleared
        at the start of each execute_all() to ensure fresh execution per slab.
        """
        self.graph = graph
        self.cache = cache or ComputationCache()
        self.executor = PathwayExecutor(dispatcher, self.cache)

    def execute_all(
        self,
        slab: Slab,
        target_parameter: str,
        config: Optional[ExecutionConfig] = None
    ) -> ExecutionResults:
        """
        Execute all possible calculation pathways for a target parameter.

        The algorithm automatically:
        1. Finds ALL valid pathways from measured data to the target parameter
        2. Executes each pathway on the provided slab
        3. Uses dynamic programming (caching) to avoid redundant calculations
        4. Computes all dependent parameters as needed

        Parameters
        ----------
        slab : Slab
            The input slab with measured values (not modified)
        target_parameter : str
            What you want to compute. Examples:
            - "density": Finds all ways to estimate density
            - "elastic_modulus": Finds all ways (via density) to compute E
            - "D11": Finds all ways to compute D11 (density → E → ν → D11)
              and all other plate theory parameters (A11, B11, A55)
        config : Optional[ExecutionConfig]
            Configuration for execution behavior (verbose output, etc.)
            If None, uses defaults (silent execution)

        Returns
        -------
        ExecutionResults
            Container with all pathway results and cache statistics

        Raises
        ------
        ValueError
            If target_parameter is not found in the graph

        Notes
        -----
        **Dynamic Programming**: The cache is cleared at the start for this slab,
        then persists across all pathway executions. When multiple pathways share
        common calculations (e.g., all elastic modulus methods need density),
        cached values avoid redundant work.
        
        **Automatic Dependencies**: You only specify what you want. The algorithm
        determines what intermediate parameters are needed. For example:
        - Ask for "density" → computes only density
        - Ask for "D11" → computes density, E, ν, then D11 (and A11, B11, A55)
        
        Examples
        --------
        Compute density using all available methods:
        
        >>> results = engine.execute_all(slab, "density")
        >>> print(f"{results.successful_pathways}/{results.total_pathways} succeeded")
        
        Compute D11 with verbose output:
        
        >>> config = ExecutionConfig(verbose=True)
        >>> results = engine.execute_all(slab, "D11", config=config)
        Executing pathway 1/16...
        Executing pathway 2/16...
        ...
        
        Access results:
        
        >>> for desc, pathway in results.get_successful_pathways().items():
        ...     print(f"{desc}: D11 = {pathway.slab.D11}")
        """
        # Use default config if not provided
        if config is None:
            config = ExecutionConfig()
        
        # Clear cache for this slab (fresh execution with dynamic programming)
        self.executor.clear_cache()

        # Get the target node
        target_node = self.graph.get_node(target_parameter)
        if target_node is None:
            raise ValueError(f"Unknown target parameter: {target_parameter}")

        # Find all parameterizations (algorithm determines what's needed).
        # find_parameterizations already deduplicates by method fingerprint,
        # so every entry here represents a genuinely distinct calculation.
        parameterizations = find_parameterizations(self.graph, target_node)

        # Execute each parameterization (cache persists across pathways)
        results = {}

        for idx, param in enumerate(parameterizations):
            if config.verbose:
                print(f"Executing pathway {idx + 1}/{len(parameterizations)}...")
            
            result = self.executor.execute_parameterization(
                parameterization=param,
                slab=slab,
                target_parameter=target_parameter,
                config=config
            )

            results[result.pathway_description] = result

        # Get cache statistics
        cache_stats = self.executor.get_cache_stats()

        return ExecutionResults(
            target_parameter=target_parameter,
            source_slab=slab,
            pathways=results,
            cache_stats=cache_stats
        )

    def execute_single(
        self,
        slab: Slab,
        target_parameter: str,
        methods: dict,
        config: Optional[ExecutionConfig] = None
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
        config : Optional[ExecutionConfig]
            Configuration controlling execution behavior. If None, uses defaults.

        Returns
        -------
        Optional[PathwayResult]
            The pathway result if successful, None if the pathway was not found

        Notes
        -----
        This method clears the cache before executing, so it is safe to call
        after execute_all (or another execute_single) on a different slab
        without carrying over stale cached density values.

        This method finds the parameterization that matches the specified
        methods and executes only that one. If no matching parameterization
        is found, returns None.
        
        Examples
        --------
        >>> methods = {"density": "geldsetzer", "elastic_modulus": "bergfeld"}
        >>> result = engine.execute_single(slab, "elastic_modulus", methods)
        """
        # Use default config if not provided
        if config is None:
            config = ExecutionConfig()

        # Clear cache for this slab so stale values from a prior execute_all
        # (on a different slab) don't pollute this single-pathway execution.
        self.executor.clear_cache()

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
                    config=config
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
