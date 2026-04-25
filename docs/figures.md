# Figure Manifest

This project keeps the code that creates documentation and manuscript figures in
the repository. Paper figures are exported as both PDF and PNG: PDF is the
preferred line-art format for NHESS/Copernicus submission, and PNG is kept for
preview and web use. Raster exports use 300 dpi.

## Output Locations

Paper figure helpers save each figure to both locations:

- `paper/figures/` in this repository
- `/Users/marykate/Desktop/Snow/mech_params_paper/figures/`

The full SnowPilot CAAML dataset is intentionally tracked under
`examples/data/` for now so notebook results can be reproduced from this
repository without a separate data download step.

## Generated Graph Diagrams

| Figure | Generator | Repo output | Use |
|---|---|---|---|
| Overview graph | `scripts/generate_diagram.py --type overview` | `docs/diagrams/overview.md`, `docs/diagrams/overview.png` | Documentation overview |
| Layer pathways | `scripts/generate_diagram.py --type layer` | `docs/diagrams/layer.md`, `docs/diagrams/layer.png` | Layer parameter documentation |
| Slab stiffness pathways | `scripts/generate_diagram.py --type slab` | `docs/diagrams/slab.md`, `docs/diagrams/slab.png` | Slab stiffness documentation |
| Slab weight pathways | `scripts/generate_diagram.py --type slab_weight` | `docs/diagrams/slab_weight.md`, `docs/diagrams/slab_weight.png` | Slab-weight target documentation |
| Full parameter graph | `scripts/generate_diagram.py --type full` | `docs/diagrams/full.md`, `docs/diagrams/full.png` | Complete graph reference |

Regenerate all graph diagrams with:

```bash
python scripts/generate_diagram.py --type all --format both --output docs/diagrams/
```

## Paper Figures

| Figure stem | Primary generator | Repo output | Paper output | Use |
|---|---|---|---|---|
| `intro_flowchart` | `examples/paper_diagrams.ipynb` via `build_intro_workflow_figure()` | `paper/figures/intro_flowchart.pdf/.png` | `mech_params_paper/figures/intro_flowchart.pdf/.png` | Manuscript workflow figure |
| `snowpylot_data_model` | `examples/paper_diagrams.ipynb` via `build_snowpylot_data_model_figure()` | `paper/figures/snowpylot_data_model.pdf/.png` | `mech_params_paper/figures/snowpylot_data_model.pdf/.png` | Manuscript data model figure |
| `mechparams_data_model` | `examples/paper_diagrams.ipynb` via `build_mechparams_data_model_figure()` | `paper/figures/mechparams_data_model.pdf/.png` | `mech_params_paper/figures/mechparams_data_model.pdf/.png` | Manuscript data model figure |
| `grain_form_hardness_ranges` | `examples/paper_diagrams.ipynb` via `build_grain_form_hardness_ranges_figure()` | `paper/figures/grain_form_hardness_ranges.pdf/.png` | `mech_params_paper/figures/grain_form_hardness_ranges.pdf/.png` | Density method applicability |
| `emod_theoretical_curves` | `examples/paper_diagrams.ipynb` via `build_elastic_modulus_curves_figure()` | `paper/figures/emod_theoretical_curves.pdf/.png` | `mech_params_paper/figures/emod_theoretical_curves.pdf/.png` | Elastic modulus method comparison |
| `params_graph` | `examples/paper_diagrams.ipynb` via `build_params_graph_figure()` | `paper/figures/params_graph.pdf/.png` | `mech_params_paper/figures/params_graph.pdf/.png` | Manuscript graph figure |
| `density_pathways` | `examples/paper_diagrams.ipynb` via `build_density_pathways_figure()` | `paper/figures/density_pathways.pdf/.png` | `mech_params_paper/figures/density_pathways.pdf/.png` | Density pathway schematic |
| `slab_weight_coverage_comparison` | `examples/slab_weight_inputs.ipynb` via `build_slab_weight_coverage_comparison_figure()` | `paper/figures/slab_weight_coverage_comparison.pdf/.png` | `mech_params_paper/figures/slab_weight_coverage_comparison.pdf/.png` | Slab-weight input coverage |
| `slab_weight_shear_with_elasticity_attrition` | `examples/slab_weight_inputs.ipynb` via `build_slab_weight_shear_with_elasticity_attrition_figure()` | `paper/figures/slab_weight_shear_with_elasticity_attrition.pdf/.png` | `mech_params_paper/figures/slab_weight_shear_with_elasticity_attrition.pdf/.png` | Slab-weight elastic-input attrition |
| `d11_top_pathways` | `examples/all_D11_pathways.ipynb` via `build_d11_distribution_figure()` | `paper/figures/d11_top_pathways.pdf/.png` | `mech_params_paper/figures/d11_top_pathways.pdf/.png` | D11 pathway distribution |

Older exploratory notebooks remain in `examples/archive/` for reference, but
paper-facing figures should be built through `examples/paper_figure_utils.py`
and exported with `save_paper_figure()`.
