"""
Comprehensive tests for Pit, Layer, and Slab creation from SnowPilot data.

Tests cover:
- Parsing CAAML files with parse_caaml_file
- Creating Pit objects from snowpylot SnowPit objects
- Layer extraction and property mapping
- Slab creation with different weak layer definitions:
  - layer_of_concern
  - CT_failure_layer  
  - ECTP_failure_layer
  - None case
- Edge cases and error handling
"""

import os
import math
from pathlib import Path
from typing import Any, List
from unittest.mock import Mock

import pytest

from snowpyt_mechparams.data_structures import Layer, Pit, Slab
from snowpyt_mechparams.snowpilot import parse_caaml_file


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def examples_data_dir():
    """Path to examples/data directory with real CAAML files."""
    # Get project root (assuming tests/ is at project root)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "examples" / "data"
    
    if not data_dir.exists():
        pytest.skip(f"Examples data directory not found: {data_dir}")
    
    return data_dir


@pytest.fixture
def sample_caaml_file(examples_data_dir):
    """Get a sample CAAML file for testing."""
    # Find any CAAML file in the directory
    caaml_files = list(examples_data_dir.glob("snowpits-*.xml"))
    
    if not caaml_files:
        pytest.skip("No CAAML files found in examples/data")
    
    return caaml_files[0]


@pytest.fixture
def mock_snowpylot_layer_simple():
    """Create a simple mock snowpylot layer."""
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
def mock_snowpylot_profile_with_layers():
    """Create a mock snowpylot SnowPit with multiple layers."""
    snow_pit = Mock()
    
    # Mock snow_profile
    snow_profile = Mock()
    
    # Create layer 1 (surface)
    layer1 = Mock()
    layer1.depth_top = [0.0]
    layer1.thickness = [10.0]
    layer1.hardness = "F"
    layer1.layer_of_concern = False
    
    grain_form1 = Mock()
    grain_form1.sub_grain_class_code = "PPgp"
    grain_form1.basic_grain_class_code = "PP"
    grain_form1.grain_size_avg = 0.5
    layer1.grain_form_primary = grain_form1
    
    # Create layer 2 (weak layer)
    layer2 = Mock()
    layer2.depth_top = [10.0]
    layer2.thickness = [5.0]
    layer2.hardness = "F-"
    layer2.layer_of_concern = True
    
    grain_form2 = Mock()
    grain_form2.sub_grain_class_code = "FCxr"
    grain_form2.basic_grain_class_code = "FC"
    grain_form2.grain_size_avg = 1.5
    layer2.grain_form_primary = grain_form2
    
    # Create layer 3 (below weak layer)
    layer3 = Mock()
    layer3.depth_top = [15.0]
    layer3.thickness = [20.0]
    layer3.hardness = "4F"
    layer3.layer_of_concern = False
    
    grain_form3 = Mock()
    grain_form3.sub_grain_class_code = None
    grain_form3.basic_grain_class_code = "RG"
    grain_form3.grain_size_avg = 1.0
    layer3.grain_form_primary = grain_form3
    
    snow_profile.layers = [layer1, layer2, layer3]
    snow_profile.density_profile = []
    
    snow_pit.snow_profile = snow_profile
    
    # Mock core_info with slope angle and pit ID
    core_info = Mock()
    core_info.pit_id = "test_pit_123"
    location = Mock()
    location.slope_angle = [35.0, "deg"]
    core_info.location = location
    snow_pit.core_info = core_info
    
    # Mock stability_tests (empty)
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = []
    stability_tests.PST = []
    snow_pit.stability_tests = stability_tests
    
    return snow_pit


@pytest.fixture
def mock_snowpylot_profile_with_ectp():
    """Create a mock snowpylot SnowPit with ECTP test results."""
    snow_pit = Mock()
    
    # Mock snow_profile with layers
    snow_profile = Mock()
    
    # Create layers
    layers = []
    for i in range(4):
        layer = Mock()
        layer.depth_top = [i * 10.0]
        layer.thickness = [10.0]
        layer.hardness = "4F" if i > 1 else "F"
        layer.layer_of_concern = False
        
        grain_form = Mock()
        grain_form.sub_grain_class_code = None
        grain_form.basic_grain_class_code = "RG"
        grain_form.grain_size_avg = 1.0
        layer.grain_form_primary = grain_form
        
        layers.append(layer)
    
    snow_profile.layers = layers
    snow_profile.density_profile = []
    snow_pit.snow_profile = snow_profile
    
    # Mock core_info
    core_info = Mock()
    core_info.pit_id = "test_pit_ectp"
    location = Mock()
    location.slope_angle = [38.0, "deg"]
    core_info.location = location
    snow_pit.core_info = core_info
    
    # Mock ECTP test result
    ect_result = Mock()
    ect_result.depth_top = 20.0  # Failure at 20cm (in layer 2)
    ect_result.fracture_character = "RP"  # Propagation
    ect_result.score = "ECTP15"
    
    stability_tests = Mock()
    stability_tests.ECT = [ect_result]
    stability_tests.CT = []
    stability_tests.PST = []
    snow_pit.stability_tests = stability_tests
    
    return snow_pit


@pytest.fixture
def mock_snowpylot_profile_with_ct():
    """Create a mock snowpylot SnowPit with CT test results."""
    snow_pit = Mock()
    
    # Mock snow_profile with layers
    snow_profile = Mock()
    
    # Create layers
    layers = []
    for i in range(3):
        layer = Mock()
        layer.depth_top = [i * 15.0]
        layer.thickness = [15.0]
        layer.hardness = "1F"
        layer.layer_of_concern = False
        
        grain_form = Mock()
        grain_form.sub_grain_class_code = None
        grain_form.basic_grain_class_code = "FC"
        grain_form.grain_size_avg = 1.2
        layer.grain_form_primary = grain_form
        
        layers.append(layer)
    
    snow_profile.layers = layers
    snow_profile.density_profile = []
    snow_pit.snow_profile = snow_profile
    
    # Mock core_info
    core_info = Mock()
    core_info.pit_id = "test_pit_ct"
    location = Mock()
    location.slope_angle = [40.0, "deg"]
    core_info.location = location
    snow_pit.core_info = core_info
    
    # Mock CT test result with sudden collapse
    ct_result = Mock()
    ct_result.depth_top = 15.0  # Failure at 15cm
    ct_result.fracture_character = "SC"  # Sudden collapse
    ct_result.score = "CT10"
    
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = [ct_result]
    stability_tests.PST = []
    snow_pit.stability_tests = stability_tests
    
    return snow_pit


# ============================================================================
# Test CAAML Parsing
# ============================================================================


def test_parse_caaml_file_returns_snowpylot_object(sample_caaml_file):
    """Test that parse_caaml_file returns a snowpylot SnowPit object."""
    snow_pit = parse_caaml_file(str(sample_caaml_file))
    
    assert snow_pit is not None
    assert hasattr(snow_pit, "snow_profile")
    assert hasattr(snow_pit, "core_info")


def test_parse_caaml_file_with_nonexistent_file():
    """Test that parse_caaml_file raises an error for nonexistent files."""
    with pytest.raises(Exception):
        parse_caaml_file("nonexistent_file.xml")


# ============================================================================
# Test Pit Creation
# ============================================================================


def test_pit_from_snow_pit_basic(mock_snowpylot_profile_with_layers):
    """Test creating a Pit from a snowpylot SnowPit."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_layers)
    
    assert pit is not None
    assert isinstance(pit, Pit)
    assert pit.pit_id == "test_pit_123"
    assert pit.slope_angle.nominal_value == 35.0
    assert pit.slope_angle.std_dev == 2.0
    assert len(pit.layers) == 3


def test_pit_from_snow_pit_extracts_layers(mock_snowpylot_profile_with_layers):
    """Test that Pit correctly extracts Layer objects from snow profile."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_layers)
    
    # Check we have layers
    assert len(pit.layers) == 3
    
    # Check first layer
    layer1 = pit.layers[0]
    assert isinstance(layer1, Layer)
    assert layer1.depth_top == 0.0
    assert layer1.thickness.nominal_value == 10.0
    assert layer1.thickness.std_dev == pytest.approx(0.5)
    assert layer1.hand_hardness == "F"
    assert layer1.grain_form == "PPgp"  # Sub grain class (preferred when available)
    assert layer1.layer_of_concern is False
    
    # Check second layer (weak layer)
    layer2 = pit.layers[1]
    assert layer2.depth_top == 10.0
    assert layer2.thickness.nominal_value == 5.0
    assert layer2.thickness.std_dev == pytest.approx(0.25)
    assert layer2.hand_hardness == "F-"
    assert layer2.grain_form == "FCxr"  # Sub grain class (preferred when available)
    assert layer2.layer_of_concern is True

    # Check third layer
    layer3 = pit.layers[2]
    assert layer3.depth_top == 15.0
    assert layer3.thickness.nominal_value == 20.0
    assert layer3.thickness.std_dev == pytest.approx(1.0)


def test_pit_from_snow_pit_handles_missing_slope_angle():
    """Test that Pit handles missing slope angle gracefully."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    snow_pit.snow_profile.layers = []
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "test"
    snow_pit.core_info.location = Mock()
    snow_pit.core_info.location.slope_angle = None  # No slope angle
    snow_pit.stability_tests = None
    
    pit = Pit.from_snow_pit(snow_pit)
    
    assert math.isnan(pit.slope_angle)


def test_pit_from_snow_pit_handles_missing_pit_id():
    """Test that Pit handles missing pit ID gracefully."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    snow_pit.snow_profile.layers = []
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = None  # No core info
    snow_pit.stability_tests = None
    
    pit = Pit.from_snow_pit(snow_pit)
    
    assert pit.pit_id is None


def test_pit_layer_of_concern_property(mock_snowpylot_profile_with_layers):
    """Test that Pit.layer_of_concern returns the correct layer."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_layers)
    
    loc = pit.layer_of_concern
    
    assert loc is not None
    assert isinstance(loc, Layer)
    assert loc.layer_of_concern is True
    assert loc.depth_top == 10.0


def test_pit_layer_of_concern_none_when_absent():
    """Test that Pit.layer_of_concern returns None when no layer is marked."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    
    # Create layer without layer_of_concern
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.sub_grain_class_code = None
    grain_form.basic_grain_class_code = "RG"
    grain_form.grain_size_avg = 1.0
    layer.grain_form_primary = grain_form
    
    snow_pit.snow_profile.layers = [layer]
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "test"
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    snow_pit.core_info.location = location
    snow_pit.stability_tests = None
    
    pit = Pit.from_snow_pit(snow_pit)
    
    assert pit.layer_of_concern is None


# ============================================================================
# Test Slab Creation - layer_of_concern
# ============================================================================


def test_create_slabs_with_layer_of_concern(mock_snowpylot_profile_with_layers):
    """Test creating a slab using layer_of_concern weak layer definition."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_layers)
    
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")
    
    assert len(slabs) == 1
    slab = slabs[0]
    
    # Check slab properties
    assert isinstance(slab, Slab)
    assert slab.angle.nominal_value == 35.0
    assert slab.angle.std_dev == 2.0
    assert slab.pit_id == "test_pit_123"
    assert slab.slab_id == "test_pit_123_slab_0"
    assert slab.weak_layer_source == "layer_of_concern"
    
    # Check weak layer
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 10.0
    assert slab.weak_layer.layer_of_concern is True
    
    # Check slab layers (should only include layers ABOVE weak layer)
    assert len(slab.layers) == 1
    assert slab.layers[0].depth_top == 0.0
    assert slab.layers[0].thickness.nominal_value == 10.0
    assert slab.layers[0].thickness.std_dev == pytest.approx(0.5)


def test_create_slabs_layer_of_concern_returns_empty_when_absent():
    """Test that create_slabs returns empty list when no layer_of_concern exists."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    
    # Create layer without layer_of_concern
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.sub_grain_class_code = None
    grain_form.basic_grain_class_code = "RG"
    grain_form.grain_size_avg = 1.0
    layer.grain_form_primary = grain_form
    
    snow_pit.snow_profile.layers = [layer]
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "test"
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    snow_pit.core_info.location = location
    snow_pit.stability_tests = None
    
    pit = Pit.from_snow_pit(snow_pit)
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")
    
    assert len(slabs) == 0


# ============================================================================
# Test Slab Creation - ECTP_failure_layer
# ============================================================================


def test_create_slabs_with_ectp_failure_layer(mock_snowpylot_profile_with_ectp):
    """Test creating slabs using ECTP test results."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_ectp)
    
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    
    assert len(slabs) == 1
    slab = slabs[0]
    
    # Check slab properties
    assert isinstance(slab, Slab)
    assert slab.angle.nominal_value == 38.0
    assert slab.angle.std_dev == 2.0
    assert slab.pit_id == "test_pit_ectp"
    assert slab.slab_id == "test_pit_ectp_slab_0"
    assert slab.weak_layer_source == "ECTP_failure_layer"
    assert slab.test_result_index == 0
    
    # Check weak layer (should be layer at 20cm depth)
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 20.0
    
    # Check slab layers (should include layers above 20cm)
    assert len(slab.layers) == 2  # Layers at 0cm and 10cm
    assert all(layer.depth_top < 20.0 for layer in slab.layers)


def test_create_slabs_ectp_returns_empty_when_no_propagation():
    """Test that ECTP weak layer def returns empty list when no propagation tests."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.sub_grain_class_code = None
    grain_form.basic_grain_class_code = "RG"
    grain_form.grain_size_avg = 1.0
    layer.grain_form_primary = grain_form
    
    snow_pit.snow_profile.layers = [layer]
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "test"
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    snow_pit.core_info.location = location
    
    # ECT test without propagation
    ect_result = Mock()
    ect_result.depth_top = 5.0
    ect_result.fracture_character = "RB"  # No propagation
    ect_result.score = "ECT15"
    
    stability_tests = Mock()
    stability_tests.ECT = [ect_result]
    stability_tests.CT = []
    stability_tests.PST = []
    snow_pit.stability_tests = stability_tests
    
    pit = Pit.from_snow_pit(snow_pit)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    
    assert len(slabs) == 0


# ============================================================================
# Test Slab Creation - CT_failure_layer
# ============================================================================


def test_create_slabs_with_ct_failure_layer(mock_snowpylot_profile_with_ct):
    """Test creating slabs using CT test results."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_ct)
    
    slabs = pit.create_slabs(weak_layer_def="CT_failure_layer")
    
    assert len(slabs) == 1
    slab = slabs[0]
    
    # Check slab properties
    assert isinstance(slab, Slab)
    assert slab.angle.nominal_value == 40.0
    assert slab.angle.std_dev == 2.0
    assert slab.pit_id == "test_pit_ct"
    assert slab.weak_layer_source == "CT_failure_layer"
    
    # Check weak layer (should be layer at 15cm depth)
    assert slab.weak_layer is not None
    assert slab.weak_layer.depth_top == 15.0
    
    # Check slab layers (should include layer above 15cm)
    assert len(slab.layers) == 1
    assert slab.layers[0].depth_top == 0.0


def test_create_slabs_ct_returns_empty_when_no_valid_ct():
    """Test that CT weak layer def returns empty list when no valid CT tests."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    grain_form = Mock()
    grain_form.sub_grain_class_code = None
    grain_form.basic_grain_class_code = "RG"
    grain_form.grain_size_avg = 1.0
    layer.grain_form_primary = grain_form
    
    snow_pit.snow_profile.layers = [layer]
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "test"
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    snow_pit.core_info.location = location
    
    # CT test with invalid fracture character
    ct_result = Mock()
    ct_result.depth_top = 5.0
    ct_result.fracture_character = "RB"  # Not Q1, SC, or SP
    ct_result.score = "CT10"
    
    stability_tests = Mock()
    stability_tests.ECT = []
    stability_tests.CT = [ct_result]
    stability_tests.PST = []
    snow_pit.stability_tests = stability_tests
    
    pit = Pit.from_snow_pit(snow_pit)
    slabs = pit.create_slabs(weak_layer_def="CT_failure_layer")
    
    assert len(slabs) == 0


# ============================================================================
# Test Slab Creation - None case
# ============================================================================


def test_create_slabs_with_none_returns_empty_list(mock_snowpylot_profile_with_layers):
    """Test that create_slabs returns empty list when weak_layer_def is None."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_layers)
    
    slabs = pit.create_slabs(weak_layer_def=None)
    
    assert len(slabs) == 0


# ============================================================================
# Test Slab Creation - Invalid weak_layer_def
# ============================================================================


def test_create_slabs_raises_error_for_invalid_weak_layer_def(mock_snowpylot_profile_with_layers):
    """Test that create_slabs raises ValueError for invalid weak_layer_def."""
    pit = Pit.from_snow_pit(mock_snowpylot_profile_with_layers)
    
    with pytest.raises(ValueError, match="Invalid weak_layer_def"):
        pit.create_slabs(weak_layer_def="invalid_definition")


# ============================================================================
# Test Edge Cases
# ============================================================================


def test_pit_with_no_layers():
    """Test that Pit handles snow profiles with no layers."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    snow_pit.snow_profile.layers = []
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "empty"
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    snow_pit.core_info.location = location
    snow_pit.stability_tests = None
    
    pit = Pit.from_snow_pit(snow_pit)
    
    assert len(pit.layers) == 0
    
    # create_slabs should return empty list
    slabs = pit.create_slabs(weak_layer_def="layer_of_concern")
    assert len(slabs) == 0


def test_layer_with_sub_grain_class_takes_precedence():
    """Test that sub_grain_class_code is used when available."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    
    grain_form = Mock()
    grain_form.sub_grain_class_code = "PPgp"  # Sub grain class available
    grain_form.basic_grain_class_code = "PP"
    grain_form.grain_size_avg = 0.5
    layer.grain_form_primary = grain_form
    
    snow_pit.snow_profile.layers = [layer]
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "test"
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    snow_pit.core_info.location = location
    snow_pit.stability_tests = None
    
    pit = Pit.from_snow_pit(snow_pit)
    
    # Should use sub_grain_class_code
    assert pit.layers[0].grain_form == "PPgp"


def test_layer_with_only_basic_grain_class():
    """Test that basic_grain_class_code is used when sub_grain_class is None."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    
    layer = Mock()
    layer.depth_top = [0.0]
    layer.thickness = [10.0]
    layer.hardness = "F"
    layer.layer_of_concern = False
    
    grain_form = Mock()
    grain_form.sub_grain_class_code = None  # No sub grain class
    grain_form.basic_grain_class_code = "RG"
    grain_form.grain_size_avg = 1.0
    layer.grain_form_primary = grain_form
    
    snow_pit.snow_profile.layers = [layer]
    snow_pit.snow_profile.density_profile = []
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "test"
    location = Mock()
    location.slope_angle = [30.0, "deg"]
    snow_pit.core_info.location = location
    snow_pit.stability_tests = None
    
    pit = Pit.from_snow_pit(snow_pit)
    
    # Should use basic_grain_class_code
    assert pit.layers[0].grain_form == "RG"


# ============================================================================
# Integration Test with Real CAAML File
# ============================================================================


def test_full_workflow_with_real_caaml_file(sample_caaml_file):
    """Test the complete workflow from CAAML file to Slab creation."""
    # Step 1: Parse CAAML file
    snow_pit = parse_caaml_file(str(sample_caaml_file))
    assert snow_pit is not None
    
    # Step 2: Create Pit
    pit = Pit.from_snow_pit(snow_pit)
    assert pit is not None
    assert isinstance(pit, Pit)
    
    # Step 3: Verify layers were created
    assert len(pit.layers) > 0
    assert all(isinstance(layer, Layer) for layer in pit.layers)
    
    # Step 4: Try to create slabs (may or may not succeed depending on the file)
    # Just verify no errors are raised
    slabs_loc = pit.create_slabs(weak_layer_def="layer_of_concern")
    slabs_ectp = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    slabs_ct = pit.create_slabs(weak_layer_def="CT_failure_layer")
    
    # Verify they're all lists
    assert isinstance(slabs_loc, list)
    assert isinstance(slabs_ectp, list)
    assert isinstance(slabs_ct, list)
    
    # If any slabs were created, verify they're valid
    for slab in slabs_loc + slabs_ectp + slabs_ct:
        assert isinstance(slab, Slab)
        assert len(slab.layers) > 0
        assert slab.weak_layer is not None


# ============================================================================
# Test Multiple ECTP/CT Results
# ============================================================================


def test_create_slabs_with_multiple_ectp_results():
    """Test that multiple ECTP results create multiple slabs."""
    snow_pit = Mock()
    snow_pit.snow_profile = Mock()
    
    # Create layers
    layers = []
    for i in range(5):
        layer = Mock()
        layer.depth_top = [i * 10.0]
        layer.thickness = [10.0]
        layer.hardness = "F"
        layer.layer_of_concern = False
        grain_form = Mock()
        grain_form.sub_grain_class_code = None
        grain_form.basic_grain_class_code = "RG"
        grain_form.grain_size_avg = 1.0
        layer.grain_form_primary = grain_form
        layers.append(layer)
    
    snow_pit.snow_profile.layers = layers
    snow_pit.snow_profile.density_profile = []
    
    snow_pit.core_info = Mock()
    snow_pit.core_info.pit_id = "multi_ectp"
    location = Mock()
    location.slope_angle = [35.0, "deg"]
    snow_pit.core_info.location = location
    
    # Create two ECTP results
    ect1 = Mock()
    ect1.depth_top = 15.0
    ect1.fracture_character = "RP"
    ect1.score = "ECTP12"
    
    ect2 = Mock()
    ect2.depth_top = 35.0
    ect2.fracture_character = "RP"
    ect2.score = "ECTP18"
    
    stability_tests = Mock()
    stability_tests.ECT = [ect1, ect2]
    stability_tests.CT = []
    stability_tests.PST = []
    snow_pit.stability_tests = stability_tests
    
    pit = Pit.from_snow_pit(snow_pit)
    slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
    
    # Should create 2 slabs, one for each ECTP result
    assert len(slabs) == 2
    
    # Check first slab
    # ECTP failure at 15.0cm falls in layer at depth_top=10.0 (range 10-20)
    assert slabs[0].weak_layer.depth_top == 10.0
    assert slabs[0].test_result_index == 0
    assert slabs[0].slab_id == "multi_ectp_slab_0"
    
    # Check second slab
    # ECTP failure at 35.0cm falls in layer at depth_top=30.0 (range 30-40)
    assert slabs[1].weak_layer.depth_top == 30.0
    assert slabs[1].test_result_index == 1
    assert slabs[1].slab_id == "multi_ectp_slab_1"
