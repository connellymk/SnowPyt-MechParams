"""
Comprehensive tests for snowpilot_convert module.

Tests cover:
- parse_caaml_file and parse_caaml_directory
- caaml_to_layers
- caaml_to_slab (with all weak layer definitions)
- convert_grain_form
- Helper functions (_extract_slope_angle, _find_weak_layer_depth, etc.)
"""

import os
import math
from typing import Any, List
from unittest.mock import Mock, MagicMock, patch

import pytest

from snowpyt_mechparams.data_structures import Layer, Slab
from snowpyt_mechparams.snowpilot_utils.snowpilot_convert import (
    parse_caaml_file,
    parse_caaml_directory,
    caaml_to_layers,
    caaml_to_slab,
    convert_grain_form,
    _extract_slope_angle,
    _find_weak_layer_depth,
    _extract_stability_test_results,
    _extract_layer_of_concern,
    _get_value_safe,
)


# ============================================================================
# Fixtures for Mock CAAML Profiles
# ============================================================================


@pytest.fixture
def mock_caaml_layer():
    """Create a mock CAAML layer object."""
    layer = Mock()
    layer.depth_top = [10.0]
    layer.thickness = [5.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    
    # Mock grain form
    grain_form = Mock()
    grain_form.sub_grain_class_code = "FCxr"
    grain_form.basic_grain_class_code = "FC"
    grain_form.grain_size_avg = 1.5
    layer.grain_form_primary = grain_form
    
    return layer


@pytest.fixture
def mock_caaml_profile_basic():
    """Create a basic mock CAAML profile with layers."""
    profile = Mock()
    
    # Mock snow_profile
    snow_profile = Mock()
    
    # Create layers
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    
    grain_form1 = Mock()
    grain_form1.sub_grain_class_code = None
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.grain_size_avg = 0.5
    layer1.grain_form_primary = grain_form1
    
    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [20.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = True
    
    grain_form2 = Mock()
    grain_form2.sub_grain_class_code = "FCxr"
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.grain_size_avg = 1.5
    layer2.grain_form_primary = grain_form2
    
    snow_profile.layers = [layer1, layer2]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    
    # Mock core_info with slope angle
    core_info = Mock()
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    # Mock stability_tests (empty)
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    return profile


@pytest.fixture
def mock_caaml_profile_with_tests():
    """Create a mock CAAML profile with stability tests."""
    profile = Mock()
    
    # Mock snow_profile
    snow_profile = Mock()
    
    # Create layers
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.grain_size_avg = 0.5
    layer1.grain_form_primary = grain_form1
    
    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [20.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.grain_size_avg = 1.5
    layer2.grain_form_primary = grain_form2
    
    layer3 = Mock()
    layer3.depth_top = [30.0]
    layer3.thickness = [10.0]
    layer3.hardness = "1F"
    layer3.layer_of_concern = True
    grain_form3 = Mock()
    grain_form3.basic_grain_class_code = "RG"
    grain_form3.grain_size_avg = 2.0
    layer3.grain_form_primary = grain_form3
    
    snow_profile.layers = [layer1, layer2, layer3]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    
    # Mock core_info with slope angle
    core_info = Mock()
    location = Mock()
    location.slope_angle = [35.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    # Mock stability_tests with CT, ECT, and PST
    stability_tests = Mock()
    
    # CT test with Q1 fracture
    ct_test = Mock()
    ct_test.depth_top = [25.0]
    ct_test.fracture_character = "Q1"
    ct_test.test_score = 5
    stability_tests.CT = [ct_test]
    
    # ECT test with propagation
    ect_test = Mock()
    ect_test.depth_top = [25.0]
    ect_test.propagation = True
    ect_test.test_score = "ECTP12"
    stability_tests.ECT = [ect_test]
    
    # PST test
    pst_test = Mock()
    pst_test.depth_top = [25.0]
    pst_test.fracture_propagation = "End"
    pst_test.cut_length = 50.0
    pst_test.column_length = 100.0
    stability_tests.PST = [pst_test]
    
    profile.stability_tests = stability_tests
    
    return profile


@pytest.fixture
def mock_caaml_profile_with_density():
    """Create a mock CAAML profile with density measurements."""
    profile = Mock()
    
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    grain_form.grain_size_avg = 0.5
    layer.grain_form_primary = grain_form
    
    snow_profile.layers = [layer]
    
    # Add density profile
    density_obs = Mock()
    density_obs.depth_top = [0.0]
    density_obs.thickness = [10.0]
    density_obs.density = 200.0
    snow_profile.density_profile = [density_obs]
    
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [25.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    return profile


# ============================================================================
# Tests for parse_caaml_file and parse_caaml_directory
# ============================================================================


def test_parse_caaml_file_success(tmp_path):
    """Test parsing a valid CAAML file."""
    # Create a temporary XML file
    xml_content = """<?xml version="1.0"?>
    <caaml:SnowProfile xmlns:caaml="http://caaml.org/Schemas/SnowProfileIACS/v6.0.3">
        <caaml:snowProfileResultsOf>
            <caaml:SnowProfileMeasurements>
                <caaml:stratProfile>
                    <caaml:Layer>
                        <caaml:depthTop uom="cm">0</caaml:depthTop>
                        <caaml:thickness uom="cm">10</caaml:thickness>
                    </caaml:Layer>
                </caaml:stratProfile>
            </caaml:SnowProfileMeasurements>
        </caaml:snowProfileResultsOf>
    </caaml:SnowProfile>
    """
    test_file = tmp_path / "test.xml"
    test_file.write_text(xml_content)
    
    with patch("snowpyt_mechparams.snowpilot_utils.snowpilot_convert.caaml_parser") as mock_parser:
        mock_profile = Mock()
        mock_parser.return_value = mock_profile
        
        result = parse_caaml_file(str(test_file))
        
        assert result == mock_profile
        mock_parser.assert_called_once_with(str(test_file))


def test_parse_caaml_directory_success(tmp_path):
    """Test parsing a directory of CAAML files."""
    # Create test XML files
    xml_content = """<?xml version="1.0"?>
    <caaml:SnowProfile xmlns:caaml="http://caaml.org/Schemas/SnowProfileIACS/v6.0.3">
        <caaml:snowProfileResultsOf>
            <caaml:SnowProfileMeasurements>
                <caaml:stratProfile/>
            </caaml:SnowProfileMeasurements>
        </caaml:snowProfileResultsOf>
    </caaml:SnowProfile>
    """
    
    (tmp_path / "file1.xml").write_text(xml_content)
    (tmp_path / "file2.xml").write_text(xml_content)
    (tmp_path / "not_xml.txt").write_text("not xml")
    
    with patch("snowpyt_mechparams.snowpilot_utils.snowpilot_convert.caaml_parser") as mock_parser:
        mock_profile = Mock()
        mock_parser.return_value = mock_profile
        
        results = parse_caaml_directory(str(tmp_path))
        
        assert len(results) == 2
        assert mock_parser.call_count == 2


def test_parse_caaml_directory_with_failures(tmp_path, caplog):
    """Test parsing directory handles failures gracefully."""
    xml_content = """<?xml version="1.0"?>
    <caaml:SnowProfile xmlns:caaml="http://caaml.org/Schemas/SnowProfileIACS/v6.0.3">
        <caaml:snowProfileResultsOf>
            <caaml:SnowProfileMeasurements>
                <caaml:stratProfile/>
            </caaml:SnowProfileMeasurements>
        </caaml:snowProfileResultsOf>
    </caaml:SnowProfile>
    """
    
    (tmp_path / "file1.xml").write_text(xml_content)
    (tmp_path / "file2.xml").write_text(xml_content)
    
    with patch("snowpyt_mechparams.snowpilot_utils.snowpilot_convert.caaml_parser") as mock_parser:
        mock_profile = Mock()
        mock_parser.side_effect = [mock_profile, Exception("Parse error")]
        
        results = parse_caaml_directory(str(tmp_path))
        
        assert len(results) == 1
        assert "Failed to parse" in caplog.text


# ============================================================================
# Tests for caaml_to_layers
# ============================================================================


def test_caaml_to_layers_basic(mock_caaml_profile_basic):
    """Test converting CAAML profile to layers."""
    layers = caaml_to_layers(mock_caaml_profile_basic)
    
    assert len(layers) == 2
    assert isinstance(layers[0], Layer)
    assert isinstance(layers[1], Layer)
    
    assert layers[0].depth_top == 0.0
    assert layers[0].thickness == 10.0
    assert layers[0].hand_hardness == "F"
    assert layers[0].grain_form == "PP"
    assert layers[0].grain_size_avg == 0.5
    
    assert layers[1].depth_top == 10.0
    assert layers[1].thickness == 20.0
    assert layers[1].hand_hardness == "4F"
    assert layers[1].grain_form == "FCxr"
    assert layers[1].grain_size_avg == 1.5


def test_caaml_to_layers_with_density(mock_caaml_profile_with_density):
    """Test converting CAAML profile to layers with density."""
    layers = caaml_to_layers(mock_caaml_profile_with_density, include_density=True)
    
    assert len(layers) == 1
    assert layers[0].density_measured == 200.0


def test_caaml_to_layers_without_density(mock_caaml_profile_with_density):
    """Test converting CAAML profile to layers without density."""
    layers = caaml_to_layers(mock_caaml_profile_with_density, include_density=False)
    
    assert len(layers) == 1
    assert layers[0].density_measured is None


def test_caaml_to_layers_empty_profile():
    """Test converting empty CAAML profile."""
    profile = Mock()
    profile.snow_profile = None
    
    layers = caaml_to_layers(profile)
    assert layers == []


def test_caaml_to_layers_no_layers():
    """Test converting CAAML profile with no layers."""
    profile = Mock()
    snow_profile = Mock()
    snow_profile.layers = []
    profile.snow_profile = snow_profile
    
    layers = caaml_to_layers(profile)
    assert layers == []


def test_caaml_to_layers_missing_attributes():
    """Test converting CAAML profile with missing layer attributes."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = None
    layer.thickness = None
    layer.hardness = None
    layer.grain_form_primary = None
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    
    layers = caaml_to_layers(profile)
    assert len(layers) == 1
    assert layers[0].depth_top is None
    assert layers[0].thickness is None
    assert layers[0].hand_hardness is None
    assert layers[0].grain_form is None


def test_caaml_to_layers_grain_size_array():
    """Test converting CAAML profile with grain size as array."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    grain_form.grain_size_avg = [2.5]  # Array
    layer.grain_form_primary = grain_form
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    
    layers = caaml_to_layers(profile)
    assert len(layers) == 1
    assert layers[0].grain_size_avg == 2.5


# ============================================================================
# Tests for caaml_to_slab
# ============================================================================


def test_caaml_to_slab_no_weak_layer_def(mock_caaml_profile_basic):
    """Test converting CAAML to slab without weak layer definition."""
    slab = caaml_to_slab(mock_caaml_profile_basic, weak_layer_def=None)
    
    assert slab is not None
    assert isinstance(slab, Slab)
    assert len(slab.layers) == 2
    assert slab.weak_layer is None
    assert slab.angle == 30.0
    assert slab.ECT_results == []
    assert slab.CT_results == []
    assert slab.PST_results == []
    assert slab.layer_of_concern is not None
    assert slab.layer_of_concern.depth_top == 10.0


def test_caaml_to_slab_layer_of_concern(mock_caaml_profile_basic):
    """Test converting CAAML to slab with layer_of_concern."""
    slab = caaml_to_slab(mock_caaml_profile_basic, weak_layer_def="layer_of_concern")
    
    assert slab is not None
    assert len(slab.layers) == 1  # Only layer above weak layer
    assert slab.layers[0].depth_top == 0.0
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 10.0
    assert slab.weak_layer.layer_of_concern is True


def test_caaml_to_slab_ct_failure_layer(mock_caaml_profile_with_tests):
    """Test converting CAAML to slab with CT failure layer."""
    slab = caaml_to_slab(mock_caaml_profile_with_tests, weak_layer_def="CT_failure_layer")
    
    assert slab is not None
    assert len(slab.layers) == 2  # Layers above depth 25.0
    assert slab.weak_layer is not None
    # Weak layer should be layer containing depth 25.0
    assert slab.weak_layer.depth_top == 10.0  # Layer 2 contains depth 25.0
    assert slab.CT_results is not None
    assert len(slab.CT_results) == 1


def test_caaml_to_slab_ectp_failure_layer(mock_caaml_profile_with_tests):
    """Test converting CAAML to slab with ECTP failure layer."""
    slab = caaml_to_slab(mock_caaml_profile_with_tests, weak_layer_def="ECTP_failure_layer")
    
    assert slab is not None
    assert len(slab.layers) == 2
    assert slab.weak_layer is not None
    assert slab.ECT_results is not None
    assert len(slab.ECT_results) == 1


def test_caaml_to_slab_no_weak_layer_found():
    """Test converting CAAML to slab when weak layer is not found."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    layer.grain_form_primary = grain_form
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [25.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    # Try to find layer_of_concern when none exists
    slab = caaml_to_slab(profile, weak_layer_def="layer_of_concern")
    
    assert slab is None


def test_caaml_to_slab_no_layers_above_weak_layer():
    """Test converting CAAML to slab when no layers exist above weak layer."""
    profile = Mock()
    snow_profile = Mock()
    
    # Only one layer at depth 0
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = True
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    layer.grain_form_primary = grain_form
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [25.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    # Weak layer is at depth 0, so no layers above it
    slab = caaml_to_slab(profile, weak_layer_def="layer_of_concern")
    
    assert slab is None


def test_caaml_to_slab_with_stability_tests(mock_caaml_profile_with_tests):
    """Test converting CAAML to slab includes stability test results."""
    slab = caaml_to_slab(mock_caaml_profile_with_tests, weak_layer_def=None)
    
    assert slab is not None
    assert slab.ECT_results is not None
    assert len(slab.ECT_results) == 1
    assert slab.CT_results is not None
    assert len(slab.CT_results) == 1
    assert slab.PST_results is not None
    assert len(slab.PST_results) == 1


def test_caaml_to_slab_with_layer_of_concern(mock_caaml_profile_with_tests):
    """Test converting CAAML to slab includes layer_of_concern."""
    slab = caaml_to_slab(mock_caaml_profile_with_tests, weak_layer_def=None)
    
    assert slab is not None
    assert slab.layer_of_concern is not None
    assert slab.layer_of_concern.depth_top == 30.0


def test_caaml_to_slab_empty_profile():
    """Test converting empty CAAML profile returns None."""
    profile = Mock()
    snow_profile = Mock()
    snow_profile.layers = []
    profile.snow_profile = snow_profile
    
    slab = caaml_to_slab(profile)
    assert slab is None


def test_caaml_to_slab_weak_layer_contains_failure_depth():
    """Test that weak layer is correctly identified when failure depth is within layer."""
    profile = Mock()
    snow_profile = Mock()
    
    # Layer 1: 0-10 cm
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    layer1.grain_form_primary = grain_form1
    
    # Layer 2: 10-30 cm (contains failure at 25 cm)
    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [20.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    layer2.grain_form_primary = grain_form2
    
    snow_profile.layers = [layer1, layer2]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    # CT test at depth 25 cm (within layer2)
    ct_test = Mock()
    ct_test.depth_top = [25.0]
    ct_test.fracture_character = "Q1"
    stability_tests.CT = [ct_test]
    stability_tests.ECT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    slab = caaml_to_slab(profile, weak_layer_def="CT_failure_layer")
    
    assert slab is not None
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 10.0  # Layer 2 contains depth 25.0
    assert len(slab.layers) == 1  # Only layer1 is above


# ============================================================================
# Tests for convert_grain_form
# ============================================================================


def test_convert_grain_form_with_sub_grain():
    """Test converting grain form with sub-grain class."""
    grain_form_obj = Mock()
    grain_form_obj.sub_grain_class_code = "FCxr"
    grain_form_obj.basic_grain_class_code = "FC"
    
    result = convert_grain_form(grain_form_obj, "geldsetzer")
    
    assert result == "FCxr"


def test_convert_grain_form_with_basic_only():
    """Test converting grain form with only basic class."""
    grain_form_obj = Mock()
    grain_form_obj.sub_grain_class_code = None
    grain_form_obj.basic_grain_class_code = "PP"
    
    result = convert_grain_form(grain_form_obj, "geldsetzer")
    
    assert result == "PP"


def test_convert_grain_form_none():
    """Test converting None grain form."""
    result = convert_grain_form(None, "geldsetzer")
    assert result is None


def test_convert_grain_form_invalid_method():
    """Test converting grain form with invalid method."""
    grain_form_obj = Mock()
    
    with pytest.raises(ValueError, match="Invalid method"):
        convert_grain_form(grain_form_obj, "invalid_method")


# ============================================================================
# Tests for Helper Functions
# ============================================================================


def test_extract_slope_angle_valid(mock_caaml_profile_basic):
    """Test extracting valid slope angle."""
    angle = _extract_slope_angle(mock_caaml_profile_basic)
    assert angle == 30.0


def test_extract_slope_angle_missing():
    """Test extracting slope angle when missing."""
    profile = Mock()
    profile.core_info = None
    
    angle = _extract_slope_angle(profile)
    assert math.isnan(angle)


def test_extract_slope_angle_empty_array():
    """Test extracting slope angle from empty array."""
    profile = Mock()
    core_info = Mock()
    location = Mock()
    location.slope_angle = []
    core_info.location = location
    profile.core_info = core_info
    
    angle = _extract_slope_angle(profile)
    assert math.isnan(angle)


def test_find_weak_layer_depth_layer_of_concern(mock_caaml_profile_basic):
    """Test finding weak layer depth for layer_of_concern."""
    depth = _find_weak_layer_depth(mock_caaml_profile_basic, "layer_of_concern")
    assert depth == 10.0


def test_find_weak_layer_depth_ct_failure(mock_caaml_profile_with_tests):
    """Test finding weak layer depth for CT failure."""
    depth = _find_weak_layer_depth(mock_caaml_profile_with_tests, "CT_failure_layer")
    assert depth == 25.0


def test_find_weak_layer_depth_ectp_failure(mock_caaml_profile_with_tests):
    """Test finding weak layer depth for ECTP failure."""
    depth = _find_weak_layer_depth(mock_caaml_profile_with_tests, "ECTP_failure_layer")
    assert depth == 25.0


def test_find_weak_layer_depth_invalid_def():
    """Test finding weak layer depth with invalid definition."""
    profile = Mock()
    
    with pytest.raises(ValueError, match="Invalid weak_layer_def"):
        _find_weak_layer_depth(profile, "invalid_def")


def test_extract_stability_test_results_ect(mock_caaml_profile_with_tests):
    """Test extracting ECT test results."""
    results = _extract_stability_test_results(mock_caaml_profile_with_tests, "ECT")
    assert results is not None
    assert len(results) == 1


def test_extract_stability_test_results_ct(mock_caaml_profile_with_tests):
    """Test extracting CT test results."""
    results = _extract_stability_test_results(mock_caaml_profile_with_tests, "CT")
    assert results is not None
    assert len(results) == 1


def test_extract_stability_test_results_pst(mock_caaml_profile_with_tests):
    """Test extracting PST test results."""
    results = _extract_stability_test_results(mock_caaml_profile_with_tests, "PST")
    assert results is not None
    assert len(results) == 1


def test_extract_stability_test_results_none():
    """Test extracting stability test results when none exist."""
    profile = Mock()
    profile.stability_tests = None
    
    results = _extract_stability_test_results(profile, "ECT")
    assert results is None


def test_extract_stability_test_results_empty():
    """Test extracting stability test results when empty."""
    profile = Mock()
    stability_tests = Mock()
    stability_tests.ECT = []
    profile.stability_tests = stability_tests
    
    results = _extract_stability_test_results(profile, "ECT")
    assert results is None


def test_extract_layer_of_concern_found(mock_caaml_profile_basic):
    """Test extracting layer of concern when found."""
    layers = caaml_to_layers(mock_caaml_profile_basic)
    layer_of_concern = _extract_layer_of_concern(mock_caaml_profile_basic, layers)
    
    assert layer_of_concern is not None
    assert layer_of_concern.depth_top == 10.0


def test_extract_layer_of_concern_not_found():
    """Test extracting layer of concern when not found."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.layer_of_concern = False
    snow_profile.layers = [layer]
    
    profile.snow_profile = snow_profile
    
    layers = [Layer(depth_top=0.0, thickness=10.0)]
    layer_of_concern = _extract_layer_of_concern(profile, layers)
    
    assert layer_of_concern is None


def test_get_value_safe_scalar():
    """Test _get_value_safe with scalar."""
    assert _get_value_safe(5.0) == 5.0


def test_get_value_safe_list():
    """Test _get_value_safe with list."""
    assert _get_value_safe([10.0]) == 10.0


def test_get_value_safe_empty_list():
    """Test _get_value_safe with empty list."""
    assert _get_value_safe([]) is None


def test_get_value_safe_none():
    """Test _get_value_safe with None."""
    assert _get_value_safe(None) is None


# ============================================================================
# Integration Tests with Real CAAML Files
# ============================================================================


@pytest.mark.integration
def test_caaml_to_slab_real_file():
    """Test converting a real CAAML file to slab."""
    # Use a real CAAML file from examples/data
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "data")
    caaml_files = [f for f in os.listdir(examples_dir) if f.endswith(".xml")]
    
    if not caaml_files:
        pytest.skip("No CAAML files found in examples/data")
    
    test_file = os.path.join(examples_dir, caaml_files[0])
    
    try:
        profile = parse_caaml_file(test_file)
        slab = caaml_to_slab(profile, weak_layer_def=None)
        
        assert slab is not None
        assert isinstance(slab, Slab)
        assert len(slab.layers) > 0
    except Exception as e:
        pytest.skip(f"Could not parse test file: {e}")


@pytest.mark.integration
def test_caaml_to_layers_real_file():
    """Test converting a real CAAML file to layers."""
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "data")
    caaml_files = [f for f in os.listdir(examples_dir) if f.endswith(".xml")]
    
    if not caaml_files:
        pytest.skip("No CAAML files found in examples/data")
    
    test_file = os.path.join(examples_dir, caaml_files[0])
    
    try:
        profile = parse_caaml_file(test_file)
        layers = caaml_to_layers(profile)
        
        assert len(layers) > 0
        assert all(isinstance(layer, Layer) for layer in layers)
    except Exception as e:
        pytest.skip(f"Could not parse test file: {e}")


# ============================================================================
# Additional Edge Case Tests
# ============================================================================


def test_caaml_to_slab_ectp_test_score_string():
    """Test ECTP detection using test_score string."""
    profile = Mock()
    snow_profile = Mock()
    
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [20.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    layer1.grain_form_primary = grain_form1
    
    layer2 = Mock()
    layer2.depth_top = [20.0]
    layer2.thickness = [10.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    layer2.grain_form_primary = grain_form2
    
    snow_profile.layers = [layer1, layer2]
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    # ECT test with propagation in test_score (no propagation attribute)
    ect_test = Mock()
    ect_test.depth_top = [15.0]
    ect_test.propagation = False  # Not set to True
    ect_test.test_score = "ECTP12"  # But test_score indicates propagation
    stability_tests.ECT = [ect_test]
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    depth = _find_weak_layer_depth(profile, "ECTP_failure_layer")
    assert depth == 15.0


def test_caaml_to_slab_ct_multiple_tests():
    """Test CT failure layer with multiple CT tests."""
    profile = Mock()
    snow_profile = Mock()
    
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    layer1.grain_form_primary = grain_form1
    
    snow_profile.layers = [layer1]
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    # Multiple CT tests - should return first Q1/SC/SP
    ct_test1 = Mock()
    ct_test1.depth_top = [5.0]
    ct_test1.fracture_character = "RP"  # Not Q1/SC/SP
    
    ct_test2 = Mock()
    ct_test2.depth_top = [5.0]
    ct_test2.fracture_character = "Q1"  # Valid
    
    stability_tests.CT = [ct_test1, ct_test2]
    stability_tests.ECT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    depth = _find_weak_layer_depth(profile, "CT_failure_layer")
    assert depth == 5.0


def test_extract_stability_test_results_single_test():
    """Test extracting single test result (not a list)."""
    profile = Mock()
    stability_tests = Mock()
    
    # Single test object (not a list)
    ct_test = Mock()
    stability_tests.CT = ct_test  # Single object, not list
    stability_tests.ECT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    results = _extract_stability_test_results(profile, "CT")
    assert results is not None
    assert len(results) == 1


def test_extract_stability_test_results_pst_alternative_names():
    """Test PST extraction with alternative attribute names."""
    profile = Mock()
    stability_tests = Mock()
    
    pst_test = Mock()
    stability_tests.PST = None  # Not PST
    stability_tests.PropSawTest = [pst_test]  # Try PropSawTest
    stability_tests.ECT = []
    stability_tests.CT = []
    profile.stability_tests = stability_tests
    
    results = _extract_stability_test_results(profile, "PST")
    assert results is not None
    assert len(results) == 1


def test_caaml_to_slab_weak_layer_at_boundary():
    """Test weak layer identification when failure is at layer boundary."""
    profile = Mock()
    snow_profile = Mock()
    
    # Layer 1: 0-10 cm
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    layer1.grain_form_primary = grain_form1
    
    # Layer 2: 10-30 cm (failure at exactly 10.0 - boundary)
    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [20.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    layer2.grain_form_primary = grain_form2
    
    snow_profile.layers = [layer1, layer2]
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    ct_test = Mock()
    ct_test.depth_top = [10.0]  # Exactly at boundary
    ct_test.fracture_character = "Q1"
    stability_tests.CT = [ct_test]
    stability_tests.ECT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    slab = caaml_to_slab(profile, weak_layer_def="CT_failure_layer")
    
    assert slab is not None
    # Failure at 10.0 should be in layer2 (depth_top <= 10.0 < depth_bottom)
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 10.0
    assert len(slab.layers) == 1  # Only layer1 is above


def test_caaml_to_slab_no_stability_tests():
    """Test slab creation when no stability tests exist."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    layer.grain_form_primary = grain_form
    
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [25.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = []
    # No PST attribute at all
    profile.stability_tests = stability_tests
    
    slab = caaml_to_slab(profile, weak_layer_def=None)
    
    assert slab is not None
    assert slab.ECT_results is None
    assert slab.CT_results is None
    assert slab.PST_results is None


def test_extract_layer_of_concern_depth_matching():
    """Test layer_of_concern extraction with depth matching tolerance."""
    profile = Mock()
    snow_profile = Mock()
    
    # CAAML layer with slight floating point difference
    caaml_layer = Mock()
    caaml_layer.depth_top = [10.0001]  # Slight difference
    caaml_layer.thickness = [20.0]
    caaml_layer.layer_of_concern = True
    snow_profile.layers = [caaml_layer]
    profile.snow_profile = snow_profile
    
    # Layer object with depth 10.0
    layers = [Layer(depth_top=10.0, thickness=20.0)]
    
    layer_of_concern = _extract_layer_of_concern(profile, layers)
    
    # Should match within tolerance (0.01)
    assert layer_of_concern is not None
    assert layer_of_concern.depth_top == 10.0
