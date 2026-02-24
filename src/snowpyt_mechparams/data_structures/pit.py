# Pit data structure for snow mechanical parameter calculations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from snowpyt_mechparams.constants import (
    U_SLOPE_ANGLE,
    U_GRAIN_SIZE,
    U_THICKNESS_FRACTION,
    U_DENSITY_FRACTION,
)
from uncertainties import ufloat as _ufloat

from snowpyt_mechparams.data_structures.layer import Layer
from snowpyt_mechparams.data_structures.slab import Slab


@dataclass
class Pit:
    """
    Represents a Snow Pit profile with layers and stability test data.

    This class encapsulates a snow pit observation, including the raw snowpylot
    SnowPit object, extracted metadata, layers, and stability test results. It
    provides methods to create layers from the snow profile and build slab objects.

    Attributes
    ----------
    snow_pit : Any
        SnowPit object from snowpylot (parsed from CAAML)
    pit_id : Optional[str]
        Identifier for the pit (extracted from core_info if available)
    slope_angle : float
        Slope angle in degrees (NaN if not available)
    layers : List[Layer]
        List of snow layers in the profile (top to bottom)
    ECT_results : Optional[List[Any]]
        Extended Column Test results from stability tests
    CT_results : Optional[List[Any]]
        Compression Test results from stability tests
    PST_results : Optional[List[Any]]
        Propagation Saw Test results from stability tests

    Notes
    -----
    Workflow for creating a Pit object:
    1. Parse CAAML file using parse_caaml_file() from snowpilot_utils
    2. Pass the snowpylot SnowPit to Pit.from_snow_pit()

    Examples
    --------
    >>> from snowpyt_mechparams.snowpilot import parse_caaml_file
    >>> from snowpyt_mechparams.data_structures import Pit
    >>>
    >>> # Parse CAAML file to get snowpylot SnowPit
    >>> snow_pit = parse_caaml_file("profile.xml")
    >>>
    >>> # Create Pit from snowpylot SnowPit
    >>> pit = Pit.from_snow_pit(snow_pit)
    >>>
    >>> # Create slabs from pit (one per matching test result)
    >>> slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    >>> print(f"Created {len(slabs)} slabs")
    """
    # Raw data
    snow_pit: Any

    # Extracted metadata
    pit_id: Optional[str] = None
    slope_angle: float = float('nan')

    # Layers and test results (populated automatically in __post_init__)
    layers: List[Layer] = field(default_factory=list)
    ECT_results: Optional[List[Any]] = None
    CT_results: Optional[List[Any]] = None
    PST_results: Optional[List[Any]] = None

    def __post_init__(self) -> None:
        """
        Initialize the pit by extracting layers and test results from snowpylot SnowPit.
        """
        # Extract slope angle and apply standard measurement uncertainty
        try:
            self.slope_angle = _ufloat(self.snow_pit.core_info.location.slope_angle[0], U_SLOPE_ANGLE)
        except (AttributeError, IndexError, TypeError, ValueError):
            self.slope_angle = float('nan')

        # Extract pit ID
        try:
            self.pit_id = self.snow_pit.core_info.pit_id
        except (AttributeError, TypeError):
            self.pit_id = None

        # Create layers from snow profile
        self.layers = self._create_layers_from_profile()

        # Extract stability test results
        if hasattr(self.snow_pit, "stability_tests") and self.snow_pit.stability_tests:
            self.ECT_results = self.snow_pit.stability_tests.ECT if self.snow_pit.stability_tests.ECT else []
            self.CT_results = self.snow_pit.stability_tests.CT if self.snow_pit.stability_tests.CT else []
            self.PST_results = self.snow_pit.stability_tests.PST if self.snow_pit.stability_tests.PST else []

    @classmethod
    def from_snow_pit(cls, snow_pit: Any) -> "Pit":
        """
        Create a Pit object from a snowpylot SnowPit.

        This is the primary way to create a Pit object. First parse a CAAML file
        using snowpylot, then pass the SnowPit to this method.

        Parameters
        ----------
        snow_pit : Any
            SnowPit object from snowpylot (via caaml_parser)

        Returns
        -------
        Pit
            Initialized Pit object with layers and test results

        Examples
        --------
        >>> from snowpyt_mechparams.snowpilot_utils import parse_caaml_file
        >>> from snowpyt_mechparams.data_structures import Pit
        >>>
        >>> # Step 1: Parse CAAML file to get snowpylot SnowPit
        >>> snow_pit = parse_caaml_file("profile.xml")
        >>>
        >>> # Step 2: Create Pit from snowpylot SnowPit
        >>> pit = Pit.from_snow_pit(snow_pit)
        >>> print(f"Pit has {len(pit.layers)} layers")
        """
        return cls(snow_pit=snow_pit)

    @property
    def layer_of_concern(self) -> Optional[Layer]:
        """
        Get the layer marked as layer of concern.

        Returns
        -------
        Optional[Layer]
            First layer with layer_of_concern=True, or None if no layer is marked
        """
        return next((layer for layer in self.layers if layer.layer_of_concern), None)

    def create_slabs(
        self,
        weak_layer_def: Optional[str] = None,
    ) -> List[Slab]:
        """
        Create multiple Slab objects from the pit's layers, one per matching test result.

        This method creates one slab for each test result that matches the weak_layer_def
        criteria. For example, if a pit has 3 ECT tests with propagation, this will create
        3 slabs (one for each ECTP result). Each slab includes metadata tracking which
        test result was used.

        The weak layer is identified by finding which layer contains the test failure depth:
        - The test result provides depth_top (depth of failure from surface)
        - The weak_layer is the layer where: layer.depth_top <= failure_depth < layer.depth_bottom
        - The slab layers are all layers above (NOT including) the weak layer

        Parameters
        ----------
        weak_layer_def : Optional[str]
            Weak layer definition - one of:
            - None: Returns empty list (no slab created without weak layer definition)
            - "layer_of_concern": Returns single slab using layer with layer_of_concern=True
            - "CT_failure_layer": Creates one slab per CT test with Q1/SC/SP fracture character
            - "ECTP_failure_layer": Creates one slab per ECT test with propagation

        Returns
        -------
        List[Slab]
            List of Slab objects, each containing layers above a weak layer identified by
            a test result. Returns empty list if no valid slabs can be created.
            Each slab includes metadata about which test result was used.

        Notes
        -----
        - For weak_layer_def=None, returns empty list (no slab without weak layer)
        - For weak_layer_def="layer_of_concern", returns single slab (or empty list if no layer_of_concern)
        - For test-based definitions (CT, ECTP), returns one slab per matching test result
        - Each slab has unique slab_id in format "{pit_id}_slab_{index}"
        - Metadata fields track test result details for analysis
        - Non-independent slabs from same pit share layer data (account for this in statistics)

        Examples
        --------
        >>> from snowpyt_mechparams.snowpilot_utils import parse_caaml_file
        >>> from snowpyt_mechparams.data_structures import Pit
        >>>
        >>> # Parse CAAML file to get snowpylot SnowPit
        >>> snow_pit = parse_caaml_file("profile.xml")
        >>> pit = Pit.from_snow_pit(snow_pit)
        >>>
        >>> # Create slabs for all ECTP results
        >>> slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
        >>> print(f"Created {len(slabs)} slabs from {pit.pit_id}")
        >>>
        >>> # Access metadata for each slab
        >>> for slab in slabs:
        ...     print(f"Slab {slab.slab_id}: weak layer at {slab.weak_layer.depth_top}cm")
        ...     print(f"  Test index: {slab.test_result_index}")
        ...     print(f"  Test properties: {slab.test_result_properties}")
        """
        slabs = []

        if not self.layers:
            return slabs

        # Handle None - return empty list (no slab without weak layer definition)
        if weak_layer_def is None:
            return slabs

        # Handle layer_of_concern - return single slab based on layer_of_concern
        if weak_layer_def == "layer_of_concern":
            if self.layer_of_concern is None or self.layer_of_concern.depth_top is None:
                return slabs

            # Filter layers above the layer of concern
            slab_layers = [
                layer for layer in self.layers
                if layer.depth_top is not None and layer.depth_top < self.layer_of_concern.depth_top
            ]

            if not slab_layers:
                return slabs

            slab = Slab(
                layers=slab_layers,
                angle=self.slope_angle,
                weak_layer=self.layer_of_concern,
                pit=self,
                pit_id=self.pit_id,
                slab_id=f"{self.pit_id}_slab_0" if self.pit_id else "slab_0",
                weak_layer_source="layer_of_concern",
                test_result_index=None,
                test_result_properties=None,
                n_test_results_in_pit=None,
            )
            slabs.append(slab)
            return slabs

        # Handle test-based weak layer definitions - create one slab per matching test
        if weak_layer_def == "ECTP_failure_layer":
            test_results = self._get_matching_ect_results()
            test_type = "ECT"
        elif weak_layer_def == "CT_failure_layer":
            test_results = self._get_matching_ct_results()
            test_type = "CT"
        else:
            raise ValueError(
                f"Invalid weak_layer_def '{weak_layer_def}'. "
                f"Valid options: None, 'layer_of_concern', 'CT_failure_layer', 'ECTP_failure_layer'"
            )

        if not test_results:
            return slabs

        # Create one slab per matching test result
        for test_idx, test_result in enumerate(test_results):
            slab = self._create_slab_from_test_result(
                test_result=test_result,
                test_idx=test_idx,
                test_type=test_type,
                weak_layer_def=weak_layer_def,
                n_total_tests=len(test_results),
            )
            if slab:
                slabs.append(slab)

        return slabs

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

    def _create_layers_from_profile(self, include_density: bool = True) -> List[Layer]:
        """
        Convert snowpylot SnowPit to a list of Layer objects.

        Parameters
        ----------
        include_density : bool
            If True, attempts to match and include direct density measurements

        Returns
        -------
        List[Layer]
            List of Layer objects representing the snow layers
        """
        layers: List[Layer] = []

        try:
            if not self.snow_pit.snow_profile.layers:
                return layers
        except (AttributeError, TypeError):
            return layers

        for layer in self.snow_pit.snow_profile.layers:
            # Extract depth_top (array to scalar)
            depth_top = layer.depth_top[0] if layer.depth_top else None

            # Extract thickness (array to scalar) and apply measurement uncertainty
            thickness = None
            if layer.thickness:
                t = layer.thickness[0]
                thickness = _ufloat(t, abs(t) * U_THICKNESS_FRACTION)

            # Extract hand hardness
            hand_hardness = layer.hardness if hasattr(layer, "hardness") else None

            # Extract layer_of_concern flag
            is_layer_of_concern = getattr(layer, "layer_of_concern", False)

            # Extract grain form from grain_form_primary
            grain_form = None
            if hasattr(layer, "grain_form_primary") and layer.grain_form_primary:
                grain_form_sub = getattr(
                    layer.grain_form_primary, "sub_grain_class_code", None
                )
                grain_form_basic = getattr(
                    layer.grain_form_primary, "basic_grain_class_code", None
                )
                # Prefer sub-grain (more specific), fall back to basic
                grain_form = grain_form_sub if grain_form_sub else grain_form_basic

            # Extract grain size average and apply standard measurement uncertainty
            grain_size_avg = None
            if (
                hasattr(layer, "grain_form_primary")
                and layer.grain_form_primary
                and hasattr(layer.grain_form_primary, "grain_size_avg")
            ):
                grain_size_data = layer.grain_form_primary.grain_size_avg
                if grain_size_data:
                    gs = (
                        grain_size_data[0]
                        if isinstance(grain_size_data, (list, tuple))
                        else grain_size_data
                    )
                    grain_size_avg = _ufloat(gs, U_GRAIN_SIZE)

            # Optionally match and extract density from density profile and apply
            # standard measurement uncertainty
            density_measured = None
            if include_density:
                try:
                    for density_obs in self.snow_pit.snow_profile.density_profile:
                        if (density_obs.depth_top == layer.depth_top and
                            density_obs.thickness == layer.thickness):
                            # density_obs.density returns [value, 'unit'] - extract just the value
                            if isinstance(density_obs.density, list) and len(density_obs.density) > 0:
                                rho = float(density_obs.density[0])
                            else:
                                rho = float(density_obs.density)
                            density_measured = _ufloat(rho, abs(rho) * U_DENSITY_FRACTION)
                            break
                except (AttributeError, TypeError):
                    pass

            # Create Layer object
            layer_obj = Layer(
                depth_top=depth_top,
                thickness=thickness,
                density_measured=density_measured,
                hand_hardness=hand_hardness,
                grain_form=grain_form,
                grain_size_avg=grain_size_avg,
                layer_of_concern=is_layer_of_concern,
            )

            layers.append(layer_obj)

        return layers

    @staticmethod
    def _get_value_safe(obj: Any) -> Optional[float]:
        """
        Safely extract value from object that might be None, scalar, or array-like.

        Parameters
        ----------
        obj : Any
            Value to extract (could be None, scalar, list, tuple, or array)

        Returns
        -------
        Optional[float]
            Scalar value or None
        """
        if obj is None:
            return None
        if isinstance(obj, (list, tuple)):
            return obj[0] if len(obj) > 0 else None
        # Handle numpy arrays if present
        if hasattr(obj, "__len__") and hasattr(obj, "shape"):
            return obj[0] if len(obj) > 0 else None
        return obj

    def _get_matching_ect_results(self) -> List[Any]:
        """
        Get all ECT test results that have propagation.

        Returns
        -------
        List[Any]
            List of ECT test results with propagation (empty list if none found)
        """
        if not self.ECT_results:
            return []

        return [
            ect for ect in self.ECT_results
            if (hasattr(ect, "propagation") and ect.propagation) or
               (hasattr(ect, "test_score") and ect.test_score and "ECTP" in str(ect.test_score))
        ]

    def _get_matching_ct_results(self) -> List[Any]:
        """
        Get all CT test results with Q1/SC/SP fracture character.

        Returns
        -------
        List[Any]
            List of CT test results with valid fracture character (empty list if none found)
        """
        if not self.CT_results:
            return []

        return [
            ct for ct in self.CT_results
            if hasattr(ct, "fracture_character") and ct.fracture_character in ["Q1", "SC", "SP"]
        ]

    def _create_slab_from_test_result(
        self,
        test_result: Any,
        test_idx: int,
        test_type: str,
        weak_layer_def: str,
        n_total_tests: int,
    ) -> Optional[Slab]:
        """
        Create a slab from a specific test result with metadata.

        The weak layer is found by identifying which layer contains the test failure depth.
        The slab layers are all layers above (not including) the weak layer.

        Parameters
        ----------
        test_result : Any
            The specific test result object with depth_top attribute
        test_idx : int
            Index of this test in the list of matching tests (0-indexed)
        test_type : str
            Type of test ("ECT" or "CT")
        weak_layer_def : str
            Weak layer definition used
        n_total_tests : int
            Total number of matching tests in the pit

        Returns
        -------
        Optional[Slab]
            Slab object with metadata, or None if slab cannot be created
        """
        # Get failure depth from test result
        failure_depth = self._get_value_safe(test_result.depth_top)
        if failure_depth is None:
            return None

        # Find the layer that contains the failure depth
        # This is the weak layer where the failure occurred
        weak_layer = None
        for layer in self.layers:
            if layer.depth_top is not None and layer.depth_bottom is not None:
                if layer.depth_top <= failure_depth < layer.depth_bottom:
                    weak_layer = layer
                    break

        if weak_layer is None or weak_layer.depth_top is None:
            return None

        # Get all layers above the weak layer (NOT including the weak layer)
        slab_layers = [
            layer for layer in self.layers
            if layer.depth_top is not None and layer.depth_top < weak_layer.depth_top
        ]

        if not slab_layers:
            return None

        # Extract test result properties for metadata
        test_props = self._extract_test_properties(test_result, test_type)

        # Create slab ID
        slab_id = f"{self.pit_id}_slab_{test_idx}" if self.pit_id else f"slab_{test_idx}"

        # Create slab with metadata
        return Slab(
            layers=slab_layers,
            angle=self.slope_angle,
            weak_layer=weak_layer,
            pit=self,
            pit_id=self.pit_id,
            slab_id=slab_id,
            weak_layer_source=weak_layer_def,
            test_result_index=test_idx,
            test_result_properties=test_props,
            n_test_results_in_pit=n_total_tests,
        )

    def _extract_test_properties(self, test_result: Any, test_type: str) -> dict:
        """
        Extract properties from a test result for metadata.

        Parameters
        ----------
        test_result : Any
            Test result object
        test_type : str
            Type of test ("ECT" or "CT")

        Returns
        -------
        dict
            Dictionary of test properties
        """
        props = {}

        if test_type == "ECT":
            # Extract ECT properties
            if hasattr(test_result, "test_score"):
                props["score"] = str(test_result.test_score) if test_result.test_score else None
            if hasattr(test_result, "propagation"):
                props["propagation"] = test_result.propagation
            if hasattr(test_result, "depth_top"):
                props["depth_top"] = self._get_value_safe(test_result.depth_top)

        elif test_type == "CT":
            # Extract CT properties
            if hasattr(test_result, "test_score"):
                props["score"] = str(test_result.test_score) if test_result.test_score else None
            if hasattr(test_result, "fracture_character"):
                props["fracture_character"] = test_result.fracture_character
            if hasattr(test_result, "depth_top"):
                props["depth_top"] = self._get_value_safe(test_result.depth_top)

        return props
