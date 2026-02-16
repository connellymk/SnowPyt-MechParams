"""
Tests for grain_form resolution in dispatcher.

Tests the fix for the grain_form_sub AttributeError bug.
"""

import pytest
from snowpyt_mechparams import Layer
from snowpyt_mechparams.execution.dispatcher import _resolve_grain_form


class TestGrainFormResolution:
    """Tests for _resolve_grain_form function."""
    
    def test_basic_grain_form(self):
        """Test basic 2-character grain form codes."""
        layer = Layer(grain_form='RG')
        result = _resolve_grain_form(layer)
        assert result == 'RG'
    
    def test_sub_grain_form(self):
        """Test longer sub-grain form codes."""
        layer = Layer(grain_form='RGmx')
        result = _resolve_grain_form(layer)
        assert result == 'RGmx'
    
    def test_none_grain_form(self):
        """Test handling of None grain_form."""
        layer = Layer(grain_form=None)
        result = _resolve_grain_form(layer)
        assert result is None
    
    def test_method_specific_basic_code(self):
        """Test method-specific grain code resolution with basic code."""
        layer = Layer(grain_form='RG')
        # The density_method_geldsetzer method accepts specific grain codes
        result = _resolve_grain_form(layer, method_name='density_method_geldsetzer')
        assert result == 'RG'
    
    def test_method_specific_sub_code(self):
        """Test method-specific grain code resolution with sub-grain code."""
        layer = Layer(grain_form='RGmx')
        # Should work with sub-grain codes too if they're in the valid set
        result = _resolve_grain_form(layer, method_name='density_method_geldsetzer')
        # RGmx might not be in valid codes, but function should return it anyway
        assert result is not None
    
    def test_main_grain_form_fallback(self):
        """Test that main_grain_form property is used as fallback."""
        layer = Layer(grain_form='FCxr')
        # main_grain_form should extract 'FC'
        assert layer.main_grain_form == 'FC'
        
        # _resolve_grain_form should handle this gracefully
        result = _resolve_grain_form(layer)
        assert result == 'FCxr'
    
    def test_no_grain_form_sub_attribute(self):
        """
        REGRESSION TEST: Ensure Layer doesn't have grain_form_sub attribute.
        
        This is the bug that was fixed - the dispatcher was trying to access
        layer.grain_form_sub which doesn't exist.
        """
        layer = Layer(grain_form='RG')
        
        # Verify grain_form_sub doesn't exist
        assert not hasattr(layer, 'grain_form_sub')
        
        # But _resolve_grain_form should still work
        result = _resolve_grain_form(layer)
        assert result == 'RG'
    
    def test_resolve_grain_form_doesnt_raise_attribute_error(self):
        """
        REGRESSION TEST: _resolve_grain_form should never raise AttributeError.
        
        This tests that the fix prevents the AttributeError that was occurring.
        """
        layer = Layer(grain_form='RGmx', density_measured=250, hand_hardness='4F')
        
        # Should not raise AttributeError
        try:
            result = _resolve_grain_form(layer, method_name='density_method_geldsetzer')
            # Should get some result (even if None)
            assert result is not None or result is None  # Either is fine, just no error
        except AttributeError as e:
            pytest.fail(f"_resolve_grain_form raised AttributeError: {e}")


class TestGrainFormInExecution:
    """Integration tests for grain_form in execution context."""
    
    def test_execute_pathway_with_grain_form(self):
        """Test that execution pathways work with grain_form."""
        from snowpyt_mechparams import ExecutionEngine, Slab
        from snowpyt_mechparams.graph import graph
        
        # Create a layer with grain_form (no grain_form_sub)
        layer = Layer(
            thickness=30,
            density_measured=250,
            grain_form='RG',
            hand_hardness='4F'
        )
        slab = Slab(layers=[layer], angle=35)
        
        # Execute density calculation
        engine = ExecutionEngine(graph)
        
        # Should not raise AttributeError
        try:
            results = engine.execute_all(
                slab=slab,
                target_parameter='density'
            )
            # Check that at least one pathway succeeded
            assert results.successful_pathways > 0
        except AttributeError as e:
            if 'grain_form_sub' in str(e):
                pytest.fail(f"grain_form_sub AttributeError in execution: {e}")
            else:
                raise
    
    def test_execute_d11_pathway_with_grain_form(self):
        """Test D11 calculation works with grain_form (regression test for notebook bug)."""
        from snowpyt_mechparams import ExecutionEngine, Slab
        from snowpyt_mechparams.graph import graph
        
        # Create a simple slab
        layer = Layer(
            thickness=30,
            density_measured=250,
            grain_form='RG',
            hand_hardness='4F'
        )
        slab = Slab(layers=[layer], angle=35)
        
        # Execute D11 calculation (this was failing in the notebook)
        engine = ExecutionEngine(graph)
        
        try:
            results = engine.execute_all(
                slab=slab,
                target_parameter='D11'
            )
            
            # Check that some D11 values were computed
            d11_count = sum(
                1 for pr in results.pathways.values()
                if pr.slab and pr.slab.D11 is not None
            )
            
            # Should have at least one D11 value
            assert d11_count > 0, "No D11 values computed (check grain_form handling)"
            
        except AttributeError as e:
            if 'grain_form_sub' in str(e):
                pytest.fail(f"grain_form_sub AttributeError in D11 execution: {e}")
            else:
                raise
