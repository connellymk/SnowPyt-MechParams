# Parser for converting snowpylot SnowPit objects into Pit data structures

from typing import TYPE_CHECKING, Any, List, Optional, cast

if TYPE_CHECKING:
    from snowpyt_mechparams.models.pit import Pit

from uncertainties import ufloat as _ufloat

from snowpyt_mechparams.constants import (
    U_DENSITY_FRACTION,
    U_GRAIN_SIZE,
    U_SLOPE_ANGLE,
    U_THICKNESS_FRACTION,
)
from snowpyt_mechparams.models._types import UncertainValue
from snowpyt_mechparams.models.layer import Layer


def parse_pit(snow_pit: Any) -> "Pit":
    """
    Create a Pit from a snowpylot SnowPit object.

    Extracts slope angle, pit ID, snow layers, and stability test results
    from the raw snowpylot object and returns a clean Pit data structure.

    Parameters
    ----------
    snow_pit : Any
        SnowPit object from snowpylot (via caaml_parser)

    Returns
    -------
    Pit
        Initialized Pit object with layers and test results
    """
    # Deferred import avoids circular dependency (pit.py imports pit_parser.py)
    from snowpyt_mechparams.models.pit import Pit

    slope_angle: Any = float("nan")
    try:
        slope_angle = _ufloat(
            snow_pit.core_info.location.slope_angle[0], U_SLOPE_ANGLE
        )
    except (AttributeError, IndexError, TypeError, ValueError):
        pass

    pit_id: Optional[str] = None
    try:
        pit_id = snow_pit.core_info.pit_id
    except (AttributeError, TypeError):
        pass

    layers = _create_layers(snow_pit)

    ect_results: Optional[List[Any]] = None
    ct_results: Optional[List[Any]] = None
    pst_results: Optional[List[Any]] = None
    if hasattr(snow_pit, "stability_tests") and snow_pit.stability_tests:
        st = snow_pit.stability_tests
        ect_results = st.ECT if st.ECT else []
        ct_results = st.CT if st.CT else []
        pst_results = st.PST if st.PST else []

    return Pit(
        pit_id=pit_id,
        slope_angle=slope_angle,
        layers=layers,
        ECT_results=ect_results,
        CT_results=ct_results,
        PST_results=pst_results,
    )


def _get_value_safe(obj: Any) -> Optional[float]:
    """
    Safely extract a scalar value from an object that might be None, scalar,
    or array-like.

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
    return cast(Optional[float], obj)


def _create_layers(snow_pit: Any, include_density: bool = True) -> List[Layer]:
    """
    Convert a snowpylot SnowPit's snow profile into a list of Layer objects.

    Parameters
    ----------
    snow_pit : Any
        SnowPit object from snowpylot
    include_density : bool
        If True, attempts to match and include direct density measurements

    Returns
    -------
    List[Layer]
        List of Layer objects representing the snow layers
    """
    layers: List[Layer] = []

    try:
        if not snow_pit.snow_profile.layers:
            return layers
    except (AttributeError, TypeError):
        return layers

    for layer in snow_pit.snow_profile.layers:
        depth_top = layer.depth_top[0] if layer.depth_top else None

        thickness: Optional[UncertainValue] = None
        if layer.thickness:
            t = layer.thickness[0]
            thickness = _ufloat(t, abs(t) * U_THICKNESS_FRACTION)

        hand_hardness = layer.hardness if hasattr(layer, "hardness") else None
        is_layer_of_concern = getattr(layer, "layer_of_concern", False)

        grain_form = None
        if hasattr(layer, "grain_form_primary") and layer.grain_form_primary:
            grain_form_sub = getattr(
                layer.grain_form_primary, "sub_grain_class_code", None
            )
            grain_form_basic = getattr(
                layer.grain_form_primary, "basic_grain_class_code", None
            )
            grain_form = grain_form_sub if grain_form_sub else grain_form_basic

        grain_size_avg: Optional[UncertainValue] = None
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

        density_measured: Optional[UncertainValue] = None
        if include_density:
            try:
                for density_obs in snow_pit.snow_profile.density_profile:
                    if (
                        density_obs.depth_top == layer.depth_top
                        and density_obs.thickness == layer.thickness
                    ):
                        if (
                            isinstance(density_obs.density, list)
                            and len(density_obs.density) > 0
                        ):
                            rho = float(density_obs.density[0])
                        else:
                            rho = float(density_obs.density)
                        density_measured = _ufloat(rho, abs(rho) * U_DENSITY_FRACTION)
                        break
            except (AttributeError, TypeError):
                pass

        layers.append(
            Layer(
                depth_top=depth_top,
                thickness=thickness,
                density_measured=density_measured,
                hand_hardness=hand_hardness,
                grain_form=grain_form,
                grain_size_avg=grain_size_avg,
                layer_of_concern=is_layer_of_concern,
            )
        )

    return layers


def extract_test_properties(test_result: Any, test_type: str) -> dict:
    """
    Extract properties from a stability test result for slab metadata.

    Parameters
    ----------
    test_result : Any
        Test result object from snowpylot
    test_type : str
        Type of test ("ECT" or "CT")

    Returns
    -------
    dict
        Dictionary of test properties
    """
    props: dict = {}

    if test_type == "ECT":
        if hasattr(test_result, "test_score"):
            props["score"] = (
                str(test_result.test_score) if test_result.test_score else None
            )
        if hasattr(test_result, "propagation"):
            props["propagation"] = test_result.propagation
        if hasattr(test_result, "depth_top"):
            props["depth_top"] = _get_value_safe(test_result.depth_top)

    elif test_type == "CT":
        if hasattr(test_result, "test_score"):
            props["score"] = (
                str(test_result.test_score) if test_result.test_score else None
            )
        if hasattr(test_result, "fracture_character"):
            props["fracture_character"] = test_result.fracture_character
        if hasattr(test_result, "depth_top"):
            props["depth_top"] = _get_value_safe(test_result.depth_top)

    return props
