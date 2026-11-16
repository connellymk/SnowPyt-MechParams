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

A failure is assigned to the first layer satisfying
`depth_top <= failure_depth < depth_bottom`. The entire containing layer is
excluded from the overlying slab, even when failure occurs inside it. No added
tolerance or partial-layer splitting is applied. Separate qualifying tests remain
separate slabs and may share observations.

Direct density uses the first sample whose raw depth and thickness exactly match
a layer. Depth-only samples are not assigned to a layer mean. The reviewer notebook audits unmatched intervals without changing
density assignments; see `paper_analysis/README.md` in the repository. Local
audits do not establish SnowPilot website validation guarantees. The workflow does
not screen wetness.

## Dataset Tiers

The full `examples/data/` directory is retained in the git repository for
research reproducibility and manuscript notebooks. It is intentionally not
included in source distributions because it contains tens of thousands of XML
files.

The packaged `examples/sample_data/` directory contains a tiny CAAML sample for
tests, docs, and release artifacts. Use it for smoke checks and tutorials, not
for population-level analysis.
