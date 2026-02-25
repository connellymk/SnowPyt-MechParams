# Slab data structure for snow mechanical parameter calculations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

import uncertainties

from snowpyt_mechparams.data_structures.layer import Layer, UncertainValue

if TYPE_CHECKING:
    from snowpyt_mechparams.data_structures.pit import Pit


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

    # Parent Reference
    pit: Optional["Pit"]
        Reference to the parent Pit object (access test results and layer_of_concern through this)

    # Metadata
    pit_id : Optional[str]
        Identifier of the source pit
    slab_id : Optional[str]
        Unique identifier for this slab (e.g., "pit_001_slab_0")
    weak_layer_source : Optional[str]
        Method used to identify weak layer (e.g., "ECTP_failure_layer", "CT_failure_layer", "layer_of_concern")
    test_result_index : Optional[int]
        Index of the specific test result used to create this slab (0-indexed)
    test_result_properties : Optional[dict]
        Properties of the specific test result used (e.g., {"score": "ECTP12", "propagation": True})
    n_test_results_in_pit : Optional[int]
        Total number of test results of this type available in the source pit

    # Calculated Parameters - From Method Implementations
    A11 : Union[float, uncertainties.UFloat]
        Extensional stiffness in N/mm. Can include uncertainty.
    A55 : Union[float, uncertainties.UFloat]
        Shear stiffness (with shear correction factor kappa) in N/mm. Can include uncertainty.
    B11 : Union[float, uncertainties.UFloat]
        Bending-extension coupling stiffness in N. Can include uncertainty.
    D11 : Union[float, uncertainties.UFloat]
        Bending stiffness in N*mm. Can include uncertainty.
    """
    # Slab Structure
    layers: List[Layer]  # Ordered list of snow layers from top (surface) to bottom
    angle: UncertainValue  # Slope angle of the slab in degrees
    weak_layer: Optional[Layer] = None  # Weak layer of the slab

    # Parent Reference - access test results through pit.ECT_results, pit.CT_results, etc.
    pit: Optional["Pit"] = None  # Reference to parent Pit object

    # Metadata - tracks which test result was used to create this slab
    pit_id: Optional[str] = None  # Source pit identifier
    slab_id: Optional[str] = None  # Unique slab identifier
    weak_layer_source: Optional[str] = None  # Method used to identify weak layer
    test_result_index: Optional[int] = None  # Index of specific test result used (0-indexed)
    test_result_properties: Optional[dict] = None  # Properties of the specific test result
    n_test_results_in_pit: Optional[int] = None  # Total test results available in pit

    # Calculated Parameters - From Method Implementations
    A11: Optional[UncertainValue] = None  # N/mm - Extensional stiffness
    A55: Optional[UncertainValue] = None  # N/mm - Shear stiffness (with shear correction factor kappa)
    B11: Optional[UncertainValue] = None  # N - Bending-extension coupling stiffness
    D11: Optional[UncertainValue] = None  # N*mm - Bending stiffness

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
        Returns None if no layers have thickness values.

        Returns
        -------
        Optional[UncertainValue]
            Total thickness in centimeters (cm), with uncertainty if applicable, or None
        """
        thicknesses = [layer.thickness for layer in self.layers if layer.thickness is not None]
        return sum(thicknesses) if thicknesses else None
