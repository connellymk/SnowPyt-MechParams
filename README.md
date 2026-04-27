# SnowPyt-MechParams

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SnowPyt-MechParams estimates mechanical parameters of snow layers and slabs from snow pit observations. It supports multiple published methods for density, elastic modulus, Poisson's ratio, shear modulus, slab stiffness, and slab-weight coverage targets.

The framework is registry-driven: each method is described once in a declarative `MethodSpec`, and the graph, pathway search, dispatcher, and execution planner all derive behavior from that registry.

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
    "D11",
    config=ExecutionConfig(include_method_uncertainty=False),
)

print(results.successful_pathways, "successful pathways")
for description, pathway in results.get_successful_pathways().items():
    print(description, pathway.slab.D11)
```

To inspect pathways without executing them:

```python
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.pathway import find_parameterizations

target = default_graph.get_node("D11")
pathways = find_parameterizations(default_graph, target)
print(len(pathways))  # 32
```

## Installation

```bash
git clone https://github.com/connellymk/snowpyt-mechparams.git
cd snowpyt-mechparams
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

With `uv`:

```bash
uv sync --extra dev
uv run --extra dev pytest
```

## Architecture

The package is organized around a simple data flow:

```text
SnowPilot/CAAML -> models -> methods registry -> graph -> pathway search -> execution -> result slabs
```

- `models`: `Layer`, `WeakLayer`, `Slab`, and `Pit` objects store field measurements, metadata, and computed outputs.
- `methods`: the extensibility center. `MethodSpec` and `MethodRegistry` describe every method, its dependencies, its callable, and its output attribute.
- `graph`: builds `default_graph` from the registry instead of hand-writing graph edges.
- `pathway`: finds all valid parameterizations through the graph and deduplicates equivalent method choices.
- `execution`: plans and runs pathway calculations on slabs, using an `ExecutionContext` so source slabs are not mutated.
- `stability_criteria`: direct Roch and WEAC APIs for analyses that supply the required weak-layer strength or fracture inputs.

## Supported Targets

Layer targets:

- `density`: direct measured density, Geldsetzer, Kim/Jamieson Table 2, Kim/Jamieson Table 5.
- `elastic_modulus`: Bergfeld, Kochle, Wautier, Schottner.
- `poissons_ratio`: Kochle, Srivastava.
- `shear_modulus`: Lame relationship from elastic modulus and Poisson's ratio.

Slab targets:

- `A11`, `B11`, `D11`, `A55`: Weissgraeber/Rosendahl laminate-theory stiffnesses.
- `slab_weight`, `slab_weight_shear`, `slab_weight_shear_with_elasticity`: slab-weight input coverage helpers.

Current expected pathway counts include 4 density pathways, 16 elastic-modulus pathways, 5 Poisson's-ratio pathways, and 32 pathways for `D11`, `A55`, and `slab_weight_shear_with_elasticity`.

## Adding A Method

Most framework extensions should start in `src/snowpyt_mechparams/methods/registry.py`.

1. Implement the formula in `methods/layer/` or `methods/slab/`.
2. Add one `MethodSpec` with:
   - `target`
   - `method_name`
   - `level`
   - `source_nodes`
   - `required_inputs`
   - `function`
   - `output_attr`
   - `cache_scope`
   - short `description` or `citation`
3. Add or update tests for the formula, registry-to-graph consistency, and pathway counts.
4. Update the relevant package README if the public workflow changes.

After registration, the graph and dispatcher pick the method up automatically:

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
)
```

## Examples

Active notebooks live in `examples/`:

- `slab_weight_inputs.ipynb`: slab-weight and elasticity input coverage.
- `all_D11_pathways.ipynb`: all 32 D11 pathways.
- `all_density_pathways.ipynb`: density method comparison.
- `all_e_mod_pathways.ipynb`: elastic-modulus method comparison.
- `all_poissons_ratio_pathways.ipynb`: Poisson's-ratio method comparison.

Preferred imports in notebooks:

```python
from snowpyt_mechparams.execution import ExecutionEngine
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.pathway import find_parameterizations
```

## Development Checks

```bash
uv run --extra dev pytest
uv run --extra dev black --check src tests
uv run --extra dev flake8 src tests
uv run --extra dev mypy src
```

Smoke active notebooks after changing public imports or execution behavior:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute examples/slab_weight_inputs.ipynb --inplace
.venv/bin/jupyter nbconvert --to notebook --execute examples/all_D11_pathways.ipynb --inplace
.venv/bin/jupyter nbconvert --to notebook --execute examples/all_density_pathways.ipynb --inplace
```

## Documentation

- `docs/code_description.md`: current module responsibilities and data flow.
- `docs/execution_engine.md`: historical execution-engine design notes.
- `src/snowpyt_mechparams/*/README.md`: package-level orientation for contributors.

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

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

**Version**: 0.4.0 | **Last Updated**: April 2026 | **Python**: 3.9+
