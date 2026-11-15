"""Internal implemented Young's-modulus domains (nominal, inclusive bounds).

Schöttner boundaries were supplied by Jakob Schöttner in author correspondence:
minimum/maximum observed ice volume fractions, converted with 916.7 kg/m³.
These calibration limits do not establish predictive accuracy throughout the
interval. They do not change the 917 kg/m³ normalization used in the equations.
Köchle MF support is an implementation choice: the source reports distinct MF
behavior without providing a separate fit. Preserve that qualified extension.
"""

from typing import Dict, Optional, Tuple

SCHOTTNER_BOUNDARY_ICE_DENSITY = 916.7
SCHOTTNER_VOLUME_FRACTIONS = {
    "SH": (0.074, 0.191),
    "DF": (0.162, 0.388),
    "RG": (0.162, 0.388),
    "FC": (0.164, 0.505),
    "DH": (0.164, 0.505),
}
ELASTIC_DOMAINS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "bergfeld": {g: (110.0, 363.0) for g in ("PP", "DF", "RG")},
    "kochle": {g: (150.0, 450.0) for g in ("RG", "FC", "DH", "MF")},
    "wautier": {g: (103.0, 544.0) for g in ("PP", "DF", "RG", "FC", "DH", "MF")},
    "schottner": {
        g: (a * SCHOTTNER_BOUNDARY_ICE_DENSITY, b * SCHOTTNER_BOUNDARY_ICE_DENSITY)
        for g, (a, b) in SCHOTTNER_VOLUME_FRACTIONS.items()
    },
}


def density_bounds(method: str, grain_form: str) -> Optional[Tuple[float, float]]:
    """Resolve subclasses to the two-character parent; unknown pairs return None."""
    return ELASTIC_DOMAINS.get(method.lower(), {}).get(grain_form[:2].upper())
