# Examples

The repository uses three example tiers.

## Tiny Synthetic Examples

Use synthetic slabs for quick API checks and documentation snippets. These do
not depend on external files and are appropriate for fast tests.

```python
from snowpyt_mechparams.models import Layer, Slab

slab = Slab(
    layers=[Layer(thickness=30, density_measured=250, grain_form="RG")],
    angle=35,
)
```

## Packaged Sample Data

`examples/sample_data/` contains a tiny SnowPilot/CAAML sample that is included
in source distributions. It is suitable for parser smoke tests and tutorials:

```python
from pathlib import Path

from snowpyt_mechparams.models import Pit
from snowpyt_mechparams.snowpilot import parse_caaml_file

sample = Path("examples/sample_data/snowpits-27829-caaml.xml")
pit = Pit.from_snow_pit(parse_caaml_file(str(sample)))
slabs = pit.create_slabs("ECTP_failure_layer")
```

## Full Research Dataset

`examples/data/` contains the full SnowPilot/CAAML dataset used by the active
notebooks and paper-support workflows. It is retained in git for reproducibility
but excluded from source distributions.

Active notebooks include:

| Notebook | Purpose |
| --- | --- |
| `slab_weight_inputs.ipynb` | Slab-weight and elasticity input coverage. |
| `all_D11_pathways.ipynb` | All currently available `D11` pathways. |
| `all_density_pathways.ipynb` | Density method comparison. |
| `all_e_mod_pathways.ipynb` | Elastic-modulus method comparison. |
| `all_poissons_ratio_pathways.ipynb` | Poisson's-ratio method comparison. |
| `dataset_overview.ipynb` | Dataset inventory and completeness summaries. |

Run notebooks through the project environment:

```bash
uv run --extra dev jupyter nbconvert --to notebook --execute examples/slab_weight_inputs.ipynb --inplace
```
