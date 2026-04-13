# Pit data structure for snow mechanical parameter calculations

from dataclasses import dataclass, field
import math
from typing import Any, List, Literal, Optional, Union

from snowpyt_mechparams.models._types import UncertainValue
from snowpyt_mechparams.models.layer import Layer
from snowpyt_mechparams.models.slab import Slab
from snowpyt_mechparams.models.weak_layer import WeakLayer

WeakLayerDef = Literal["layer_of_concern", "CT_failure_layer", "ECTP_failure_layer"]


@dataclass
class Pit:
    """
    Represents a Snow Pit profile with layers and stability test data.

    This class encapsulates a snow pit observation, including extracted
    metadata, layers, and stability test results. It provides methods to
    build slab objects from the profile.

    Attributes
    ----------
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
    1. Parse CAAML file using parse_caaml_file() from snowpilot
    2. Pass the snowpylot SnowPit to parse_pit() from models.pit_parser, or use the
       convenience classmethod Pit.from_snow_pit()

    """
    # Extracted metadata
    pit_id: Optional[str] = None
    slope_angle: Union[float, UncertainValue] = field(default_factory=lambda: float("nan"))

    # Layers and test results
    layers: List[Layer] = field(default_factory=list)
    ECT_results: Optional[List[Any]] = None
    CT_results: Optional[List[Any]] = None
    PST_results: Optional[List[Any]] = None

    @classmethod
    def from_snow_pit(cls, snow_pit: Any) -> "Pit":
        """
        Create a Pit object from a snowpylot SnowPit.

        This is the primary convenience method for creating a Pit object.
        First parse a CAAML file using snowpylot, then pass the SnowPit here.

        Parameters
        ----------
        snow_pit : Any
            SnowPit object from snowpylot (via caaml_parser)

        Returns
        -------
        Pit
            Initialized Pit object with layers and test results

        """
        # Deferred import avoids circular dependency with pit_parser
        from snowpyt_mechparams.models.pit_parser import parse_pit

        return parse_pit(snow_pit)

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

    @staticmethod
    def _nominal_depth(value: Optional[UncertainValue]) -> Optional[float]:
        """
        Convert a depth-like value to a comparable nominal float.

        Returns ``None`` for missing or NaN-valued depths.
        """
        if value is None:
            return None
        depth = float(getattr(value, "nominal_value", value))
        if math.isnan(depth):
            return None
        return depth

    def create_slabs(
        self,
        weak_layer_def: Optional[WeakLayerDef] = None,
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
        weak_layer_def : Optional[WeakLayerDef]
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

        """
        slabs: List[Slab] = []

        if not self.layers:
            return slabs

        if weak_layer_def is None:
            return slabs

        if weak_layer_def == "layer_of_concern":
            weak_layer = self.layer_of_concern
            weak_layer_depth_top = None if weak_layer is None else self._nominal_depth(weak_layer.depth_top)
            if weak_layer is None or weak_layer_depth_top is None:
                return slabs

            slab_layers = [
                layer for layer in self.layers
                if (layer_depth_top := self._nominal_depth(layer.depth_top)) is not None
                and layer_depth_top < weak_layer_depth_top
            ]

            if not slab_layers:
                return slabs

            slab = Slab(
                layers=slab_layers,
                angle=self.slope_angle,
                weak_layer=WeakLayer.from_layer(weak_layer),
                pit_id=self.pit_id,
                slab_id=f"{self.pit_id}_slab_0" if self.pit_id else "slab_0",
                weak_layer_source="layer_of_concern",
                test_result_index=None,
                test_result_properties=None,
                n_test_results_in_pit=None,
            )
            slabs.append(slab)
            return slabs

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

        for test_idx, test_result in enumerate(test_results):
            created_slab = self._create_slab_from_test_result(
                test_result=test_result,
                test_idx=test_idx,
                test_type=test_type,
                weak_layer_def=weak_layer_def,
                n_total_tests=len(test_results),
            )
            if created_slab is not None:
                slabs.append(created_slab)

        return slabs

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

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
            # Two conditions cover different snowpylot/CAAML versions:
            # some versions expose a boolean `propagation` field; others encode
            # propagation in the test score string (e.g., "ECTP21").
            if (hasattr(ect, "propagation") and ect.propagation)
            or (
                hasattr(ect, "test_score")
                and ect.test_score
                and "ECTP" in str(ect.test_score)
            )
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
            if hasattr(ct, "fracture_character")
            and ct.fracture_character in ["Q1", "SC", "SP"]
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
        from snowpyt_mechparams.models.pit_parser import extract_test_properties

        # Extract scalar failure depth from value that may be None, scalar, or array-like
        raw = test_result.depth_top
        if raw is None:
            return None
        if isinstance(raw, (list, tuple)):
            failure_depth = raw[0] if len(raw) > 0 else None
        elif hasattr(raw, "__len__") and hasattr(raw, "shape"):
            failure_depth = raw[0] if len(raw) > 0 else None
        else:
            failure_depth = raw
        failure_depth = self._nominal_depth(failure_depth)
        if failure_depth is None:
            return None

        weak_layer = None
        for layer in self.layers:
            dt = self._nominal_depth(layer.depth_top)
            db = self._nominal_depth(layer.depth_bottom)
            if dt is not None and db is not None and dt <= failure_depth < db:
                weak_layer = layer
                break

        weak_layer_depth_top = None if weak_layer is None else self._nominal_depth(weak_layer.depth_top)
        if weak_layer is None or weak_layer_depth_top is None:
            return None

        slab_layers = [
            layer for layer in self.layers
            if (layer_depth_top := self._nominal_depth(layer.depth_top)) is not None
            and layer_depth_top < weak_layer_depth_top
        ]

        if not slab_layers:
            return None

        test_props = extract_test_properties(test_result, test_type)
        slab_id = f"{self.pit_id}_slab_{test_idx}" if self.pit_id else f"slab_{test_idx}"

        return Slab(
            layers=slab_layers,
            angle=self.slope_angle,
            weak_layer=WeakLayer.from_layer(weak_layer),
            pit_id=self.pit_id,
            slab_id=slab_id,
            weak_layer_source=weak_layer_def,
            test_result_index=test_idx,
            test_result_properties=test_props,
            n_test_results_in_pit=n_total_tests,
        )
