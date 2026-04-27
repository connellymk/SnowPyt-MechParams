# sources/

Reference materials for the empirical parameterizations implemented in `src/snowpyt_mechparams/`.

| Folder / File | Implemented in |
|---|---|
| `density/` | `methods/layer/density.py` — Geldsetzer (2000), Kim & Jamieson (2014) |
| `youngs_modulus/` | `methods/layer/elastic_modulus.py` — Bergfeld (2023), Köchle (2014), Wautier (2015), Schöttner |
| `poissons_ratio/` | `methods/layer/poissons_ratio.py` — Köchle (2014), Srivastava (2016) |
| `slab/` | `methods/slab/` — Weißgraeber & Rosendahl (2023) |
| `tc-17-1475-2023.xml` | JATS XML for Weißgraeber & Rosendahl (2023) |

These files are not included in the installed package. They are kept here for traceability between published regression tables and the coefficient values in the source code.
