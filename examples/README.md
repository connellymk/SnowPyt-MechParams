# Examples

This directory contains active notebooks, paper-support utilities, archived
exploratory notebooks, a tiny packaged CAAML sample, and the full repo-local
SnowPilot/CAAML dataset used by the research workflows.

## Example Tiers

- `sample_data/`: tiny CAAML sample included in source distributions for docs
  and smoke tests.
- `data/`: full SnowPilot/CAAML dataset retained in the git repository for
  notebook and manuscript reproducibility. It is intentionally excluded from
  source distributions.
- synthetic snippets: small slabs created directly in documentation and tests.

## Active Notebooks

- `slab_weight_inputs.ipynb`: slab-weight and elasticity input coverage.
- `all_D11_pathways.ipynb`: all currently available `D11` pathways.
- `all_density_pathways.ipynb`: density method comparison.
- `all_e_mod_pathways.ipynb`: elastic-modulus method comparison.
- `all_poissons_ratio_pathways.ipynb`: Poisson's-ratio method comparison.
- `dataset_overview.ipynb`, `dataset_ectp_slabs.ipynb`, and
  `grain_form_count.ipynb`: dataset exploration and summary workflows.
- `paper_diagrams.ipynb`: generated diagrams and figures for manuscript work.

Run notebooks through the project environment:

```bash
uv run --extra dev jupyter nbconvert --to notebook --execute examples/slab_weight_inputs.ipynb --inplace
```

## Utilities

- `notebook_utils.py`: shared helpers for loading and preparing example data.
- `paper_figure_utils.py`: shared plotting helpers for paper figures.

## Data

`sample_data/` contains the packaged tutorial and test sample.

`data/` contains the full SnowPilot/CAAML XML files used by the example
notebooks and paper-support workflows. The dataset is intentionally retained in
this repository for now so existing research workflows remain reproducible, but
it is not packaged into source distributions.

## Archive

`archive/` contains older exploratory notebooks and scripts. Treat these as
historical references, not canonical examples for new workflows. New examples
should follow the active notebooks and the public imports documented in the root
README.
