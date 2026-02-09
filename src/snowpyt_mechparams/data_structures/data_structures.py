# Common data structures for snow mechanical parameter calculations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union

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
    Represents a Snow Pit profile with layers and stability test data.
    
    This class encapsulates a snow pit observation, including the raw snowpylot
    data, extracted metadata, layers, and stability test results. It provides
    methods to create layers from the snow profile and build slab objects.
    
    Attributes
    ----------
    snowpylot_profile : Any
        Raw CAAML profile object from snowpylot parser
    pit_id : Optional[str]
        Identifier for the pit (extracted from profile if available)
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
    layer_of_concern : Optional[Layer]
        Layer marked as layer of concern in the profile
    
    Notes
    -----
    Workflow for creating a Pit object:
    1. Parse CAAML file using parse_caaml_file() from snowpilot_utils
    2. Pass the snowpylot profile to Pit.from_snowpylot_profile()
    
    Examples
    --------
    >>> from snowpyt_mechparams.snowpilot_utils import parse_caaml_file
    >>> from snowpyt_mechparams.data_structures import Pit
    >>> 
    >>> # Parse CAAML file to get snowpylot profile
    >>> profile = parse_caaml_file("profile.xml")
    >>> 
    >>> # Create Pit from snowpylot profile
    >>> pit = Pit.from_snowpylot_profile(profile)
    >>> 
    >>> # Create slab from pit
    >>> slab = pit.create_slab(weak_layer_def="layer_of_concern")
    """
    # Raw data
    snowpylot_profile: Any
    
    # Extracted metadata
    pit_id: Optional[str] = None
    slope_angle: float = float('nan')
    
    # Layers and test results (populated automatically in __post_init__)
    layers: List[Layer] = field(default_factory=list)
    ECT_results: Optional[List[Any]] = None
    CT_results: Optional[List[Any]] = None
    PST_results: Optional[List[Any]] = None
    layer_of_concern: Optional[Layer] = None
    
    def __post_init__(self) -> None:
        """
        Initialize the pit by extracting layers and test results from snowpylot profile.
        """
        # Extract slope angle
        self.slope_angle = self._extract_slope_angle()
        
        # Extract pit ID if available
        self.pit_id = self._extract_pit_id()
        
        # Create layers from snow profile
        self.layers = self._create_layers_from_profile()
        
        # Extract stability test results
        self.ECT_results = self._extract_stability_test_results("ECT")
        self.CT_results = self._extract_stability_test_results("CT")
        self.PST_results = self._extract_stability_test_results("PST")
        
        # Extract layer of concern
        self.layer_of_concern = self._extract_layer_of_concern()
    
    @classmethod
    def from_snowpylot_profile(cls, profile: Any) -> "Pit":
        """
        Create a Pit object from a snowpylot profile.
        
        This is the primary way to create a Pit object. First parse a CAAML file
        using snowpylot, then pass the profile to this method.
        
        Parameters
        ----------
        profile : Any
            Parsed CAAML profile object from snowpylot (via caaml_parser)
            
        Returns
        -------
        Pit
            Initialized Pit object with layers and test results
            
        Examples
        --------
        >>> from snowpyt_mechparams.snowpilot_utils import parse_caaml_file
        >>> from snowpyt_mechparams.data_structures import Pit
        >>> 
        >>> # Step 1: Parse CAAML file to get snowpylot profile
        >>> profile = parse_caaml_file("profile.xml")
        >>> 
        >>> # Step 2: Create Pit from snowpylot profile
        >>> pit = Pit.from_snowpylot_profile(profile)
        >>> print(f"Pit has {len(pit.layers)} layers")
        """
        return cls(snowpylot_profile=profile)
    
    def create_slab(
        self,
        weak_layer_def: Optional[str] = None,
        depth_tolerance: float = 2.0,
    ) -> Optional["Slab"]:
        """
        Create a Slab object from the pit's layers.
        
        Parameters
        ----------
        weak_layer_def : Optional[str]
            Weak layer definition - one of:
            - None: Returns all layers in the profile (no weak layer filtering)
            - "layer_of_concern": Uses layer with layer_of_concern=True
            - "CT_failure_layer": Uses CT test failure layer with Q1/SC/SP fracture character
            - "ECTP_failure_layer": Uses ECT test failure layer with propagation
        depth_tolerance : float, optional
            Tolerance in cm for matching test depths to layer depths (default: 2.0 cm)
            
        Returns
        -------
        Optional[Slab]
            Slab object containing layers above the weak layer (or all layers if
            weak_layer_def=None), or None if no valid slab can be created
            
        Examples
        --------
        >>> from snowpyt_mechparams.snowpilot_utils import parse_caaml_file
        >>> profile = parse_caaml_file("profile.xml")
        >>> pit = Pit.from_snowpylot_profile(profile)
        >>> slab = pit.create_slab(weak_layer_def="layer_of_concern")
        >>> if slab:
        ...     print(f"Slab has {len(slab.layers)} layers")
        """
        if not self.layers:
            return None
        
        # If no weak layer definition, return all layers
        if weak_layer_def is None:
            return Slab(
                layers=self.layers,
                angle=self.slope_angle,
                ECT_results=self.ECT_results,
                CT_results=self.CT_results,
                PST_results=self.PST_results,
                layer_of_concern=self.layer_of_concern,
            )
        
        # Find the weak layer depth
        weak_layer_depth = self._find_weak_layer_depth(weak_layer_def, depth_tolerance)
        
        if weak_layer_depth is None:
            return None
        
        # Find the weak layer object from layers
        # The weak layer is the layer that contains the failure depth
        weak_layer = None
        for layer in self.layers:
            if layer.depth_top is not None and layer.depth_bottom is not None:
                if layer.depth_top <= weak_layer_depth < layer.depth_bottom:
                    weak_layer = layer
                    break
        
        # If no weak layer found, return None
        if weak_layer is None or weak_layer.depth_top is None:
            return None
        
        # Filter layers above the weak layer
        # Layers are above the weak layer if their depth_top < weak_layer's depth_top
        slab_layers = [
            layer for layer in self.layers
            if layer.depth_top is not None and layer.depth_top < weak_layer.depth_top
        ]
        
        # Return None if no valid layers above weak layer
        if not slab_layers:
            return None
        
        return Slab(
            layers=slab_layers,
            angle=self.slope_angle,
            weak_layer=weak_layer,
            ECT_results=self.ECT_results,
            CT_results=self.CT_results,
            PST_results=self.PST_results,
            layer_of_concern=self.layer_of_concern,
        )
    
    # ============================================================================
    # Private Helper Methods
    # ============================================================================
    
    def _extract_slope_angle(self) -> float:
        """Extract slope angle from snowpylot profile."""
        try:
            slope_angle_data = self.snowpylot_profile.core_info.location.slope_angle
            if slope_angle_data and len(slope_angle_data) > 0:
                return float(slope_angle_data[0])
            else:
                return float('nan')
        except (AttributeError, IndexError, TypeError, ValueError):
            return float('nan')
    
    def _extract_pit_id(self) -> Optional[str]:
        """Extract pit ID from snowpylot profile if available."""
        try:
            # Try common CAAML fields for observation/profile ID
            if hasattr(self.snowpylot_profile, 'obs_id'):
                return str(self.snowpylot_profile.obs_id)
            if hasattr(self.snowpylot_profile, 'profile_id'):
                return str(self.snowpylot_profile.profile_id)
            return None
        except (AttributeError, TypeError):
            return None
    
    def _create_layers_from_profile(self, include_density: bool = True) -> List[Layer]:
        """
        Convert snowpylot profile to a list of Layer objects.
        
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
        
        # Check if snow_profile and layers exist
        if (
            not hasattr(self.snowpylot_profile, "snow_profile")
            or not hasattr(self.snowpylot_profile.snow_profile, "layers")
        ):
            return layers
        
        if not self.snowpylot_profile.snow_profile.layers:
            return layers
        
        for layer in self.snowpylot_profile.snow_profile.layers:
            # Extract depth_top (array to scalar)
            depth_top = layer.depth_top[0] if layer.depth_top else None
            
            # Extract thickness (array to scalar)
            thickness = layer.thickness[0] if layer.thickness else None
            
            # Extract hand hardness
            hand_hardness = layer.hardness if hasattr(layer, "hardness") else None
            
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
            
            # Extract grain size average
            grain_size_avg = None
            if (
                hasattr(layer, "grain_form_primary")
                and layer.grain_form_primary
                and hasattr(layer.grain_form_primary, "grain_size_avg")
            ):
                grain_size_data = layer.grain_form_primary.grain_size_avg
                if grain_size_data:
                    grain_size_avg = (
                        grain_size_data[0]
                        if isinstance(grain_size_data, (list, tuple))
                        else grain_size_data
                    )
            
            # Optionally match and extract density from density profile
            density_measured = None
            if include_density and hasattr(self.snowpylot_profile.snow_profile, "density_profile"):
                for density_obs in self.snowpylot_profile.snow_profile.density_profile:
                    if (
                        density_obs.depth_top == layer.depth_top
                        and density_obs.thickness == layer.thickness
                    ):
                        density_measured = density_obs.density
                        break
            
            # Create Layer object
            layer_obj = Layer(
                depth_top=depth_top,
                thickness=thickness,
                density_measured=density_measured,
                hand_hardness=hand_hardness,
                grain_form=grain_form,
                grain_size_avg=grain_size_avg,
            )
            
            layers.append(layer_obj)
        
        return layers
    
    def _extract_stability_test_results(self, test_type: str) -> Optional[List[Any]]:
        """
        Extract stability test results from snowpylot profile.
        
        Parameters
        ----------
        test_type : str
            Test type - one of: "ECT", "CT", "PST"
            
        Returns
        -------
        Optional[List[Any]]
            List of test results, or None if not available
        """
        if not hasattr(self.snowpylot_profile, "stability_tests") or not self.snowpylot_profile.stability_tests:
            return None
        
        # Map test types to possible snowpylot attribute names
        test_attr_map = {
            "ECT": ["ECT"],
            "CT": ["CT"],
            "PST": ["PST", "PropSawTest", "PropSaw"],
        }
        
        if test_type not in test_attr_map:
            return None
        
        # Try each possible attribute name
        for attr_name in test_attr_map[test_type]:
            if hasattr(self.snowpylot_profile.stability_tests, attr_name):
                tests = getattr(self.snowpylot_profile.stability_tests, attr_name)
                if tests is not None:
                    # Handle empty lists (return empty list, not None)
                    if isinstance(tests, (list, tuple)):
                        return list(tests) if tests else []
                    else:
                        return [tests]
        return None
    
    def _extract_layer_of_concern(self) -> Optional[Layer]:
        """
        Extract the layer of concern from snowpylot profile.
        
        Returns
        -------
        Optional[Layer]
            Layer object for the layer of concern, or None if not found
        """
        if (
            not hasattr(self.snowpylot_profile, "snow_profile")
            or not hasattr(self.snowpylot_profile.snow_profile, "layers")
            or not self.snowpylot_profile.snow_profile.layers
        ):
            return None
        
        # Find the layer marked as layer_of_concern in CAAML
        for caaml_layer in self.snowpylot_profile.snow_profile.layers:
            if hasattr(caaml_layer, "layer_of_concern") and caaml_layer.layer_of_concern is True:
                # Find the corresponding Layer object by matching depth_top
                depth_top = self._get_value_safe(caaml_layer.depth_top)
                if depth_top is not None:
                    for layer in self.layers:
                        if layer.depth_top is not None and abs(layer.depth_top - depth_top) < 0.01:
                            return layer
        return None
    
    def _find_weak_layer_depth(
        self, 
        weak_layer_def: str,
        depth_tolerance: float = 2.0
    ) -> Optional[float]:
        """
        Find the depth of the weak layer based on the specified definition.
        
        Parameters
        ----------
        weak_layer_def : str
            Weak layer definition - one of:
            - "layer_of_concern": Uses layer with layer_of_concern=True
            - "CT_failure_layer": Uses CT test failure layer with Q1/SC/SP fracture character
            - "ECTP_failure_layer": Uses ECT test failure layer with propagation
        depth_tolerance : float
            Tolerance in cm for matching test depths to layer depths
            
        Returns
        -------
        Optional[float]
            Depth (from top) of the weak layer in cm, or None if no weak layer found
        """
        if not hasattr(self.snowpylot_profile, "snow_profile") or not self.snowpylot_profile.snow_profile:
            return None
        
        if weak_layer_def == "layer_of_concern":
            # Find layer marked as layer_of_concern
            if (
                not hasattr(self.snowpylot_profile.snow_profile, "layers")
                or not self.snowpylot_profile.snow_profile.layers
            ):
                return None
            
            for layer in self.snowpylot_profile.snow_profile.layers:
                if hasattr(layer, "layer_of_concern") and layer.layer_of_concern is True:
                    depth = self._get_value_safe(layer.depth_top)
                    if depth is not None:
                        return depth
            return None
        
        elif weak_layer_def == "CT_failure_layer":
            # Find CT test failure layer with Q1/SC/SP fracture character
            if not hasattr(self.snowpylot_profile, "stability_tests") or not hasattr(
                self.snowpylot_profile.stability_tests, "CT"
            ):
                return None
            
            ct_tests = self.snowpylot_profile.stability_tests.CT
            if not ct_tests:
                return None
            
            for ct in ct_tests:
                if (
                    hasattr(ct, "fracture_character")
                    and ct.fracture_character in ["Q1", "SC", "SP"]
                ):
                    depth = self._get_value_safe(ct.depth_top)
                    if depth is not None:
                        return depth
            return None
        
        elif weak_layer_def == "ECTP_failure_layer":
            # Find ECT test failure layer with propagation
            if not hasattr(self.snowpylot_profile, "stability_tests") or not hasattr(
                self.snowpylot_profile.stability_tests, "ECT"
            ):
                return None
            
            ect_tests = self.snowpylot_profile.stability_tests.ECT
            if not ect_tests:
                return None
            
            for ect in ect_tests:
                # Check for propagation in both attribute and test_score
                has_propagation = (
                    hasattr(ect, "propagation") and ect.propagation is True
                ) or (
                    hasattr(ect, "test_score")
                    and ect.test_score
                    and "ECTP" in str(ect.test_score)
                )
                if has_propagation:
                    depth = self._get_value_safe(ect.depth_top)
                    if depth is not None:
                        return depth
            return None
        
        else:
            raise ValueError(
                f"Invalid weak_layer_def '{weak_layer_def}'. "
                f"Valid options: 'layer_of_concern', 'CT_failure_layer', 'ECTP_failure_layer'"
            )
    
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
