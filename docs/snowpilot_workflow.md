# SnowPilot And CAAML Workflow

SnowPyt-MechParams reads SnowPilot CAAML XML through `snowpylot`, converts raw
profiles into project model objects, and creates slabs from weak-layer
definitions.

```python
from snowpyt_mechparams.models import Pit
from snowpyt_mechparams.snowpilot import parse_caaml_file

snow_pit = parse_caaml_file("examples/sample_data/snowpits-27829-caaml.xml")
pit = Pit.from_snow_pit(snow_pit)
slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")
```

`Pit.create_slabs` supports:

| Weak-layer definition | Behavior |
| --- | --- |
| `layer_of_concern` | Creates one slab above the marked layer of concern. |
| `CT_failure_layer` | Creates one slab per matching CT result with Q1, SC, or SP fracture character. |
| `ECTP_failure_layer` | Creates one slab per propagating ECT result. |

Each slab stores source metadata such as `pit_id`, `slab_id`,
`weak_layer_source`, `test_result_index`, and `test_result_properties`.

## Dataset Tiers

The full `examples/data/` directory is retained in the git repository for
research reproducibility and manuscript notebooks. It is intentionally not
included in source distributions because it contains tens of thousands of XML
files.

The packaged `examples/sample_data/` directory contains a tiny CAAML sample for
tests, docs, and release artifacts. Use it for smoke checks and tutorials, not
for population-level analysis.
