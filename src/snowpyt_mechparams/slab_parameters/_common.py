"""Shared helpers for slab parameter calculations.

A11, B11, and D11 all share the same structure:
1. Validate slab (non-empty layers, required properties present)
2. Compute z-coordinates for each layer relative to the slab centroid
3. Calculate plane-strain modulus E_i / (1 - nu_i^2) for each layer
4. Accumulate a weighted sum that differs only in the power of z

This module extracts that shared logic into a single function.
"""

import logging
from typing import Callable

import numpy as np
from uncertainties import ufloat
from uncertainties.core import AffineScalarFunc

from snowpyt_mechparams.data_structures import Slab

logger = logging.getLogger(__name__)


# Type alias: the accumulation function receives
#   (plane_strain_modulus, z_top, z_bottom) and returns the layer contribution.
LayerAccumulator = Callable[
    [AffineScalarFunc, AffineScalarFunc, AffineScalarFunc],
    AffineScalarFunc,
]


def integrate_plane_strain_over_layers(
    slab: Slab,
    accumulate: LayerAccumulator,
    *,
    needs_z_coords: bool = True,
) -> ufloat:
    """Validate *slab*, iterate its layers, and accumulate a weighted sum.

    For each layer the function:
    - Checks that ``elastic_modulus``, ``poissons_ratio``, and ``thickness``
      are present.
    - Validates Poisson's ratio (must satisfy -1 < nu < 1).
    - Computes the plane-strain modulus ``E_i / (1 - nu_i^2)``.
    - Converts layer thickness from cm to mm.
    - Computes z-coordinates of the layer top and bottom relative to the
      slab centroid (z = 0 at centroid, positive upward).
    - Calls ``accumulate(plane_strain_modulus, z_top, z_bottom)`` and adds
      the result to a running sum.

    Parameters
    ----------
    slab : Slab
        Slab with ordered layers (top to bottom).
    accumulate : callable
        ``(plane_strain_modulus, z_top, z_bottom) -> contribution``.
        For A11 (zeroth order), *z_top* and *z_bottom* can be ignored.
    needs_z_coords : bool
        If ``False``, z-coordinate setup is skipped and ``z_top`` / ``z_bottom``
        are passed as ``None``. Use for A11 where only ``h_i`` matters (derived
        from ``z_top - z_bottom`` when coords are present, but more efficient
        when not needed).

    Returns
    -------
    ufloat
        The accumulated result, or ``ufloat(NaN, NaN)`` on invalid input.
    """
    if not slab.layers:
        logger.debug("integrate_plane_strain_over_layers: slab has no layers")
        return ufloat(np.nan, np.nan)

    # z-coordinate setup (only for B11, D11)
    if needs_z_coords:
        total_thickness = slab.total_thickness
        if total_thickness is None:
            logger.debug("integrate_plane_strain_over_layers: slab total_thickness is None")
            return ufloat(np.nan, np.nan)
        h_total_mm = total_thickness * 10.0  # cm → mm
        z_top_surface = h_total_mm / 2.0
        depth_from_top = 0.0  # mm, running accumulator

    result = 0.0

    for i, layer in enumerate(slab.layers):
        # --- Validate required properties ---
        if layer.elastic_modulus is None:
            logger.debug("integrate_plane_strain_over_layers: layer %d missing elastic_modulus", i)
            return ufloat(np.nan, np.nan)
        if layer.poissons_ratio is None:
            logger.debug("integrate_plane_strain_over_layers: layer %d missing poissons_ratio", i)
            return ufloat(np.nan, np.nan)
        if layer.thickness is None:
            logger.debug("integrate_plane_strain_over_layers: layer %d missing thickness", i)
            return ufloat(np.nan, np.nan)

        E_i = layer.elastic_modulus       # MPa = N/mm²
        nu_i = layer.poissons_ratio       # dimensionless
        h_i = layer.thickness * 10.0      # cm → mm

        # --- Validate Poisson's ratio ---
        nu_val = nu_i.nominal_value if hasattr(nu_i, 'nominal_value') else nu_i
        if nu_val >= 1.0 or nu_val < -1.0:
            logger.debug(
                "integrate_plane_strain_over_layers: layer %d Poisson's ratio %.3f outside valid range (-1, 1)",
                i,
                nu_val,
            )
            return ufloat(np.nan, np.nan)

        # --- Plane-strain modulus ---
        plane_strain_modulus = E_i / (1.0 - nu_i ** 2)

        # --- z-coordinates ---
        if needs_z_coords:
            z_top = z_top_surface - depth_from_top
            z_bottom = z_top_surface - (depth_from_top + h_i)
            depth_from_top += h_i
        else:
            z_top = None
            z_bottom = None

        # --- Accumulate ---
        result += accumulate(plane_strain_modulus, z_top, z_bottom)

    return result
