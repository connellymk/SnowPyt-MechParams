# Slab data structure for snow mechanical parameter calculations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from snowpyt_mechparams.models._types import UncertainValue
from snowpyt_mechparams.models.layer import Layer
from snowpyt_mechparams.models.weak_layer import WeakLayer

if TYPE_CHECKING:
    from snowpyt_mechparams.stability_criteria.weac.weac_result import WeacSkierResult
    from snowpyt_mechparams.stability_criteria.roch.roch_result import RochResult


@dataclass
class Slab:
    """
    Represents a snow slab as an ordered collection of layers.

    The slab is ordered from top to bottom, where the first layer
    is at the surface and subsequent layers are deeper in the snowpack.

    Attributes
    ----------

    # Field Measurements
    angle: UncertainValue
        Slope angle of the slab in degrees (required). May be a plain float or
        a ``ufloat`` with measurement uncertainty (e.g., ``ufloat(35.0, 2.0)``
        for a 35° slope with ±2° uncertainty).

    # Layer Structure
    layers : List[Layer]
        Ordered list of snow layers from top (surface) to bottom

    # Weak Layer
    weak_layer: Optional[Layer]
        Weak layer of the slab (measured Layer object from the snow pit).
    weac_layer: Optional[WeakLayer]
        Computed fracture/strength parameters for the WEAC skier criterion.
        Populated by the execution engine when targeting stability parameters.

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
    A11 : Optional[UncertainValue]
        Extensional stiffness in N/mm. Can include uncertainty.
    A55 : Optional[UncertainValue]
        Shear stiffness (with shear correction factor kappa) in N/mm. Can include uncertainty.
    B11 : Optional[UncertainValue]
        Bending-extension coupling stiffness in N. Can include uncertainty.
    D11 : Optional[UncertainValue]
        Bending stiffness in N*mm. Can include uncertainty.
    """
    # Slab Structure
    layers: List[Layer]  # Ordered list of snow layers from top (surface) to bottom
    angle: UncertainValue  # Slope angle of the slab in degrees
    weak_layer: Optional[Layer] = None  # Weak layer of the slab

    # Metadata - tracks which test result was used to create this slab
    pit_id: Optional[str] = None  # Source pit identifier
    slab_id: Optional[str] = None  # Unique slab identifier
    weak_layer_source: Optional[str] = None  # Method used to identify weak layer
    test_result_index: Optional[int] = None  # Index of specific test result used (0-indexed)
    test_result_properties: Optional[dict] = None  # Properties of the specific test result
    n_test_results_in_pit: Optional[int] = None  # Total test results available in pit

    # Weak Layer Fracture Parameters (populated by execution engine)
    weac_layer: Optional[WeakLayer] = None  # Fracture/strength params for WEAC skier criterion

    # Calculated Parameters - From Method Implementations
    A11: Optional[UncertainValue] = None  # N/mm - Extensional stiffness
    A55: Optional[UncertainValue] = None  # N/mm - Shear stiffness (with shear correction factor kappa)
    B11: Optional[UncertainValue] = None  # N - Bending-extension coupling stiffness
    D11: Optional[UncertainValue] = None  # N*mm - Bending stiffness

    # Stability Criterion Results (populated by execution engine)
    weac_result: Optional["WeacSkierResult"] = None        # Full result from WEAC skier criterion
    roch_result: Optional["RochResult"] = None             # Roch natural criterion (S_r = τ_c / τ)
    roch_skier_result: Optional["RochResult"] = None       # Roch skier criterion (S_sk = (τ_c − τ) / τ_sk)

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
