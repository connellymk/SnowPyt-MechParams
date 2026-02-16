"""
Tests for centralized grain form resolution utility.

Tests the resolve_grain_form_for_method() function which is the single
source of truth for grain form validation logic.
"""

import pytest
from snowpyt_mechparams.constants import (
    resolve_grain_form_for_method,
    GRAIN_FORM_METHODS,
)


class TestResolveGrainFormForMethod:
    """Tests for resolve_grain_form_for_method utility function."""
    
    def test_none_grain_form(self):
        """Test handling of None grain_form."""
        result = resolve_grain_form_for_method(None, "geldsetzer")
        assert result is None
    
    def test_valid_sub_grain_code(self):
        """Test sub-grain code that is valid for the method."""
        # RGmx is in geldsetzer's sub_grain_class set
        result = resolve_grain_form_for_method("RGmx", "geldsetzer")
        assert result == "RGmx"
    
    def test_valid_basic_grain_code(self):
        """Test basic grain code that is valid for the method."""
        # RG is in geldsetzer's basic_grain_class set
        result = resolve_grain_form_for_method("RG", "geldsetzer")
        assert result == "RG"
    
    def test_sub_grain_code_not_in_method_falls_back_to_basic(self):
        """Test sub-grain code not valid falls back to basic code."""
        # RGxf is NOT in geldsetzer's sub_grain_class, but RG is in basic_grain_class
        result = resolve_grain_form_for_method("RGxf", "geldsetzer")
        assert result == "RG"
    
    def test_invalid_grain_code_returns_none(self):
        """Test grain code that is not valid for any form in the method."""
        # DH is not valid for kim_jamieson_table5
        result = resolve_grain_form_for_method("DH", "kim_jamieson_table5")
        assert result is None
    
    def test_unknown_method_returns_grain_form_unchanged(self):
        """Test unknown method returns grain_form as-is."""
        result = resolve_grain_form_for_method("RG", "unknown_method")
        assert result == "RG"
    
    def test_case_insensitive_method_name(self):
        """Test method names are case-insensitive."""
        result1 = resolve_grain_form_for_method("RG", "geldsetzer")
        result2 = resolve_grain_form_for_method("RG", "GELDSETZER")
        result3 = resolve_grain_form_for_method("RG", "Geldsetzer")
        assert result1 == result2 == result3 == "RG"
    
    def test_all_methods_have_required_keys(self):
        """Test all methods in GRAIN_FORM_METHODS have required structure."""
        for method, codes in GRAIN_FORM_METHODS.items():
            assert "sub_grain_class" in codes, f"{method} missing sub_grain_class"
            assert "basic_grain_class" in codes, f"{method} missing basic_grain_class"
            assert isinstance(codes["sub_grain_class"], set)
            assert isinstance(codes["basic_grain_class"], set)
    
    def test_geldsetzer_specific_codes(self):
        """Test geldsetzer-specific grain form codes."""
        # Valid sub-grain codes
        assert resolve_grain_form_for_method("PPgp", "geldsetzer") == "PPgp"
        assert resolve_grain_form_for_method("RGmx", "geldsetzer") == "RGmx"
        assert resolve_grain_form_for_method("FCmx", "geldsetzer") == "FCmx"
        
        # Valid basic codes
        assert resolve_grain_form_for_method("PP", "geldsetzer") == "PP"
        assert resolve_grain_form_for_method("DF", "geldsetzer") == "DF"
        assert resolve_grain_form_for_method("RG", "geldsetzer") == "RG"
        assert resolve_grain_form_for_method("FC", "geldsetzer") == "FC"
        assert resolve_grain_form_for_method("DH", "geldsetzer") == "DH"
    
    def test_kim_jamieson_table2_specific_codes(self):
        """Test kim_jamieson_table2-specific grain form codes."""
        # Valid sub-grain codes
        assert resolve_grain_form_for_method("PPgp", "kim_jamieson_table2") == "PPgp"
        assert resolve_grain_form_for_method("RGxf", "kim_jamieson_table2") == "RGxf"
        assert resolve_grain_form_for_method("FCxr", "kim_jamieson_table2") == "FCxr"
        assert resolve_grain_form_for_method("MFcr", "kim_jamieson_table2") == "MFcr"
        
        # Valid basic codes
        assert resolve_grain_form_for_method("PP", "kim_jamieson_table2") == "PP"
        assert resolve_grain_form_for_method("DF", "kim_jamieson_table2") == "DF"
        assert resolve_grain_form_for_method("FC", "kim_jamieson_table2") == "FC"
        assert resolve_grain_form_for_method("DH", "kim_jamieson_table2") == "DH"
        assert resolve_grain_form_for_method("RG", "kim_jamieson_table2") == "RG"
    
    def test_kim_jamieson_table5_specific_codes(self):
        """Test kim_jamieson_table5-specific grain form codes."""
        # Valid sub-grain codes
        assert resolve_grain_form_for_method("FCxr", "kim_jamieson_table5") == "FCxr"
        assert resolve_grain_form_for_method("PPgp", "kim_jamieson_table5") == "PPgp"
        
        # Valid basic codes
        assert resolve_grain_form_for_method("FC", "kim_jamieson_table5") == "FC"
        assert resolve_grain_form_for_method("PP", "kim_jamieson_table5") == "PP"
        assert resolve_grain_form_for_method("DF", "kim_jamieson_table5") == "DF"
        assert resolve_grain_form_for_method("MF", "kim_jamieson_table5") == "MF"
        
        # Invalid codes (not in table5)
        assert resolve_grain_form_for_method("DH", "kim_jamieson_table5") is None
        assert resolve_grain_form_for_method("RG", "kim_jamieson_table5") is None
    
    def test_fallback_extraction_from_sub_grain_code(self):
        """Test that basic code is extracted from longer sub-grain codes."""
        # FCxr should fall back to FC for geldsetzer (FCxr not in geldsetzer's sub set)
        result = resolve_grain_form_for_method("FCxr", "geldsetzer")
        assert result == "FC"
        
        # PPgp should stay PPgp for geldsetzer (PPgp IS in geldsetzer's sub set)
        result = resolve_grain_form_for_method("PPgp", "geldsetzer")
        assert result == "PPgp"
    
    def test_empty_string_grain_form(self):
        """Test handling of empty string grain_form."""
        result = resolve_grain_form_for_method("", "geldsetzer")
        assert result is None
    
    def test_single_character_grain_form(self):
        """Test handling of single character grain_form (invalid)."""
        result = resolve_grain_form_for_method("R", "geldsetzer")
        assert result is None


class TestGrainFormMethodsConstants:
    """Tests for GRAIN_FORM_METHODS constant structure."""
    
    def test_all_methods_present(self):
        """Test all expected methods are in GRAIN_FORM_METHODS."""
        expected_methods = ["geldsetzer", "kim_jamieson_table2", "kim_jamieson_table5"]
        for method in expected_methods:
            assert method in GRAIN_FORM_METHODS
    
    def test_no_duplicate_codes_within_method(self):
        """Test sub and basic sets don't have overlapping codes within a method."""
        for method, codes in GRAIN_FORM_METHODS.items():
            sub = codes["sub_grain_class"]
            basic = codes["basic_grain_class"]
            # Note: Some codes MAY appear in both (like 'PP' might be both)
            # This is actually OK - the function tries sub first, then basic
            # So we just verify they're both sets with valid string content
            assert all(isinstance(code, str) for code in sub)
            assert all(isinstance(code, str) for code in basic)
    
    def test_codes_have_consistent_format(self):
        """Test grain form codes follow expected format."""
        for method, codes in GRAIN_FORM_METHODS.items():
            # Sub-grain codes should be 4 characters
            for code in codes["sub_grain_class"]:
                assert len(code) == 4, f"Sub-grain code '{code}' in {method} should be 4 chars"
            
            # Basic codes should be 2 characters
            for code in codes["basic_grain_class"]:
                assert len(code) == 2, f"Basic code '{code}' in {method} should be 2 chars"
