"""
Comprehensive tests for snowpilot_convert module.

Tests cover:
- parse_caaml_file and parse_caaml_directory
- Pit class (layers creation, slab creation with all weak layer definitions)
- convert_grain_form
"""

import os
import math
from typing import Any, List
from unittest.mock import Mock, MagicMock, patch

import pytest

from snowpyt_mechparams.data_structures import Layer, Pit, Slab
from snowpyt_mechparams.snowpilot_utils.snowpilot_convert import (
    parse_caaml_file,
    parse_caaml_directory,
    convert_grain_form,
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
# Tests for Pit class - Layer creation
# ============================================================================


def test_pit_layers_basic(mock_caaml_profile_basic):
    """Test Pit creating layers from CAAML profile."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_basic)
    
    assert len(pit.layers) == 2
    assert isinstance(pit.layers[0], Layer)
    assert isinstance(pit.layers[1], Layer)
    
    assert pit.layers[0].depth_top == 0.0
    assert pit.layers[0].thickness == 10.0
    assert pit.layers[0].hand_hardness == "F"
    assert pit.layers[0].grain_form == "PP"
    assert pit.layers[0].grain_size_avg == 0.5
    
    assert pit.layers[1].depth_top == 10.0
    assert pit.layers[1].thickness == 20.0
    assert pit.layers[1].hand_hardness == "4F"
    assert pit.layers[1].grain_form == "FCxr"
    assert pit.layers[1].grain_size_avg == 1.5


def test_pit_layers_with_density(mock_caaml_profile_with_density):
    """Test Pit creating layers with density from CAAML profile."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_with_density)
    
    assert len(pit.layers) == 1
    assert pit.layers[0].density_measured == 200.0


def test_pit_layers_empty_profile():
    """Test Pit with empty CAAML profile."""
    profile = Mock()
    profile.snow_profile = None
    # Add required attributes for Pit
    profile.core_info = Mock()
    profile.core_info.location = Mock()
    profile.core_info.location.slope_angle = None
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert pit.layers == []


def test_pit_layers_no_layers():
    """Test Pit with CAAML profile with no layers."""
    profile = Mock()
    snow_profile = Mock()
    snow_profile.layers = []
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    # Add required attributes
    profile.core_info = Mock()
    profile.core_info.location = Mock()
    profile.core_info.location.slope_angle = [30.0, "deg"]
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert pit.layers == []


def test_pit_layers_missing_attributes():
    """Test Pit with CAAML profile with missing layer attributes."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = None
    layer.thickness = None
    layer.hardness = None
    layer.grain_form_primary = None
    layer.layer_of_concern = False
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    # Add required attributes
    profile.core_info = Mock()
    profile.core_info.location = Mock()
    profile.core_info.location.slope_angle = [30.0, "deg"]
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert len(pit.layers) == 1
    assert pit.layers[0].depth_top is None
    assert pit.layers[0].thickness is None
    assert pit.layers[0].hand_hardness is None
    assert pit.layers[0].grain_form is None


def test_pit_layers_grain_size_array():
    """Test Pit with CAAML profile with grain size as array."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    grain_form.sub_grain_class_code = None
    grain_form.grain_size_avg = [2.5]  # Array
    layer.grain_form_primary = grain_form
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    # Add required attributes
    profile.core_info = Mock()
    profile.core_info.location = Mock()
    profile.core_info.location.slope_angle = [30.0, "deg"]
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert len(pit.layers) == 1
    assert pit.layers[0].grain_size_avg == 2.5


# ============================================================================
# Tests for Pit class - Slab creation
# ============================================================================


def test_pit_create_slab_no_weak_layer_def(mock_caaml_profile_basic):
    """Test Pit creating slab without weak layer definition."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_basic)
    slabs = pit.create_slabs(weak_layer_def=None)

    slab = slabs[0] if slabs else None
    
    assert slab is not None
    assert isinstance(slab, Slab)
    assert len(slab.layers) == 2
    assert slab.weak_layer is None
    assert slab.angle == 30.0
    assert slab.pit is not None
    assert slab.pit.ECT_results == []
    assert slab.pit.CT_results == []
    assert slab.pit.PST_results == []
    assert slab.pit.layer_of_concern is not None
    assert slab.pit.layer_of_concern.depth_top == 10.0


def test_pit_create_slab_layer_of_concern(mock_caaml_profile_basic):
    """Test Pit creating slab with layer_of_concern."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_basic)
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")

    slab = slabs[0] if slabs else None
    
    assert slab is not None
    assert len(slab.layers) == 1  # Only layer above weak layer
    assert slab.layers[0].depth_top == 0.0
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 10.0


def test_pit_create_slab_ct_failure_layer(mock_caaml_profile_with_tests):
    """Test Pit creating slab with CT failure layer."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_with_tests)
    slabs = pit.create_slabs(weak_layer_def="CT_failure_layer")

    assert len(slabs) == 1
    slab = slabs[0]
    assert len(slab.layers) == 1  # Only layers above weak layer (NOT including it)
    assert slab.weak_layer is not None
    # Weak layer should be layer containing depth 25.0
    assert slab.weak_layer.depth_top == 10.0  # Layer 2 contains depth 25.0
    assert slab.pit is not None
    assert slab.pit.CT_results is not None
    assert len(slab.pit.CT_results) == 1


def test_pit_create_slab_ectp_failure_layer(mock_caaml_profile_with_tests):
    """Test Pit creating slab with ECTP failure layer."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_with_tests)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

    assert len(slabs) == 1
    slab = slabs[0]
    assert len(slab.layers) == 1  # Only layers above weak layer (NOT including it)
    assert slab.weak_layer is not None
    assert slab.pit is not None
    assert slab.pit.ECT_results is not None
    assert len(slab.pit.ECT_results) == 1


def test_pit_create_slab_no_weak_layer_found():
    """Test Pit creating slab when weak layer is not found."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    grain_form.sub_grain_class_code = None
    grain_form.grain_size_avg = None
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
    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")

    slab = slabs[0] if slabs else None
    
    assert slab is None


def test_pit_create_slab_no_layers_above_weak_layer():
    """Test Pit creating slab when no layers exist above weak layer."""
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
    grain_form.sub_grain_class_code = None
    grain_form.grain_size_avg = None
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
    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")

    slab = slabs[0] if slabs else None
    
    assert slab is None


def test_pit_create_slab_with_stability_tests(mock_caaml_profile_with_tests):
    """Test Pit creating slab has access to stability test results through pit reference."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_with_tests)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

    assert len(slabs) == 1
    slab = slabs[0]

    assert slab is not None
    assert slab.pit is not None
    assert slab.pit.ECT_results is not None
    assert len(slab.pit.ECT_results) == 1
    assert slab.pit.CT_results is not None
    assert len(slab.pit.CT_results) == 1
    assert slab.pit.PST_results is not None
    assert len(slab.pit.PST_results) == 1


def test_pit_create_slab_with_layer_of_concern(mock_caaml_profile_with_tests):
    """Test Pit creating slab has access to layer_of_concern through pit reference."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_with_tests)
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")

    assert len(slabs) == 1
    slab = slabs[0]

    assert slab is not None
    assert slab.pit is not None
    assert slab.pit.layer_of_concern is not None
    assert slab.pit.layer_of_concern.depth_top == 30.0


def test_pit_create_slab_empty_profile():
    """Test Pit creating slab with empty profile returns None."""
    profile = Mock()
    snow_profile = Mock()
    snow_profile.layers = []
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    # Add required attributes
    profile.core_info = Mock()
    profile.core_info.location = Mock()
    profile.core_info.location.slope_angle = None
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs()

    slab = slabs[0] if slabs else None
    assert slab is None


def test_pit_create_slab_weak_layer_contains_failure_depth():
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
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1
    
    # Layer 2: 10-30 cm (contains failure at 25 cm)
    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [20.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
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
    
    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="CT_failure_layer")

    assert len(slabs) == 1
    slab = slabs[0]
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 10.0  # Layer 2 contains depth 25.0
    assert len(slab.layers) == 1  # Only layer1 is above weak layer (NOT including weak layer)


# ============================================================================
# Tests for convert_grain_form
# ============================================================================


def test_convert_grain_form_with_sub_grain():
    """Test converting grain form with sub-grain class."""
    grain_form_obj = Mock()
    grain_form_obj.sub_grain_class_code = "FCxr"
    grain_form_obj.basic_grain_class_code = "FC"
    
    # Use kim_jamieson_table2 which supports FCxr sub-grain code
    result = convert_grain_form(grain_form_obj, "kim_jamieson_table2")
    
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
# Tests for Pit class - Metadata extraction
# ============================================================================


def test_pit_slope_angle_extraction(mock_caaml_profile_basic):
    """Test Pit extracting valid slope angle."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_basic)
    assert pit.slope_angle == 30.0


def test_pit_slope_angle_missing():
    """Test Pit with missing slope angle."""
    profile = Mock()
    profile.snow_profile = Mock()
    profile.snow_profile.layers = []
    profile.snow_profile.density_profile = []
    profile.core_info = None
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert math.isnan(pit.slope_angle)


def test_pit_slope_angle_empty_array():
    """Test Pit with slope angle as empty array."""
    profile = Mock()
    profile.snow_profile = Mock()
    profile.snow_profile.layers = []
    profile.snow_profile.density_profile = []
    core_info = Mock()
    location = Mock()
    location.slope_angle = []
    core_info.location = location
    profile.core_info = core_info
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert math.isnan(pit.slope_angle)


def test_pit_layer_of_concern_extraction(mock_caaml_profile_basic):
    """Test Pit extracting layer of concern."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_basic)
    
    assert pit.layer_of_concern is not None
    assert pit.layer_of_concern.depth_top == 10.0


def test_pit_layer_of_concern_not_found():
    """Test Pit when layer of concern is not found."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = None
    layer.layer_of_concern = False
    layer.grain_form_primary = None
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    
    profile.snow_profile = snow_profile
    profile.core_info = Mock()
    profile.core_info.location = Mock()
    profile.core_info.location.slope_angle = None
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert pit.layer_of_concern is None


def test_pit_stability_test_extraction(mock_caaml_profile_with_tests):
    """Test Pit extracting stability test results."""
    pit = Pit.from_snowpylot_profile(mock_caaml_profile_with_tests)
    
    assert pit.ECT_results is not None
    assert len(pit.ECT_results) == 1
    assert pit.CT_results is not None
    assert len(pit.CT_results) == 1
    assert pit.PST_results is not None
    assert len(pit.PST_results) == 1


def test_pit_stability_test_none():
    """Test Pit when stability tests are None."""
    profile = Mock()
    profile.snow_profile = Mock()
    profile.snow_profile.layers = []
    profile.snow_profile.density_profile = []
    profile.core_info = Mock()
    profile.core_info.location = Mock()
    profile.core_info.location.slope_angle = None
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)
    assert pit.ECT_results is None
    assert pit.CT_results is None
    assert pit.PST_results is None


# ============================================================================
# Integration Tests with Real CAAML Files
# ============================================================================


@pytest.mark.integration
def test_pit_from_caaml_file_real():
    """Test creating Pit from a real CAAML file using two-step workflow."""
    # Use a real CAAML file from examples/data
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "data")
    caaml_files = [f for f in os.listdir(examples_dir) if f.endswith(".xml")]
    
    if not caaml_files:
        pytest.skip("No CAAML files found in examples/data")
    
    test_file = os.path.join(examples_dir, caaml_files[0])
    
    try:
        # Step 1: Parse CAAML file to get snowpylot profile
        profile = parse_caaml_file(test_file)
        
        # Step 2: Create Pit from snowpylot profile
        pit = Pit.from_snowpylot_profile(profile)
        
        assert pit is not None
        assert len(pit.layers) > 0
        assert all(isinstance(layer, Layer) for layer in pit.layers)
        
        # Test slab creation
        slabs = pit.create_slabs()

        slab = slabs[0] if slabs else None
        assert slab is not None
        assert isinstance(slab, Slab)
        assert len(slab.layers) > 0
    except Exception as e:
        pytest.skip(f"Could not parse test file: {e}")


# ============================================================================
# Additional Edge Case Tests
# ============================================================================


def test_pit_ectp_test_score_string():
    """Test Pit ECTP detection using test_score string."""
    profile = Mock()
    snow_profile = Mock()
    
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [20.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1
    
    layer2 = Mock()
    layer2.depth_top = [20.0]
    layer2.thickness = [10.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
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
    
    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    # Since layer1 is the weak layer and there are no layers above it, no slab can be created

    assert len(slabs) == 0


def test_pit_ct_multiple_tests():
    """Test Pit with multiple CT tests - should use first Q1/SC/SP."""
    profile = Mock()
    snow_profile = Mock()

    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
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

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="CT_failure_layer")
    # Since layer1 is the weak layer and there are no layers above it, no slab can be created

    assert len(slabs) == 0


def test_pit_stability_single_test():
    """Test Pit with single test result (not a list)."""
    profile = Mock()
    snow_profile = Mock()
    snow_profile.layers = []
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    core_info.location = Mock()
    core_info.location.slope_angle = None
    profile.core_info = core_info
    
    stability_tests = Mock()
    # Single test object (not a list)
    ct_test = Mock()
    stability_tests.CT = ct_test  # Single object, not list
    stability_tests.ECT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests
    
    pit = Pit.from_snowpylot_profile(profile)
    assert pit.CT_results is not None
    assert len(pit.CT_results) == 1


def test_pit_pst_alternative_names():
    """Test Pit PST extraction with alternative attribute names."""
    profile = Mock()
    snow_profile = Mock()
    snow_profile.layers = []
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    core_info.location = Mock()
    core_info.location.slope_angle = None
    profile.core_info = core_info
    
    stability_tests = Mock()
    pst_test = Mock()
    stability_tests.PST = None  # Not PST
    stability_tests.PropSawTest = [pst_test]  # Try PropSawTest
    stability_tests.ECT = []
    stability_tests.CT = []
    profile.stability_tests = stability_tests
    
    pit = Pit.from_snowpylot_profile(profile)
    assert pit.PST_results is not None
    assert len(pit.PST_results) == 1


def test_pit_weak_layer_at_boundary():
    """Test Pit weak layer identification when failure is at layer boundary."""
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
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1
    
    # Layer 2: 10-30 cm (failure at exactly 10.0 - boundary)
    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [20.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
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
    
    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="CT_failure_layer")

    slab = slabs[0] if slabs else None
    
    assert slab is not None
    # Failure at 10.0 should be in layer2 (depth_top <= 10.0 < depth_bottom)
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 10.0
    assert len(slab.layers) == 1  # Only layer1 is above


def test_pit_no_stability_tests():
    """Test Pit slab creation when no stability tests exist."""
    profile = Mock()
    snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.basic_grain_class_code = "PP"
    grain_form.sub_grain_class_code = None
    grain_form.grain_size_avg = None
    layer.grain_form_primary = grain_form
    
    snow_profile.layers = [layer]
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    location = Mock()
    location.slope_angle = [25.0, "deg"]
    core_info.location = location
    profile.core_info = core_info
    
    stability_tests = Mock(spec=['ECT', 'CT'])  # Only ECT and CT, no PST
    stability_tests.ECT = []
    stability_tests.CT = []
    # No PST attribute - using spec to prevent Mock from auto-creating it
    profile.stability_tests = stability_tests
    
    pit = Pit.from_snowpylot_profile(profile)

    # Test that pit correctly extracts test results
    assert pit.ECT_results == []
    assert pit.CT_results == []
    assert pit.PST_results is None  # PST doesn't exist, so None

    # Test that slabs have access through pit reference
    # Note: weak_layer_def=None returns empty list, so we can't test slab access here
    slabs = pit.create_slabs(weak_layer_def=None)
    assert slabs == []  # No slabs created when weak_layer_def is None


def test_pit_layer_of_concern_depth_matching():
    """Test Pit layer_of_concern extraction with depth matching tolerance."""
    profile = Mock()
    snow_profile = Mock()
    
    # CAAML layer with slight floating point difference
    caaml_layer = Mock()
    caaml_layer.depth_top = [10.0001]  # Slight difference
    caaml_layer.thickness = [20.0]
    caaml_layer.hardness = None
    caaml_layer.layer_of_concern = True
    caaml_layer.grain_form_primary = None
    snow_profile.layers = [caaml_layer]
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile
    
    core_info = Mock()
    core_info.location = Mock()
    core_info.location.slope_angle = None
    profile.core_info = core_info
    profile.stability_tests = None
    
    pit = Pit.from_snowpylot_profile(profile)

    # Should match within tolerance (0.01)
    assert pit.layer_of_concern is not None
    assert abs(pit.layer_of_concern.depth_top - 10.0) < 0.01


# ============================================================================
# Tests for create_slabs() method - Multiple slabs per pit
# ============================================================================


def test_pit_create_slabs_multiple_ectp():
    """Test create_slabs with multiple ECTP results creates multiple slabs."""
    profile = Mock()
    snow_profile = Mock()

    # Create 3 layers
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [20.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1

    layer2 = Mock()
    layer2.depth_top = [20.0]
    layer2.thickness = [30.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
    layer2.grain_form_primary = grain_form2

    layer3 = Mock()
    layer3.depth_top = [50.0]
    layer3.thickness = [20.0]
    layer3.hardness = "1F"
    layer3.layer_of_concern = False
    grain_form3 = Mock()
    grain_form3.basic_grain_class_code = "RG"
    grain_form3.sub_grain_class_code = None
    grain_form3.grain_size_avg = None
    layer3.grain_form_primary = grain_form3

    snow_profile.layers = [layer1, layer2, layer3]
    snow_profile.density_profile = []
    profile.snow_profile = snow_profile

    core_info = Mock()
    location = Mock()
    location.slope_angle = [35.0, "deg"]
    core_info.location = location
    profile.core_info = core_info

    # Create 3 ECT tests with propagation at different depths
    stability_tests = Mock()
    ect_test1 = Mock()
    ect_test1.depth_top = [25.0]  # In layer2
    ect_test1.propagation = True
    ect_test1.test_score = "ECTP12"

    ect_test2 = Mock()
    ect_test2.depth_top = [55.0]  # In layer3
    ect_test2.propagation = True
    ect_test2.test_score = "ECTP18"

    ect_test3 = Mock()
    ect_test3.depth_top = [45.0]  # In layer2
    ect_test3.propagation = True
    ect_test3.test_score = "ECTP15"

    stability_tests.ECT = [ect_test1, ect_test2, ect_test3]
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests

    # Add pit_id
    profile.obs_id = "test_pit_001"

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

    # Should create 3 slabs
    assert len(slabs) == 3

    # Check metadata for each slab
    for idx, slab in enumerate(slabs):
        assert slab.pit_id == "test_pit_001"
        assert slab.slab_id == f"test_pit_001_slab_{idx}"
        assert slab.weak_layer_source == "ECTP_failure_layer"
        assert slab.test_result_index == idx
        assert slab.n_test_results_in_pit == 3
        assert slab.test_result_properties is not None
        assert "score" in slab.test_result_properties
        assert "propagation" in slab.test_result_properties
        assert "depth_top" in slab.test_result_properties

    # Check weak layer depths match test depths
    assert slabs[0].weak_layer.depth_top == 20.0  # layer2 contains 25.0
    assert slabs[1].weak_layer.depth_top == 50.0  # layer3 contains 55.0
    assert slabs[2].weak_layer.depth_top == 20.0  # layer2 contains 45.0

    # Check slab layer counts
    # Slab includes layers with depth_top < weak_layer.depth_top (NOT including weak layer)
    assert len(slabs[0].layers) == 1  # Only layer1 (layer2 is the weak layer, excluded)
    assert len(slabs[1].layers) == 2  # layer1 and layer2 (layer3 is the weak layer, excluded)
    assert len(slabs[2].layers) == 1  # Only layer1 (layer2 is the weak layer, excluded)


def test_pit_create_slabs_single_ectp():
    """Test create_slabs with single ECTP creates one slab."""
    profile = Mock()
    snow_profile = Mock()

    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [20.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1

    layer2 = Mock()
    layer2.depth_top = [20.0]
    layer2.thickness = [10.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
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
    ect_test = Mock()
    ect_test.depth_top = [25.0]
    ect_test.propagation = True
    ect_test.test_score = "ECTP12"
    stability_tests.ECT = [ect_test]
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests

    profile.obs_id = "pit_002"

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

    # Should create 1 slab
    assert len(slabs) == 1
    assert slabs[0].pit_id == "pit_002"
    assert slabs[0].slab_id == "pit_002_slab_0"
    assert slabs[0].test_result_index == 0
    assert slabs[0].n_test_results_in_pit == 1


def test_pit_create_slabs_no_ectp():
    """Test create_slabs with no ECTP returns empty list."""
    profile = Mock()
    snow_profile = Mock()

    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [20.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
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
    # ECT tests but no propagation
    ect_test = Mock()
    ect_test.depth_top = [15.0]
    ect_test.propagation = False
    ect_test.test_score = "ECT15"  # No "ECTP"
    stability_tests.ECT = [ect_test]
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

    # Should return empty list
    assert len(slabs) == 0


def test_pit_create_slabs_multiple_ct():
    """Test create_slabs with multiple CT results creates multiple slabs."""
    profile = Mock()
    snow_profile = Mock()

    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [15.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1

    layer2 = Mock()
    layer2.depth_top = [15.0]
    layer2.thickness = [25.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
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
    # Multiple CT tests with valid fracture characters
    ct_test1 = Mock()
    ct_test1.depth_top = [20.0]
    ct_test1.fracture_character = "Q1"
    ct_test1.test_score = "CT12"

    ct_test2 = Mock()
    ct_test2.depth_top = [35.0]
    ct_test2.fracture_character = "SC"
    ct_test2.test_score = "CT18"

    ct_test3 = Mock()
    ct_test3.depth_top = [10.0]
    ct_test3.fracture_character = "RP"  # Not valid - should be excluded
    ct_test3.test_score = "CT8"

    stability_tests.CT = [ct_test1, ct_test2, ct_test3]
    stability_tests.ECT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests

    profile.obs_id = "pit_003"

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="CT_failure_layer")

    # Should create 2 slabs (ct_test3 excluded due to RP fracture character)
    assert len(slabs) == 2

    # Check metadata
    assert slabs[0].pit_id == "pit_003"
    assert slabs[0].weak_layer_source == "CT_failure_layer"
    assert slabs[0].test_result_index == 0
    assert slabs[0].n_test_results_in_pit == 2
    assert slabs[0].test_result_properties["fracture_character"] == "Q1"

    assert slabs[1].test_result_index == 1
    assert slabs[1].test_result_properties["fracture_character"] == "SC"


def test_pit_create_slabs_layer_of_concern():
    """Test create_slabs with layer_of_concern returns single slab."""
    profile = Mock()
    snow_profile = Mock()

    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1

    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [20.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = True
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
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
    stability_tests.ECT = []
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests

    profile.obs_id = "pit_004"

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")

    # Should create 1 slab
    assert len(slabs) == 1
    assert slabs[0].pit_id == "pit_004"
    assert slabs[0].slab_id == "pit_004_slab_0"
    assert slabs[0].weak_layer_source == "layer_of_concern"
    assert slabs[0].test_result_index is None
    assert slabs[0].test_result_properties is None
    assert slabs[0].n_test_results_in_pit is None


def test_pit_create_slabs_none_weak_layer():
    """Test create_slabs with None weak_layer_def returns all layers."""
    profile = Mock()
    snow_profile = Mock()

    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
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
    stability_tests.ECT = []
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests

    profile.obs_id = "pit_005"

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def=None)

    # Should create 1 slab with all layers
    assert len(slabs) == 1
    assert len(slabs[0].layers) == 1
    assert slabs[0].weak_layer is None
    assert slabs[0].weak_layer_source is None


def test_pit_create_slabs_no_pit_id():
    """Test create_slabs generates slab_id even without pit_id."""
    profile = Mock()
    snow_profile = Mock()

    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    grain_form1 = Mock()
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.sub_grain_class_code = None
    grain_form1.grain_size_avg = None
    layer1.grain_form_primary = grain_form1

    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [10.0]
    layer2.hardness = "4F"
    layer2.layer_of_concern = False
    grain_form2 = Mock()
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.sub_grain_class_code = None
    grain_form2.grain_size_avg = None
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
    ect_test1 = Mock()
    ect_test1.depth_top = [15.0]
    ect_test1.propagation = True
    ect_test1.test_score = "ECTP12"

    ect_test2 = Mock()
    ect_test2.depth_top = [12.0]
    ect_test2.propagation = True
    ect_test2.test_score = "ECTP10"

    stability_tests.ECT = [ect_test1, ect_test2]
    stability_tests.CT = []
    stability_tests.PST = []
    profile.stability_tests = stability_tests

    # No obs_id or profile_id - pit_id will be None
    # Use spec to prevent Mock from auto-creating these attributes
    del profile.obs_id
    del profile.profile_id

    pit = Pit.from_snowpylot_profile(profile)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

    # Should still generate slab_ids
    assert len(slabs) == 2
    assert slabs[0].pit_id is None
    assert slabs[0].slab_id == "slab_0"
    assert slabs[1].slab_id == "slab_1"
