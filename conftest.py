"""Shared pytest configuration and marks for SnowPyt-MechParams tests."""

import pytest

try:
    import weac as _weac_pkg  # noqa: F401
    _WEAC_AVAILABLE = True
except ImportError:
    _WEAC_AVAILABLE = False

requires_weac = pytest.mark.skipif(
    not _WEAC_AVAILABLE,
    reason="weac package not installed — skip integration tests",
)
