"""Configuration objects for execution engine."""

from dataclasses import dataclass


@dataclass
class ExecutionConfig:
    """
    Configuration for parameterization pathway execution.
    
    This class controls execution behavior. The execution engine automatically:
    - Finds ALL valid pathways to the target parameter
    - Uses dynamic programming (caching) for efficiency
    - Computes all dependent parameters (e.g., D11 requires density, E, ν)
    
    Attributes
    ----------
    verbose : bool
        If True, print progress information during execution.
        Useful for debugging or monitoring long-running executions.
        Default: False
        
    Examples
    --------
    Basic usage with defaults (silent execution):
    
    >>> results = engine.execute_all(slab, "density")
    
    With verbose output:
    
    >>> config = ExecutionConfig(verbose=True)
    >>> results = engine.execute_all(slab, "D11", config=config)
    Executing pathway 1/16...
    Executing pathway 2/16...
    ...
    
    Notes
    -----
    The algorithm automatically determines what needs to be computed based on
    the target parameter and the dependency graph. For example:
    - Asking for "density" computes only density pathways
    - Asking for "D11" computes density → E → ν → D11 and all plate theory
      parameters (A11, B11, D11, A55)
    """
    verbose: bool = False
