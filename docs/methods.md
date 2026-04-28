# Methods And Provenance

This page is generated from `snowpyt_mechparams.methods.default_registry()`.
Update registry metadata, then regenerate this file instead of hand-editing the
table.

```bash
uv run --extra dev python docs/_scripts/generate_method_catalog.py
uv run --extra dev python docs/_scripts/generate_method_catalog.py --check
```

The table records graph dependencies, runtime inputs, output attributes, cache
scope, citation labels, and short descriptions for every built-in method.

| Target | Method | Level | Graph inputs | Runtime inputs | Output attribute | Cache | Citation | Description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `density` | `data_flow` | `layer` | `measured_density` | `density_measured` | `density_calculated` | `layer` | Direct field measurement | Use directly measured density. |
| `density` | `geldsetzer` | `layer` | `measured_hand_hardness`, `measured_grain_form` | `hand_hardness_index`, `grain_form` | `density_calculated` | `layer` | Geldsetzer & Jamieson (2000) | Estimate density from hand hardness and grain form. |
| `density` | `kim_jamieson_table2` | `layer` | `measured_hand_hardness`, `measured_grain_form` | `hand_hardness_index`, `grain_form` | `density_calculated` | `layer` | Kim & Jamieson (2014) | Estimate density from hand hardness and grain form using Table 2. |
| `density` | `kim_jamieson_table5` | `layer` | `measured_hand_hardness`, `measured_grain_form`, `measured_grain_size` | `hand_hardness_index`, `grain_form`, `grain_size` | `density_calculated` | `layer` | Kim & Jamieson (2014) | Estimate density from hand hardness, grain form, and grain size using Table 5. |
| `elastic_modulus` | `bergfeld` | `layer` | `density`, `measured_grain_form` | `density`, `grain_form` | `elastic_modulus` | `none` | Bergfeld et al. (2023) | Estimate elastic modulus from density and grain form. |
| `elastic_modulus` | `kochle` | `layer` | `density`, `measured_grain_form` | `density`, `grain_form` | `elastic_modulus` | `none` | Kochle & Schneebeli (2014) | Estimate elastic modulus from density and grain form. |
| `elastic_modulus` | `wautier` | `layer` | `density`, `measured_grain_form` | `density`, `grain_form` | `elastic_modulus` | `none` | Wautier et al. (2015) | Estimate elastic modulus from density and grain form. |
| `elastic_modulus` | `schottner` | `layer` | `density`, `measured_grain_form` | `density`, `grain_form` | `elastic_modulus` | `none` | Schottner et al. (2026) | Estimate elastic modulus from density and grain form. |
| `poissons_ratio` | `kochle` | `layer` | `measured_grain_form` | `grain_form` | `poissons_ratio` | `none` | Kochle & Schneebeli (2014) | Estimate Poisson's ratio from grain form. |
| `poissons_ratio` | `srivastava` | `layer` | `density`, `measured_grain_form` | `density`, `grain_form` | `poissons_ratio` | `none` | Srivastava et al. (2016) | Estimate Poisson's ratio from density and grain form. |
| `shear_modulus` | `lame_relationship` | `layer` | `elastic_modulus`, `poissons_ratio` | `elastic_modulus`, `poissons_ratio` | `shear_modulus` | `none` | Isotropic Lame relationship | Calculate shear modulus from elastic modulus and Poisson's ratio. |
| `slab_weight` | `sum_layer_weight` | `slab` | `density`, `measured_layer_thickness` | `slab` | `slab_weight` | `none` | SnowPyt-MechParams coverage helper | Integrate computed density through slab thickness. |
| `slab_weight_shear` | `slope_parallel_component` | `slab` | `slab_weight`, `measured_slope_angle` | `slab` | `slab_weight_shear` | `none` | SnowPyt-MechParams coverage helper | Project slab weight parallel to slope angle. |
| `slab_weight_shear_with_elasticity` | `combine_shear_weight_and_elasticity` | `slab` | `slab_weight_shear`, `elastic_modulus`, `poissons_ratio` | `slab` | `slab_weight_shear_with_elasticity` | `none` | SnowPyt-MechParams coverage helper | Coverage target requiring W_s, E, and nu. |
| `A11` | `weissgraeber_rosendahl` | `slab` | `measured_layer_thickness`, `elastic_modulus`, `poissons_ratio` | `slab` | `A11` | `none` | Weissgraeber & Rosendahl (2023) | Calculate extensional stiffness from layer thickness, E, and nu. |
| `B11` | `weissgraeber_rosendahl` | `slab` | `measured_layer_location`, `measured_layer_thickness`, `elastic_modulus`, `poissons_ratio` | `slab` | `B11` | `none` | Weissgraeber & Rosendahl (2023) | Calculate bending-extension coupling from layer location, thickness, E, and nu. |
| `D11` | `weissgraeber_rosendahl` | `slab` | `measured_layer_location`, `measured_layer_thickness`, `elastic_modulus`, `poissons_ratio` | `slab` | `D11` | `none` | Weissgraeber & Rosendahl (2023) | Calculate bending stiffness from layer location, thickness, E, and nu. |
| `A55` | `weissgraeber_rosendahl` | `slab` | `measured_layer_thickness`, `shear_modulus` | `slab` | `A55` | `none` | Weissgraeber & Rosendahl (2023) | Calculate shear stiffness from layer thickness and shear modulus. |

## Source Materials

The `sources/` directory contains reference materials used to implement the
published parameterizations. Those files are retained for traceability in the
repository but are not included in installed packages.

Formula-level docstrings in `src/snowpyt_mechparams/methods/` provide equation
notes, units, uncertainty behavior, supported grain forms, and validity ranges.
