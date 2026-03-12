"""Configuration objects for execution engine."""

from dataclasses import dataclass
from typing import Optional


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
    include_method_uncertainty : bool
        If True (default), empirical methods include their regression standard
        error in the output uncertainty. If False, only input measurement
        uncertainties propagate; the method's own standard error is suppressed.
        Default: True
    weac_timeout_seconds : Optional[float]
        Per-slab wall-clock time limit (seconds) for the WEAC coupled criterion
        solver.  If the solver does not finish within this budget the slab is
        treated as a pathway failure and excluded from results.  Only effective
        on POSIX systems (macOS / Linux); silently ignored on Windows.
        ``None`` (default) disables the timeout.  A value of ``5.0`` is a
        reasonable default for large batch runs over real-world datasets.

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

    Without method uncertainty:

    >>> config = ExecutionConfig(include_method_uncertainty=False)
    >>> results = engine.execute_all(slab, "density", config=config)

    With per-slab timeout for large batch runs:

    >>> config = ExecutionConfig(include_method_uncertainty=False, weac_timeout_seconds=5.0)
    >>> results = engine.execute_all(slab, "g_delta", config=config)

    Notes
    -----
    The algorithm automatically determines what needs to be computed based on
    the target parameter and the dependency graph. For example:
    - Asking for "density" computes only density pathways
    - Asking for "D11" computes density → E → ν → D11 and all plate theory
      parameters (A11, B11, D11, A55)
    """
    verbose: bool = False
    include_method_uncertainty: bool = True
    weac_timeout_seconds: Optional[float] = None
