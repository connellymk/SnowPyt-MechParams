# sources/

Reference materials for the empirical parameterizations implemented in `src/snowpyt_mechparams/`.

| Folder / File | Implemented in |
|---|---|
| `density/` | `layer_parameters/density.py` — Geldsetzer (2000), Kim & Jamieson (2014) |
| `youngs_modulus/` | `layer_parameters/elastic_modulus.py` — Bergfeld (2023), Köchle (2014), Wautier (2015), Schöttner |
| `poissons_ratio/` | `layer_parameters/poissons_ratio.py` — Köchle (2014), Srivastava (2016) |
| `slab/` | `slab_parameters/` — Weißgraeber & Rosendahl (2023) |
| `tc-17-1475-2023.xml` | JATS XML for Weißgraeber & Rosendahl (2023) |

These files are not included in the installed package. They are kept here for traceability between published regression tables and the coefficient values in the source code.
