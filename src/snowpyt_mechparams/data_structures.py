# Common data structures for snow mechanical parameter calculations

from dataclasses import dataclass
from typing import List, NamedTuple


class Layer(NamedTuple):
    """
    Represents a snow layer with thickness and density.

    Attributes
    ----------
    thickness : float
        Layer thickness in millimeters (mm)
    density : float
        Layer density in kilograms per cubic meter (kg/m³)
    """
    thickness: float  # mm
    density: float    # kg/m³


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
    angle: float    # angle of the slope in degrees TODO: Do we need this?

    def __post_init__(self) -> None:
        """Validate that the slab contains at least one layer."""
        if not self.layers:
            raise ValueError("Slab must contain at least one layer")

        # Validate that all items are Layer objects
        for i, layer in enumerate(self.layers):
            if not isinstance(layer, Layer):
                raise TypeError(f"Layer {i} must be a Layer object, got {type(layer)}")

    @property
    def total_thickness(self) -> float:
        """
        Calculate the total thickness of the slab.

        Returns
        -------
        float
            Total thickness in millimeters (mm)
        """
        return sum(layer.thickness for layer in self.layers)

    def __repr__(self) -> str:
        """String representation of the slab."""
        return f"Slab(layers={len(self.layers)}, total_thickness={self.total_thickness:.1f}mm)"
