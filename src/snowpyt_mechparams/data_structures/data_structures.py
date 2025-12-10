# Common data structures for snow mechanical parameter calculations

from dataclasses import dataclass
from typing import List, Optional, Union

import uncertainties

# Type alias for values that can be floats or uncertain numbers
UncertainValue = Union[float, uncertainties.UFloat]

# Map hand hardness string to numeric hand hardness index (hhi)
HARDNESS_MAPPING = {
    'F-': 0.67, 'F': 1.0, 'F+': 1.33,
    '4F-': 1.67, '4F': 2.0, '4F+': 2.33,
    '1F-': 2.67, '1F': 3.0, '1F+': 3.33,
    'P-': 3.67, 'P': 4.0, 'P+': 4.33,
    'K-': 4.67, 'K': 5.0, 'K+': 5.33
}


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
    hand_hardness: str
        Layer hand hardness 
    grain_form: str
    grain_size_avg: Union[float, uncertainties.UFloat]


    # Calculated Parameters

    ## From Field Measurements
    depth_bottom: Union[float, uncertainties.UFloat]
        location of the bottom of the layer in centimeters (cm). Can include uncertainty.
    hand_hardness_index: Union[float, uncertainties.UFloat]
        Hand hardness index of the layer.
    main_grain_from: str
        Main grain shape of the layer.

    ## From Method Implementations
    density: Union[float, uncertainties.UFloat]
        Layer density in kilograms per cubic meter (kg/m³). Can include uncertainty.
        NOTE: Can also be measured directly
    poissons_ratio: Union[float, uncertainties.UFloat]
        Layer poissons ratio. Can include uncertainty.
    shear_modulus: Union[float, uncertainties.UFloat]
        Layer shear modulus. Can include uncertainty.
    elastic_modulus: Union[float, uncertainties.UFloat]
        Layer elastic modulus. Can include uncertainty.


    Examples
    --------

    """
    # Field Measurements
    depth_top: Optional[UncertainValue] = None  # cm - Layer depth from the top of the snowpack
    thickness: Optional[UncertainValue] = None  # cm - Layer thickness
    hand_hardness: Optional[str] = None  # Layer hand hardness
    grain_form: Optional[str] = None  # Grain form
    grain_size_avg: Optional[UncertainValue] = None  # Average grain size
    
    # Calculated Parameters - From Method Implementations
    density: Optional[UncertainValue] = None  # kg/m³ - Layer density (can also be measured directly)
    poissons_ratio: Optional[UncertainValue] = None  # Layer Poisson's ratio
    shear_modulus: Optional[UncertainValue] = None  # Layer shear modulus
    elastic_modulus: Optional[UncertainValue] = None  # Layer elastic modulus
    
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
        Extract the main grain form from the grain_form string.
        
        Returns the first two characters of grain_form.
        Returns None if grain_form is not defined or has less than 2 characters.
        
        Returns
        -------
        Optional[str]
            Main grain shape of the layer (first 2 characters of grain_form), or None
        """
        if self.grain_form is not None and len(self.grain_form) >= 2:
            return self.grain_form[:2]
        return None


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

    # Calculated Parameters
    """
    layers: List[Layer]
    angle: float

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
