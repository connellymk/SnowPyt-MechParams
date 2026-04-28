# Getting Started

## Installation

The recommended development setup uses `uv`:

```bash
git clone https://github.com/connellymk/snowpyt-mechparams.git
cd snowpyt-mechparams
uv sync --extra dev
uv run --extra dev pytest
```

Editable installs through `pip` are also supported:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Use the `weac` extra only when you need the optional WEAC stability adapter. That
extra requires Python 3.12 or newer.

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
```

`execute_all` enumerates every structural pathway to the requested target and
then tests each pathway against the slab data. A pathway can fail gracefully when
the slab is missing an input or a method does not support a grain form or value
range.

## Inspect Pathways

```python
from snowpyt_mechparams.graph import default_graph
from snowpyt_mechparams.pathway import find_parameterizations

target = default_graph.get_node("D11")
pathways = find_parameterizations(default_graph, target)

print(len(pathways))
```

Pathway search is independent of any real snow pit. It answers what could be
computed from the registered graph. Execution answers what succeeds on a
particular slab.
