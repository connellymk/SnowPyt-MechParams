"""
Internal utilities shared across stability criterion implementations.
"""

from typing import Any, Optional


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
