# Common data structures for snow mechanical parameter calculations

from dataclasses import dataclass
from typing import List, Optional, Union

import uncertainties

from snowpyt_mechparams.constants import HARDNESS_MAPPING

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
        Calculate the hand hardness index from the hand hardness string.
        
        Uses the HARDNESS_MAPPING to convert hand hardness strings to numeric indices.
        Returns None if hand_hardness is not defined or not in the mapping.
        
        Returns
        -------
        Optional[UncertainValue]
            Hand hardness index of the layer, or None
        """
        if self.hand_hardness is not None and self.hand_hardness in HARDNESS_MAPPING:
            return HARDNESS_MAPPING[self.hand_hardness]
        return None
    
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

@dataclass
class Pit:
    """
    Represents a Snow Pilot Snowpit object.
    """
    core_info: CoreInfo # Core information about the snowpit
    snow_profile: SnowProfile # Snow profile of the snowpit
    stability_tests: StabilityTests # Stability tests of the snowpit

@dataclass
class Slab:
    """
    Represents a snow slab as an ordered collection of layers.

    The slab is ordered from top to bottom, where the first layer
    is at the surface and subsequent layers are deeper in the snowpack.

    Attributes
    ----------

    # Field Measurements
    angle: float
        Angle of the slab in degrees.

    # Layer Structure
    layers : List[Layer]
        Ordered list of snow layers from top (surface) to bottom

    # Weak Layer
    weak_layer: Optional[Layer]
        Weak layer of the slab.

    # Calculated Parameters - From Method Implementations
    A11 : Union[float, uncertainties.UFloat]
        Extensional stiffness in N/mm. Can include uncertainty.
    A55 : Union[float, uncertainties.UFloat]
        Shear stiffness (with shear correction factor κ) in N/mm. Can include uncertainty.
    B11 : Union[float, uncertainties.UFloat]
        Bending-extension coupling stiffness in N. Can include uncertainty.
    D11 : Union[float, uncertainties.UFloat]
        Bending stiffness in N·mm. Can include uncertainty.
    """
    # Slab Structure
    layers: List[Layer] # Ordered list of snow layers from top (surface) to bottom
    angle: float # Slope angle of the slab in degrees
    weak_layer: Optional[Layer] = None  # Weak layer of the slab

    # Stability Test Results
    ECT_results: Optional[List[Any]] = None  # ECT test results
    CT_results: Optional[List[Any]] = None  # CT test results
    PST_results: Optional[List[Any]] = None  # PST test results
    layer_of_concern: Optional[Layer] = None  # Layer of concern

    # Calculated Parameters - From Method Implementations
    A11: Optional[UncertainValue] = None  # N/mm - Extensional stiffness
    A55: Optional[UncertainValue] = None  # N/mm - Shear stiffness (with shear correction factor κ)
    B11: Optional[UncertainValue] = None  # N - Bending-extension coupling stiffness
    D11: Optional[UncertainValue] = None  # N·mm - Bending stiffness

    def __post_init__(self) -> None:
        """Validate that the slab contains at least one layer."""
        if not self.layers:
            raise ValueError("Slab must contain at least one layer")

        # Validate that all items are Layer objects
        for i, layer in enumerate(self.layers):
            if not isinstance(layer, Layer):
                raise TypeError(f"Layer {i} must be a Layer object, got {type(layer)}")

    @property
    def total_thickness(self) -> Optional[UncertainValue]:
        """
        Calculate the total thickness of the slab.

        If any layers have uncertain thickness values, the result will
        automatically include propagated uncertainties.
        Returns None if any layer has a None thickness value.

        Returns
        -------
        Optional[UncertainValue]
            Total thickness in centimeters (cm), with uncertainty if applicable, or None
        """
        thicknesses = [layer.thickness for layer in self.layers if layer.thickness is not None]
        if not thicknesses:
            return None
        return sum(thicknesses)
