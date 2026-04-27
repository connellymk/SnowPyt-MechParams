"""Sphinx configuration for SnowPyt-MechParams documentation."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

project = "SnowPyt-MechParams"
author = "Mary Connelly, Samuel Verplanck, and SnowPyt-MechParams Contributors"
copyright = "2026, SnowPyt-MechParams Contributors"
release = "0.4.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}
master_doc = "index"

html_theme = "sphinx_rtd_theme"
html_static_path = []

myst_heading_anchors = 3
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_google_docstring = False
napoleon_numpy_docstring = True

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]
