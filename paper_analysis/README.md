# Reproducing the reviewer-response evidence

This revision implements the chosen responses with three production changes:
Wautier PP support, Schöttner calibration-density limits, and a symmetric
48% grain-size standard deviation. The existing notebooks produce the coverage,
D11, audit, and verification evidence. Monte Carlo propagation, correlation
sensitivity, alternative density assignment, and stability-model demonstrations
remain future work.

Use Python 3.13 with the tracked lockfile:

```sh
uv sync --locked --extra dev --extra io --extra docs
.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 examples/paper_diagrams.ipynb examples/slab_weight_inputs.ipynb paper_analysis/loss-analysis.ipynb examples/D11_analysis.ipynb paper_analysis/hand-verification.ipynb paper_analysis/reviewer_evidence.ipynb
```

Run each notebook from its own directory (as nbconvert does). Check that the
selected Jupyter kernel uses this checkout's `.venv/bin/python`. The order above
is significant: the reviewer notebook independently reconciles the D11 output.
The recorded source commit is the checkout HEAD at execution; the accompanying
source and notebook-source SHA-256 maps identify the exact files, including
changes awaiting the evidence commit. No multi-stage runner or cached attempt
tables are required. Exports default to
this repository; the external manuscript repository is not an automatic target.

The full 50,278 XML inputs are tracked in `examples/data/`. Sorting filenames
retains the existing cohort of 14,776 ECTP slabs, including repeated tests. The
last notebook archives baseline source at `c8b712e93fe219c9c5dd71e6a5a8a3a6d947866c`
and runs it in an isolated process against the same data and environment. It
does not emulate baseline equations through runtime overrides.

## Evidence index

| Response topic | Generating notebook | Compact evidence |
| --- | --- | --- |
| Wautier/Schöttner coverage changes (R2 major 3) | `reviewer_evidence.ipynb` | `reviewer_results/coverage_comparison.csv` |
| Slab construction, repeats, density exclusions (R2 major 4) | `reviewer_evidence.ipynb`, `loss-analysis.ipynb` | `reviewer_results/audit_summary.json` |
| Individual/union coverage (R2 major 5) | `reviewer_evidence.ipynb` | `reviewer_results/coverage.csv`, `coverage_summary.json` |
| First-failure losses (R1 major 7; R2 major 5) | `loss-analysis.ipynb` | `reviewer_results/first_failure_classes.csv`, `method_failure_summary.csv` |
| D11 spread and SD comparison (R1 minor L377–382; R2 major 6–7) | `../examples/D11_analysis.ipynb` | `reviewer_results/d11_summary.json`, `d11_per_slab.csv`, `d11_common.csv` |
| Independent worked calculations (R1 major 3; R2 minor 6) | `hand-verification.ipynb` | Worked calculation cells and final verification summary |
| Input/source versions and timings (R1 minor L486–489; R2 minor 6) | All six notebooks | `reviewer_results/reproduction.json`, `*_timing.json`, `validation.json` |
| Applicability and uncertainty tables (R2 major 3, 6) | `reviewer_evidence.ipynb` | `../paper/tables/elastic_applicability.{csv,tex}`, `observation_uncertainty.{csv,tex}` |

D11 comparison rows contain N·mm values and symmetric measurement SDs. Intervals
are descriptive, not physically bounded confidence intervals or significance
tests. The pooled relative SD includes each of the 316 × 16 results once.
The top-16 set and common-subset membership are unchanged between the fresh
baseline and corrected runs. Both reproduce 316 common slabs; the historical
saved notebook reported 317. The new domain checks do not explain that discrepancy.

The density audit records exact matches and unmatched sample geometry without
assigning replacement densities. All 8,650 unmatched observations lack sampling
intervals; there are no additional unmatched usable contained intervals in this
export. A depth alone does not establish a representative layer density.
Quality anomalies and repeated records are reported without filtering them.

Failure combinations partition attempts at the first unsuccessful step in the
stated reporting order. The saved partitions cover all three targets (4, 32, and 32 pathways).
Detailed method causes can overlap. The retained stepwise
figure combines processing exclusions with unavailable observations, and grain
and numerical restrictions with validity limits; the CSV evidence separates them.

## Canonical figure inventory

Each stem below has one PDF/PNG pair in `paper/figures/`.

| Notebook | Figure stems | Use |
| --- | --- | --- |
| `../examples/paper_diagrams.ipynb` | `method_support_matrices`, `density_pathways`, `emod_theoretical_curves` | Manuscript Figures 3, 6, 11 |
| `../examples/slab_weight_inputs.ipynb` | `slab_weight_coverage_comparison`, `slab_weight_shear_with_elasticity_attrition` | Manuscript Figures 7, 8 |
| `../examples/D11_analysis.ipynb` | `d11_paired_pathway_effects`, `d11_slab_uncertainty` | Manuscript Figures 9, 10 |
| `loss-analysis.ipynb` | `loss_stepwise_comparison`, `successful_pathway_distribution` | Both responses / Reviewer 2 |

Existing unrelated assets on main are retained but not regenerated. The response
screenshots of applicability and uncertainty tables have editable CSV and LaTeX
sources; they are not duplicated as another figure collection. The successful
pathway table also has its existing standalone LaTeX preview. Compile it from
`paper/tables/` with `pdflatex successful_pathway_distribution_preview.tex`.
The two new table fragments require `booktabs` and `tabularx`.

## Validation

```sh
.venv/bin/python -m pytest --cov=snowpyt_mechparams --cov-branch --cov-report=json:coverage.json
.venv/bin/python tools/check_method_coverage.py coverage.json
.venv/bin/python -m sphinx -b html -W --keep-going docs docs/_build/html
```

The boundary and diagnostic fixtures check numerical domains, unit conventions,
exact matching, first-failure partitions, interval overlap, and local figure
exports. Report fresh test counts and timings from this branch, not PR-15's
counts. See `MANUSCRIPT_HANDOFF.md` for changes to make in the separate documents.
