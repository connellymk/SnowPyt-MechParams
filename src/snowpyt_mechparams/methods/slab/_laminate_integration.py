"""Shared helpers for slab parameter calculations.

A11, B11, and D11 all share the same structure:
1. Validate slab (non-empty layers, required properties present)
2. Compute z-coordinates for each layer relative to the slab centroid
3. Calculate plane-strain modulus E_i / (1 - nu_i^2) for each layer
4. Accumulate a weighted sum that differs only in the power of z

This module extracts that shared logic into a single function.
"""

import logging
from typing import Callable, Union

import numpy as np
from uncertainties import ufloat
from uncertainties.core import AffineScalarFunc

from snowpyt_mechparams.models import Slab, UncertainValue

logger = logging.getLogger(__name__)


# Type alias: the accumulation function receives
#   (plane_strain_modulus, z_top, z_bottom) and returns the layer contribution.
# Arguments may be plain float or AffineScalarFunc depending on whether
# the layer properties carry uncertainty.
_Numeric = Union[float, AffineScalarFunc]
LayerAccumulator = Callable[
    [_Numeric, _Numeric, _Numeric],
    _Numeric,
]


def integrate_plane_strain_over_layers(
    slab: Slab,
    accumulate: LayerAccumulator,
) -> UncertainValue:
    """Validate *slab*, iterate its layers, and accumulate a weighted sum.

    For each layer the function:
    - Checks that ``elastic_modulus``, ``poissons_ratio``, ``thickness``,
      and ``depth_top`` are present.
    - Validates Poisson's ratio (must satisfy -1 < nu < 1).
    - Computes the plane-strain modulus ``E_i / (1 - nu_i^2)``.
    - Converts layer thickness from cm to mm.
    - Reads ``layer.depth_top`` (measured depth from snow surface in cm) to
      compute z-coordinates relative to the slab midplane (z = 0 at midplane,
      positive upward). Returns ``ufloat(NaN, NaN)`` if any layer is missing
      ``depth_top``. For A11 the z-coordinates cancel (``z_top - z_bottom =
      h_i``); B11 and D11 depend on the actual z-positions.
    - Calls ``accumulate(plane_strain_modulus, z_top, z_bottom)`` and adds
      the result to a running sum.

    Parameters
    ----------
    slab : Slab
        Slab with ordered layers (top to bottom). All layers must have
        ``depth_top`` set so that z-coordinates can be anchored to the
        measured snow profile.
    accumulate : callable
        ``(plane_strain_modulus, z_top, z_bottom) -> contribution``.
        For A11 (zeroth order), ``h_i = z_top - z_bottom`` gives the layer
        thickness. For B11 (first order) and D11 (second order), the full
        z-coordinates are used directly.

    Returns
    -------
    ufloat
        The accumulated result, or ``ufloat(NaN, NaN)`` on invalid input.
    """
    if not slab.layers:
        logger.debug("integrate_plane_strain_over_layers: slab has no layers")
        return ufloat(np.nan, np.nan)

    total_thickness = slab.total_thickness
    if total_thickness is None:
        logger.debug("integrate_plane_strain_over_layers: slab total_thickness is None")
        return ufloat(np.nan, np.nan)

    h_total_mm = total_thickness * 10.0  # cm → mm

    # Reference plane: midplane of the slab.
    # When depth_top is available on all layers, use measured snowpack positions
    # so that gaps between layers are reflected in the z-coordinates.
    # Fall back to cumulative thickness when depth_top is absent (e.g. for A11,
    # where z_top - z_bottom = h_i regardless of the reference frame).
    use_depth_top = slab.layers[0].depth_top is not None
    if use_depth_top:
        slab_top_mm = slab.layers[0].depth_top * 10.0  # cm → mm
        z_ref = slab_top_mm + h_total_mm / 2.0
    else:
        z_ref = h_total_mm / 2.0  # geometric midplane, depth_from_top = 0

    depth_from_top = 0.0  # mm, used only in cumulative fallback
    result = 0.0

    for i, layer in enumerate(slab.layers):
        # --- Validate required properties ---
        if layer.elastic_modulus is None:
            logger.debug(
                "integrate_plane_strain_over_layers: layer %d missing elastic_modulus",
                i,
            )
            return ufloat(np.nan, np.nan)
        if layer.poissons_ratio is None:
            logger.debug(
                "integrate_plane_strain_over_layers: layer %d missing poissons_ratio", i
            )
            return ufloat(np.nan, np.nan)
        if layer.thickness is None:
            logger.debug(
                "integrate_plane_strain_over_layers: layer %d missing thickness", i
            )
            return ufloat(np.nan, np.nan)

        E_i = layer.elastic_modulus  # MPa = N/mm²
        nu_i = layer.poissons_ratio  # dimensionless
        h_i = layer.thickness * 10.0  # cm → mm

        # --- Validate Poisson's ratio ---
        nu_val = nu_i.nominal_value if hasattr(nu_i, "nominal_value") else nu_i
        if nu_val >= 1.0 or nu_val < -1.0:
            logger.debug(
                "integrate_plane_strain_over_layers: layer %d Poisson's ratio %.3f outside valid range (-1, 1)",
                i,
                nu_val,
            )
            return ufloat(np.nan, np.nan)

        # --- Plane-strain modulus ---
        plane_strain_modulus = E_i / (1.0 - nu_i**2)

        # --- z-coordinates relative to slab midplane ---
        if use_depth_top:
            depth_top_mm = layer.depth_top * 10.0  # cm → mm
            z_top = z_ref - depth_top_mm
            z_bottom = z_ref - (depth_top_mm + h_i)
        else:
            z_top = z_ref - depth_from_top
            z_bottom = z_ref - (depth_from_top + h_i)
            depth_from_top += h_i

        # --- Accumulate ---
        result += accumulate(plane_strain_modulus, z_top, z_bottom)

    return result
