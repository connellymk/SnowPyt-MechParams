# WeacSkierResult — pure dataclass, no WEAC import required.
#
# This module is safe to import even when weac is not installed.
# The adapter (weac_criterion.py) performs the lazy import.

from dataclasses import dataclass


@dataclass
class WeacSkierResult:
    """
    Results of a WEAC skier coupled criterion evaluation.

    All values are plain floats (UFloat uncertainties from SnowPyt inputs are
    stripped at the adapter boundary; WEAC's eigensystem solver is incompatible
    with uncertainties.UFloat).

    Attributes
    ----------
    g_delta : float
        Coupled stability criterion value (≥ 1.0 = anticrack nucleation likely).
    converged : bool
        Whether the coupled criterion algorithm converged.
    G_I : float
        Mode-I energy release rate at the critical configuration [J/m²].
        Extracted from ``Analyzer(result.final_system).incremental_ERR()[1]``.
    G_II : float
        Mode-II energy release rate at the critical configuration [J/m²].
        Extracted from ``Analyzer(result.final_system).incremental_ERR()[2]``.
    G_total : float
        Total energy release rate G_I + G_II [J/m²].
        Extracted from ``Analyzer(result.final_system).incremental_ERR()[0]``.
    critical_skier_weight : float
        Skier mass at which anticrack nucleation occurs [kg].
        Stored as mass despite the "weight" name — this mirrors the field name
        used by ``weac.analysis.CoupledCriterionResult.critical_skier_weight``.
    crack_length : float
        Anticrack half-length at the critical configuration [mm].
    max_dist_stress : float
        Maximum distance to the stress failure envelope (from WEAC).
    min_dist_stress : float
        Minimum distance to the stress failure envelope (from WEAC).
    max_dist_ERR_envelope : float
        Maximum distance to the energy release rate (ERR) failure envelope
        (from WEAC).  Named consistently with ``max_dist_stress`` /
        ``min_dist_stress``; WEAC's own field is ``dist_ERR_envelope``.
    segment_length : float
        Segment length used in the WEAC model [mm].
    skier_mass : float
        Skier mass used in the WEAC model [kg].
    """

    g_delta: float
    converged: bool
    G_I: float
    G_II: float
    G_total: float
    critical_skier_weight: float
    crack_length: float
    max_dist_stress: float
    min_dist_stress: float
    max_dist_ERR_envelope: float
    segment_length: float
    skier_mass: float
