"""
WEAC skier stability criterion adapter.

Requires weac to be installed:
    pip install snowpyt-mechparams[weac]

Note: UFloat uncertainties are not propagated through WEAC results.
WEAC's eigensystem solver (scipy.linalg.eig) is incompatible with
uncertainties.UFloat; nominal values are used at the adapter boundary.
"""

from snowpyt_mechparams.stability_criteria.weac.weac_result import WeacSkierResult
from snowpyt_mechparams.stability_criteria.weac.weac_criterion import (
    calculate_weac_skier,
)

__all__ = [
    "WeacSkierResult",
    "calculate_weac_skier",
]
