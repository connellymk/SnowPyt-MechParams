# SnowPyt-MechParams Documentation

SnowPyt-MechParams estimates snow mechanical parameters from snow pit
observations. It helps researchers compare published density, elastic-modulus,
Poisson's-ratio, shear-modulus, slab-weight, and slab-stiffness methods on the
same slab and trace which observations support each output.

Use these docs when you want to run analyses, understand method provenance, or
extend the calculation graph with a new published parameterization.

```{toctree}
:maxdepth: 2
:caption: Research Workflows

getting_started
units_uncertainty
snowpilot_workflow
pathway_execution
interpreting_results
examples
methods
```

```{toctree}
:maxdepth: 2
:caption: Contributor Reference

contributor_guide
code_description
execution_engine
api_reference
```

## Build Locally

Install the development environment and build the docs with warnings treated as
errors:

```bash
uv sync --extra dev
uv run --extra dev sphinx-build -W -b html docs /tmp/snowpyt_docs_html
```

The documentation source is Markdown rendered by Sphinx through MyST. API pages
use autodoc against the local `src/` package.
