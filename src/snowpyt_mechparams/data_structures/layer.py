# Layer data structure for snow mechanical parameter calculations

from dataclasses import dataclass
from typing import Optional, Union

import uncertainties

from snowpyt_mechparams.constants import (
    HARDNESS_MAPPING,
    U_HAND_HARDNESS_INDEX,
)
from uncertainties import ufloat as _ufloat

# Type alias for values that can be floats or uncertain numbers
UncertainValue = Union[float, uncertainties.UFloat]


@dataclass
class Layer:
    """
    Represents a snow layer with thickness and density.

    Values can be regular floats or uncertain numbers (ufloat) from the
    uncertainties package. When using uncertain numbers, uncertainties will
    automatically propagate through calculations.

    Attributes
    ----------
    # Field Measurements
    depth_top: Union[float, uncertainties.UFloat]
        Layer depth from the top of the snowpack in centimeters (cm). Can include uncertainty.
    thickness: Union[float, uncertainties.UFloat]
        Layer thickness in centimeters (cm). Can include uncertainty.
    density_measured: Union[float, uncertainties.UFloat]
        Layer density measured directly in kilograms per cubic meter (kg/m³). Can include uncertainty.
    hand_hardness: str
        Layer hand hardness
    grain_form: str
        Grain form code: sub-grain class (e.g., 'FCxr', 'PPgp', 'RGmx') if available,
        otherwise basic class (e.g., 'FC', 'PP', 'RG')
    grain_size_avg: Union[float, uncertainties.UFloat]
        Average grain size in millimeters (mm). Can include uncertainty.
    layer_of_concern: bool
        Whether this layer is marked as layer of concern (default: False)


    # Calculated Parameters

    ## From Field Measurements
    depth_bottom: Union[float, uncertainties.UFloat]
        Location of the bottom of the layer in centimeters (cm). Can include uncertainty.
    hand_hardness_index: Union[float, uncertainties.UFloat]
        Hand hardness index of the layer.
    main_grain_form: str
        Basic grain class code extracted from grain_form (first 2 characters).
        Always returns the 2-character basic code regardless of whether grain_form
        contains a sub-grain or basic code.

    ## From Method Implementations
    density_calculated: Union[float, uncertainties.UFloat]
        Layer density in kilograms per cubic meter (kg/m³). Can include uncertainty.
    poissons_ratio: Union[float, uncertainties.UFloat]
        Layer poissons ratio. Can include uncertainty.
    shear_modulus: Union[float, uncertainties.UFloat]
        Layer shear modulus. Can include uncertainty.
    elastic_modulus: Union[float, uncertainties.UFloat]
        Layer elastic modulus. Can include uncertainty.

    --------

    """
    # ==========================================
    # Field Measurements
    # ==========================================
    depth_top: Optional[UncertainValue] = None  # cm - Layer depth from the top of the snowpack
    thickness: Optional[UncertainValue] = None  # cm - Layer thickness
    density_measured: Optional[UncertainValue] = None  # kg/m³ - Layer density measured directly
    hand_hardness: Optional[str] = None  # Layer hand hardness
    grain_form: Optional[str] = None  # Grain form code: sub-grain class (e.g., 'FCxr', 'PPgp', 'RGmx') if available, otherwise basic class (e.g., 'FC', 'PP', 'RG')
    grain_size_avg: Optional[UncertainValue] = None  # mm - Average grain size
    layer_of_concern: bool = False  # Whether this layer is marked as layer of concern

    # ==========================================
    # Calculated Parameters - From Method Implementations
    # ==========================================
    density_calculated: Optional[UncertainValue] = None  # kg/m³ - Layer density
    poissons_ratio: Optional[UncertainValue] = None  # Layer Poisson's ratio
    shear_modulus: Optional[UncertainValue] = None  # Layer shear modulus
    elastic_modulus: Optional[UncertainValue] = None  # Layer elastic modulus

    # ==========================================
    # Calculated Parameters - From Field Measurements (Properties)
    # ==========================================

    @property
    def depth_bottom(self) -> Optional[UncertainValue]:
        """
        Calculate the bottom depth of the layer.

        Calculated as depth_top + thickness when both are available.
        Returns None if either depth_top or thickness is not defined.

        Returns
        -------
        Optional[UncertainValue]
            Location of the bottom of the layer in centimeters (cm), or None
        """
        if self.depth_top is not None and self.thickness is not None:
            return self.depth_top + self.thickness
        return None

    @property
    def hand_hardness_index(self) -> Optional[UncertainValue]:
        """
        Calculate the hand hardness index from the hand hardness string, with
        standard measurement uncertainty applied.

        Looks up the nominal HHI from ``HARDNESS_MAPPING`` and wraps it with
        ``U_HAND_HARDNESS_INDEX``, consistent with how thickness, grain size,
        density, and slope angle uncertainties are all applied in this module.

        Returns
        -------
        Optional[UncertainValue]
            ``ufloat(hhi, U_HAND_HARDNESS_INDEX)``, or ``None`` if
            ``hand_hardness`` is not set or not in the mapping.
        """
        if self.hand_hardness is None:
            return None
        hhi = HARDNESS_MAPPING.get(self.hand_hardness)
        if hhi is None:
            return None
        return _ufloat(hhi, U_HAND_HARDNESS_INDEX)

    @property
    def main_grain_form(self) -> Optional[str]:
        """
        Extract the basic grain form from the grain_form string.

        Returns the first two characters of grain_form, which extracts the basic
        grain class code:
        - For sub-grain codes (e.g., 'FCxr', 'PPgp', 'RGmx'): returns basic form ('FC', 'PP', 'RG')
        - For basic codes (e.g., 'FC', 'PP', 'RG'): returns same value (already basic)

        This property is useful when you need the basic grain class regardless of
        whether the full grain_form contains a sub-grain or basic code.

        Returns None if grain_form is not defined or has less than 2 characters.

        Returns
        -------
        Optional[str]
            Basic grain class code (first 2 characters of grain_form), or None

        Examples
        --------
        >>> layer.grain_form = "FCxr"
        >>> layer.main_grain_form
        'FC'

        >>> layer.grain_form = "PP"
        >>> layer.main_grain_form
        'PP'
        """
        if self.grain_form is not None and len(self.grain_form) >= 2:
            return self.grain_form[:2]
        return None
