# Common data structures for snow mechanical parameter calculations

from dataclasses import dataclass
from typing import List, NamedTuple, Union

import uncertainties

# Type alias for values that can be floats or uncertain numbers
UncertainValue = Union[float, uncertainties.UFloat]


class Layer(NamedTuple):
    """
    Represents a snow layer with thickness and density.

    Values can be regular floats or uncertain numbers (ufloat) from the
    uncertainties package. When using uncertain numbers, uncertainties will
    automatically propagate through calculations.

    Attributes
    ----------
    thickness : Union[float, uncertainties.UFloat]
        Layer thickness in millimeters (mm). Can include uncertainty.
    density : Union[float, uncertainties.UFloat]
        Layer density in kilograms per cubic meter (kg/m³). Can include uncertainty.

    Examples
    --------
    >>> # Layer with exact values
    >>> layer1 = Layer(thickness=50.0, density=250.0)
    >>>
    >>> # Layer with uncertain values
    >>> from uncertainties import ufloat
    >>> layer2 = Layer(thickness=ufloat(50, 2), density=ufloat(250, 10))
    """
    thickness: UncertainValue  # mm
    density: UncertainValue    # kg/m³


@dataclass
class Slab:
    """
    Represents a snow slab as an ordered collection of layers.

    The slab is ordered from top to bottom, where the first layer
    is at the surface and subsequent layers are deeper in the snowpack.

    Attributes
    ----------
    layers : List[Layer]
        Ordered list of snow layers from top (surface) to bottom
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
    def total_thickness(self) -> UncertainValue:
        """
        Calculate the total thickness of the slab.

        If any layers have uncertain thickness values, the result will
        automatically include propagated uncertainties.

        Returns
        -------
        Union[float, uncertainties.UFloat]
            Total thickness in millimeters (mm), with uncertainty if applicable
        """
        return sum(layer.thickness for layer in self.layers)
