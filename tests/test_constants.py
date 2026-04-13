"""Tests for exact physical constants and their import behavior."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from snowpyt_mechparams.constants import E_ICE_POLYCRYSTALLINE, G_ICE


def test_exact_ice_constants_are_plain_floats():
    """Exact ice reference values should not be zero-uncertainty UFloats."""
    assert isinstance(E_ICE_POLYCRYSTALLINE, float)
    assert isinstance(G_ICE, float)


def test_constants_module_imports_under_warning_errors(tmp_path):
    """Loading constants directly from source should not emit warnings."""
    project_root = Path(__file__).resolve().parents[1]
    constants_path = project_root / "src" / "snowpyt_mechparams" / "constants.py"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(tmp_path)

    command = (
        "import importlib.util, pathlib; "
        f"path = pathlib.Path({str(constants_path)!r}); "
        "spec = importlib.util.spec_from_file_location('snowpyt_mechparams.constants_test', path); "
        "module = importlib.util.module_from_spec(spec); "
        "spec.loader.exec_module(module)"
    )
    result = subprocess.run(
        [sys.executable, "-Werror", "-c", command],
        capture_output=True,
        text=True,
        env=env,
        cwd=project_root,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
