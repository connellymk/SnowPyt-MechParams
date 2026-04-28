# SnowPyt-MechParams

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Project Info

SnowPyt-MechParams estimates snow mechanical parameters from snow pit
observations, helping researchers compare how published density, modulus,
Poisson's-ratio, shear-modulus, slab-weight, and slab-stiffness methods propagate
field measurements into mechanical outputs. The package is organized around
domain models, a method registry, a generated parameter graph, pathway search,
and an execution engine, so adding a method in one place makes it available for
graph construction, pathway enumeration, and calculation.

The project is intended for snow mechanics and avalanche researchers who want to:

- compare published parameterizations on the same slab
- test new empirical or mechanics-based methods
- trace which observations support a target parameter
- preserve uncertainty through calculation pathways
- identify how missing measurements limit slab-scale outputs

## Installation

The recommended development setup uses `uv`, which creates and manages the
project environment in `.venv`:

```bash
git clone https://github.com/connellymk/snowpyt-mechparams.git
cd snowpyt-mechparams
uv sync --extra dev
uv run --extra dev pytest
```

Manual editable installs are also supported:

```bash
git clone https://github.com/connellymk/snowpyt-mechparams.git
cd snowpyt-mechparams
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional extras are available for plotting, columnar I/O, documentation, and
WEAC-based stability calculations:

```bash
pip install -e ".[plotting,io,docs]"
pip install -e ".[weac]"  # requires Python 3.12+
```

## Documentation

The full documentation is built with Sphinx and MyST from `docs/`:

```bash
uv run --extra dev sphinx-build -W -b html docs /tmp/snowpyt_docs_html
```

Start with `docs/getting_started.md` for research workflows and
`docs/methods.md` for the registry-generated methods and provenance catalog.

## Quick Start

```python
from uncertainties import ufloat

from snowpyt_mechparams import ExecutionEngine
from snowpyt_mechparams.execution import ExecutionConfig
from snowpyt_mechparams.models import Layer, Slab

layers = [
    Layer(thickness=ufloat(20, 1), hand_hardness="1F", grain_form="RG"),
    Layer(thickness=ufloat(25, 1), density_measured=ufloat(220, 20), grain_form="DF"),
]
slab = Slab(layers=layers, angle=35.0)

engine = ExecutionEngine()
results = engine.execute_all(
    slab,
    target_parameter="D11",
    config=ExecutionConfig(include_method_uncertainty=False),
)

print(results.successful_pathways, "successful pathways")

for description, pathway_result in results.get_successful_pathways().items():
    print(description, pathway_result.slab.D11)
```

To inspect available pathways without running calculations:

```python
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.pathway import find_parameterizations

target = default_graph.get_node("D11")
pathways = find_parameterizations(default_graph, target)

print(len(pathways))
```

## What It Computes

Layer-level targets:

- `density`
- `elastic_modulus`
- `poissons_ratio`
- `shear_modulus`

Slab-level targets:

- `A11`: extensional stiffness
- `B11`: bending-extension coupling
- `D11`: bending stiffness
- `A55`: shear stiffness
- `slab_weight`
- `slab_weight_shear`
- `slab_weight_shear_with_elasticity`

Stability-criteria utilities are also available for Roch and WEAC workflows that
already provide the required weak-layer or fracture inputs.

## Project Structure

The source package is organized by research responsibility:

- `snowpyt_mechparams.models`: `Layer`, `WeakLayer`, `Slab`, and `Pit` domain
  objects.
- `snowpyt_mechparams.methods`: method specifications, the default registry, and
  built-in formulas.
- `snowpyt_mechparams.graph`: graph data structures and the registry-generated
  `default_graph`.
- `snowpyt_mechparams.pathway`: pathway objects, graph search, and pathway
  deduplication.
- `snowpyt_mechparams.execution`: pathway planning, formula dispatch, caching,
  tracing, and result objects.
- `snowpyt_mechparams.stability_criteria`: Roch and WEAC stability criteria.
- `snowpyt_mechparams.snowpilot`: SnowPilot/CAAML-oriented data helpers.

Package-level READMEs in `src/snowpyt_mechparams/` describe each public package
in more detail.

## Adding And Testing A Method

Most new methods only need two code changes: add the formula implementation and
register it with one `MethodSpec`.

### 1. Place the formula

Add layer formulas under `src/snowpyt_mechparams/methods/layer/` and slab
formulas under `src/snowpyt_mechparams/methods/slab/`. Keep the function focused
on the scientific calculation: it should accept physical inputs and return the
calculated value.

### 2. Register the method

Add one `MethodSpec` in `src/snowpyt_mechparams/methods/registry.py`.

```python
from snowpyt_mechparams.methods import MethodSpec, ParameterLevel

MethodSpec(
    target="density",
    method_name="new_density_method",
    level=ParameterLevel.LAYER,
    source_nodes=("measured_hand_hardness", "measured_grain_form"),
    required_inputs=("hand_hardness_index", "grain_form"),
    function=new_density_method,
    output_attr="density_calculated",
    cache_scope="layer",
    citation="Author et al. (Year)",
    description="Estimate density from hand hardness and grain form.",
)
```

Key fields:

- `target`: parameter being calculated, such as `density`, `D11`, or
  `slab_weight_shear`
- `method_name`: name shown in pathway descriptions
- `level`: `LAYER` or `SLAB`
- `source_nodes`: measured inputs or intermediate parameters required by the
  method
- `required_inputs`: function arguments pulled from the layer, slab, or
  execution context
- `function`: formula implementation
- `output_attr`: field where the result is stored
- `cache_scope`: optional cache behavior; valid values are `"none"` and
  `"layer"`. Slab methods should omit it unless slab-level cache semantics are
  added later.

After registration, the method is available to graph construction, pathway
search, dispatch, and execution.

### 3. Test the method

Method tests should check expected numerical output, uncertainty behavior,
invalid or missing inputs, and any publication-specific assumptions about units,
grain forms, or valid ranges.

If the method changes available pathways, update framework tests to verify that
the method appears once in the registry, the generated graph includes the
expected edge, pathway counts change only where expected, execution produces the
target, and the source slab is not mutated.

Useful test files include:

- `tests/test_methods_registry.py`
- target-specific tests such as `tests/test_density_methods.py`
- graph and pathway tests such as `tests/test_graph.py` and
  `tests/test_algorithm.py`
- execution tests such as `tests/test_engine_api.py` and
  `tests/test_executor_dynamic_programming.py`

Run the checks:

```bash
uv run --extra dev pytest
uv run --extra dev black --check src tests
uv run --extra dev ruff check src tests examples
uv run --extra dev mypy src
```

Smoke notebooks when public imports, pathway counts, or scientific outputs
change:

```bash
uv run --extra dev jupyter nbconvert --to notebook --execute examples/slab_weight_inputs.ipynb --inplace
uv run --extra dev jupyter nbconvert --to notebook --execute examples/all_D11_pathways.ipynb --inplace
uv run --extra dev jupyter nbconvert --to notebook --execute examples/all_density_pathways.ipynb --inplace
```

## Examples And Notebooks

Examples are organized in three tiers:

- tiny synthetic snippets in the documentation and tests
- `examples/sample_data/`, a packaged CAAML sample for smoke checks
- `examples/data/`, the full repo-local SnowPilot/CAAML dataset for notebooks
  and manuscript workflows

Active notebooks live in `examples/`:

- `slab_weight_inputs.ipynb`: slab-weight and elasticity input coverage.
- `all_D11_pathways.ipynb`: all currently available `D11` pathways.
- `all_density_pathways.ipynb`: density method comparison.
- `all_e_mod_pathways.ipynb`: elastic-modulus method comparison.
- `all_poissons_ratio_pathways.ipynb`: Poisson's-ratio method comparison.

Preferred imports for new examples:

```python
from snowpyt_mechparams.execution import ExecutionEngine
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.pathway import find_parameterizations
```

The full `examples/data/` XML dataset is retained in the git repository for
research reproducibility but is not included in source distributions. Source
distributions include only the small `examples/sample_data/` XML sample.

## Public API

Top-level imports such as `Layer`, `Slab`, and `ExecutionEngine` remain
supported for common workflows. For framework internals and advanced extension
work, prefer explicit subpackage imports such as `snowpyt_mechparams.methods`,
`snowpyt_mechparams.graph`, and `snowpyt_mechparams.execution`.

## Additional Documentation

- `docs/code_description.md`: current architecture, module responsibilities, and
  data flow.
- `docs/execution_engine.md`: execution-engine design notes.
- `src/snowpyt_mechparams/*/README.md`: package-level orientation for
  contributors.

## Citation

```bibtex
@software{snowpyt_mechparams,
  author = {Connelly, Mary and Verplanck, Samuel and {SnowPyt-MechParams Contributors}},
  title = {SnowPyt-MechParams: A collaborative Python library for snow mechanical parameter estimation},
  url = {https://github.com/connellymk/snowpyt-mechparams},
  version = {0.4.0},
  year = {2026}
}
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for
details.

**Version**: 0.4.0 | **Last Updated**: April 2026 | **Python**: 3.9+
