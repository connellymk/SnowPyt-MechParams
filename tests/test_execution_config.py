"""Tests for ExecutionConfig."""

from snowpyt_mechparams.execution import ExecutionConfig


def test_config_defaults():
    """Test default configuration values."""
    config = ExecutionConfig()
    assert config.verbose is False


def test_config_custom_values():
    """Test creating config with custom values."""
    config = ExecutionConfig(verbose=True)
    assert config.verbose is True


def test_config_verbose_false():
    """Test verbose can be explicitly set to False."""
    config = ExecutionConfig(verbose=False)
    assert config.verbose is False


def test_config_is_simple():
    """Test that config only has verbose attribute."""
    config = ExecutionConfig()
    
    # Config should only have verbose (and dataclass internals)
    config_attrs = [attr for attr in dir(config) if not attr.startswith('_')]
    # Should have verbose and maybe some dataclass methods
    assert 'verbose' in config_attrs
    
    # Should NOT have these removed attributes
    assert not hasattr(config, 'include_plate_theory')
    assert not hasattr(config, 'enable_caching')
    assert not hasattr(config, 'fail_on_first_error')
    assert not hasattr(config, 'max_pathways')
