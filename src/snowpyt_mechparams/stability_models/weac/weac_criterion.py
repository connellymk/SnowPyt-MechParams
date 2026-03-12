"""
WEAC skier stability criterion adapter.

Converts a SnowPyt ``Slab`` (with computed layer mechanical parameters and
populated ``weac_layer`` fracture/strength parameters) into WEAC inputs and
runs the coupled anticrack nucleation criterion.

Units at the SnowPyt / WEAC boundary
--------------------------------------
SnowPyt uses SI-derived units per-field:
  - thickness / depth: cm
  - density: kg/m³
  - elastic modulus: MPa
  - shear modulus: MPa
  - Poisson's ratio: dimensionless
  - slope angle: degrees

WEAC expects:
  - thickness: mm
  - density: kg/m³   (same)
  - elastic modulus: MPa  (same)
  - shear modulus: MPa    (same)
  - Poisson's ratio: dimensionless  (same)
  - slope angle (phi): degrees  (same)

The only unit conversion required is **thickness: cm → mm (× 10)**.

UFloat handling
---------------
All ``uncertainties.UFloat`` values are stripped to their nominal float value
at this adapter boundary.  WEAC's internal solver (scipy.linalg.eig) is not
compatible with UFloat arithmetic.
"""

from __future__ import annotations

import signal
import sys
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Lazy import guard — weac is an optional dependency.
# This module is importable even without weac; the error is raised only when
# calculate_weac_skier is *called*.
# ---------------------------------------------------------------------------
try:
    import weac as _weac_pkg  # noqa: F401  (presence check only)
    from weac.analysis import Analyzer, CriteriaEvaluator
    from weac.components import (
        CriteriaConfig,
        ModelInput,
        ScenarioConfig,
        Segment,
    )
    from weac.components.layer import Layer as WeacLayer
    from weac.components.layer import WeakLayer as WeacWeakLayer
    from weac.core.system_model import SystemModel

    _WEAC_AVAILABLE = True
except ImportError:
    _WEAC_AVAILABLE = False

from snowpyt_mechparams.data_structures import Slab
from snowpyt_mechparams.stability_models.weac.weac_result import WeacSkierResult


def _nominal(v: Any) -> Optional[float]:
    """
    Strip ``uncertainties.UFloat`` to its nominal float value.

    Parameters
    ----------
    v : Any
        A ``float``, ``UFloat``, or ``None``.

    Returns
    -------
    Optional[float]
        ``float(v.nominal_value)`` for UFloat, ``float(v)`` for plain
        numeric types, ``None`` if *v* is ``None``.
    """
    if v is None:
        return None
    if hasattr(v, "nominal_value"):
        return float(v.nominal_value)
    return float(v)


class _WeacTimeout(Exception):
    """Raised by the SIGALRM handler when a per-slab timeout fires."""


def _sigalrm_handler(signum: int, frame: object) -> None:  # noqa: ARG001
    raise _WeacTimeout("weac evaluation timed out")


def calculate_weac_skier(
    slab: Slab,
    skier_mass: float = 80.0,
    segment_length: Optional[float] = None,
    timeout_seconds: Optional[float] = None,
    **weak_layer_overrides: Any,
) -> Optional[WeacSkierResult]:
    """
    Run the WEAC coupled skier criterion on a SnowPyt ``Slab``.

    The adapter converts SnowPyt's layer mechanical parameters and weak-layer
    fracture/strength data into WEAC inputs, runs the coupled anticrack
    nucleation criterion, and returns a ``WeacSkierResult``.

    Parameters
    ----------
    slab : Slab
        SnowPyt slab with:

        * All layers having ``density_calculated``, ``elastic_modulus``,
          ``poissons_ratio``, ``shear_modulus``, and ``thickness`` populated.
        * ``weak_layer`` set (provides ``rho`` and ``h`` for WEAC's WeakLayer).
        * ``weac_layer`` set (provides fracture/strength params).
        * ``angle`` set (slope angle in degrees).

    skier_mass : float, optional
        Skier mass in kg.  Default 80.0 kg.
    segment_length : float, optional
        Half-segment length for the WEAC model in mm.  If ``None``, derived
        from ``slab.total_thickness × 10`` (cm → mm).
    timeout_seconds : float, optional
        Wall-clock time limit for the WEAC solver per slab (seconds).  If the
        coupled criterion does not finish within this budget the slab is treated
        as a pathway failure and ``None`` is returned.  Only supported on
        POSIX systems (macOS / Linux) where ``signal.SIGALRM`` is available;
        ignored silently on Windows.  A value of ``5.0`` is a reasonable
        default for large batch runs.
    **weak_layer_overrides
        Override individual weak-layer fracture/strength parameters passed to
        WEAC (e.g. ``G_Ic=1.0``).  These take precedence over ``slab.weac_layer``.

    Returns
    -------
    Optional[WeacSkierResult]
        Result object, or ``None`` if any required input is missing, the WEAC
        solver exceeds ``timeout_seconds``, or a ``RecursionError`` is raised
        by the iterative solver.

    Raises
    ------
    ImportError
        If the ``weac`` package is not installed.
        Install with: ``pip install snowpyt-mechparams[weac]``
    """
    # ------------------------------------------------------------------
    # 1. Validate required inputs
    #    Validation happens before the WEAC availability check so that
    #    missing-input paths return None even when weac is not installed.
    # ------------------------------------------------------------------

    # Slope angle
    phi = _nominal(slab.angle)
    if phi is None:
        return None

    # Weak layer (for rho and h supplied to WEAC)
    if slab.weak_layer is None:
        return None
    wl_rho = _nominal(slab.weak_layer.density_measured)
    if wl_rho is None:
        wl_rho = _nominal(getattr(slab.weak_layer, "density_calculated", None))
    if wl_rho is None:
        return None
    wl_h = _nominal(slab.weak_layer.thickness)
    if wl_h is None:
        return None
    wl_h_mm = wl_h * 10.0  # cm → mm

    # Slab layers — all must have the four mechanical params + thickness
    weac_layers = []
    for layer in slab.layers:
        rho = _nominal(layer.density_calculated)
        if rho is None:
            return None
        h = _nominal(layer.thickness)
        if h is None:
            return None
        h_mm = h * 10.0  # cm → mm
        E = _nominal(layer.elastic_modulus)
        if E is None:
            return None
        G = _nominal(layer.shear_modulus)
        if G is None:
            return None
        nu = _nominal(layer.poissons_ratio)
        if nu is None:
            return None
        weac_layers.append(WeacLayer(rho=rho, h=h_mm, E=E, G=G, nu=nu))

    # ------------------------------------------------------------------
    # 1b. WEAC availability check (deferred until after input validation
    #     so that missing-input paths return None even without weac).
    # ------------------------------------------------------------------

    if not _WEAC_AVAILABLE:
        raise ImportError(
            "The 'weac' package is required to run the skier stability criterion.\n"
            "Install it with:  pip install snowpyt-mechparams[weac]\n"
            "or install the optional dependency group:  pip install 'snowpyt-mechparams[weac]'"
        )

    # ------------------------------------------------------------------
    # 2. Fracture / strength parameters for WEAC WeakLayer
    #    Priority: kwargs > slab.weac_layer > WEAC built-in defaults
    # ------------------------------------------------------------------

    weac_wl_kwargs: dict[str, Any] = {"rho": wl_rho, "h": wl_h_mm}

    if slab.weac_layer is not None:
        wl = slab.weac_layer
        for attr, weac_field in [
            ("G_c",        "G_c"),
            ("G_Ic",       "G_Ic"),
            ("G_IIc",      "G_IIc"),
            ("sigma_c",    "sigma_c"),
            ("tau_c",      "tau_c"),
            ("sigma_comp", "sigma_comp"),
        ]:
            val = _nominal(getattr(wl, attr, None))
            if val is not None:
                weac_wl_kwargs[weac_field] = val

    # Caller overrides take precedence
    for key, val in weak_layer_overrides.items():
        weac_wl_kwargs[key] = float(val) if val is not None else val

    weac_weak_layer = WeacWeakLayer(**weac_wl_kwargs)

    # ------------------------------------------------------------------
    # 3. Segment length
    # ------------------------------------------------------------------

    if segment_length is None:
        total_h = _nominal(slab.total_thickness)
        if total_h is None:
            return None
        L = total_h * 10.0  # cm → mm
    else:
        L = float(segment_length)

    # ------------------------------------------------------------------
    # 4. Build WEAC ModelInput → SystemModel
    # ------------------------------------------------------------------

    scenario_config = ScenarioConfig(phi=phi, system_type="skiers")

    segments = [
        Segment(length=L, has_foundation=True, m=skier_mass),
        Segment(length=L, has_foundation=True, m=0.0),
    ]

    model_input = ModelInput(
        weak_layer=weac_weak_layer,
        layers=weac_layers,
        scenario_config=scenario_config,
        segments=segments,
    )

    system = SystemModel(model_input)

    # ------------------------------------------------------------------
    # 5. Run coupled criterion
    #
    # Guard against two failure modes that occur on numerically pathological
    # slabs:
    #
    #   RecursionError — evaluate_coupled_criterion recurses with
    #       damping_ERR+1 on each non-convergence pass; for some inputs it
    #       descends hundreds of levels before Python's stack limit is hit.
    #
    #   _WeacTimeout — on POSIX systems (macOS / Linux) an optional
    #       SIGALRM fires after timeout_seconds so that a slow-converging
    #       slab does not stall an entire batch loop.  On Windows (no
    #       SIGALRM) the timeout is silently skipped.
    #
    # Both cases return None, which the dispatcher treats as pathway failure.
    # ------------------------------------------------------------------

    _use_timeout = (
        timeout_seconds is not None
        and sys.platform != "win32"
        and hasattr(signal, "SIGALRM")
    )

    _old_handler: Any = None
    try:
        if _use_timeout:
            _old_handler = signal.signal(signal.SIGALRM, _sigalrm_handler)
            signal.setitimer(signal.ITIMER_REAL, float(timeout_seconds))  # type: ignore[arg-type]

        evaluator = CriteriaEvaluator(CriteriaConfig())
        result = evaluator.evaluate_coupled_criterion(system)

    except (RecursionError, _WeacTimeout):
        return None
    finally:
        if _use_timeout:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            if _old_handler is not None:
                signal.signal(signal.SIGALRM, _old_handler)

    # ------------------------------------------------------------------
    # 6. Extract G_I / G_II from the final system at the critical point
    #    incremental_ERR returns [G_total, G_I, G_II, 0] (confirmed from source)
    # ------------------------------------------------------------------

    analyzer = Analyzer(result.final_system)
    arr = analyzer.incremental_ERR(unit="J/m^2")
    G_total = float(arr[0])
    G_I = float(arr[1])
    G_II = float(arr[2])

    return WeacSkierResult(
        g_delta=float(result.g_delta),
        converged=bool(result.converged),
        G_I=G_I,
        G_II=G_II,
        G_total=G_total,
        critical_skier_weight=float(result.critical_skier_weight),
        crack_length=float(result.crack_length),
        max_dist_stress=float(result.max_dist_stress),
        min_dist_stress=float(result.min_dist_stress),
        dist_ERR_envelope=float(result.dist_ERR_envelope),
        segment_length=L,
        skier_mass=float(skier_mass),
    )
