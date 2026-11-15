# Reproducing reviewer-response evidence

This workflow compares pinned revision
`c8b712e93fe219c9c5dd71e6a5a8a3a6d947866c` with corrected methods and an
analysis-only contained-density policy. It never edits the manuscript or Word
responses. Use Python 3.13 and the repository lockfile (safe archive extraction
in the runner requires Python 3.12+):

```bash
uv sync --locked --extra dev --extra io --extra docs
.venv/bin/python paper_analysis/run_review.py --smoke
.venv/bin/python paper_analysis/run_review.py
```

Smoke mode uses the first 1,000 sorted XML files and 1,000 Monte Carlo draws and
writes `results/smoke/`. Full mode uses all 50,278 files and 20,000 draws per
case/pathway/correlation condition. Baseline source is extracted from Git into a
temporary directory and executed in a separate process with the same dataset and
analysis definitions. No runtime method override emulates the baseline.

Execution is sequential: baseline, corrected, contained comparison, audits/loss
diagnostics, Monte Carlo, and rendering. Parsing, calculation, audit, diagnostics
and rendering are timed separately. Benchmarks use stable slab-ID ordering with
100/1,000 slabs and three repeats, with a fresh engine per run; shared calculations
within a slab may be cached. Timings do not establish real-time operational fitness.
The OS file cache is uncontrolled and warmed by preceding runs; it is not flushed.
Baseline diagnostics use the pinned source equations and their original domains
(no Schöttner density restriction, no Wautier PP), while corrected diagnostics and
figures use the shared current domains. Diagnostic compatibility definitions do
not alter the archived numerical implementation.

Deliberate partial reruns are supported:

```bash
.venv/bin/python paper_analysis/run_review.py --steps diagnostics mc render
```

Partial runs require earlier cached results. Use a full run after changing methods,
parsing or calculation policies. Recorded source hashes distinguish the exact
working tree from its recorded Git revision; stage metadata identifies what ran.

## Outputs

- `results/reviewer_response_support.md`: suggested response wording, uncertainty
  table and fresh results mapped to reviewer comments.
- `results/comparison.json` and `coverage_comparison.csv`: individual/union
  coverage, original/new top-16 pathways and common-subset membership changes.
- `results/input_manifest.json.gz`: deterministic compressed filenames, pit IDs
  and SHA-256 checksums, including files that fail parsing.
- `results/{baseline,corrected,contained}/`: compact coverage/D11/audit summaries,
  slab/test identifiers, selected cases and benchmark evidence.
- `results/figures/`: reproducible PDF/PNG response-support figures.
- `results/corrected/monte_carlo*.csv`: conditional summaries, failure counts and
  paired differences computed from shared observations.

Parquet attempt tables, observation/layer ledgers and verbose profile audits are
untracked and regenerated. Raw Monte Carlo draws are not persisted; case definitions
and seeds reproduce them. The layer ledger records sample-coverage fractions and
assignment decisions. Commit compact evidence rather than these caches.

Execute `hand-verification.ipynb` top to bottom after the pipeline. It retains
independent coefficients and analytical derivatives; compact saved text summarizes
the checks and detailed HTML worked examples regenerate on execution.
`examples/D11_analysis.ipynb` presents canonical pipeline results without duplicating
aggregation logic. `loss-analysis.ipynb` loads canonical diagnostics, preserving
raw density-processing provenance. `reviewer_evidence.ipynb` presents audits,
Monte Carlo results, correlation checks, and timings from the same outputs.

To regenerate the notebook presentations and legacy repository-local paper assets:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 examples/paper_diagrams.ipynb examples/slab_weight_inputs.ipynb paper_analysis/loss-analysis.ipynb examples/D11_analysis.ipynb paper_analysis/reviewer_evidence.ipynb
```

LaTeX table previews can be compiled with `pdflatex` from `paper/tables/` after
the loss notebook.
Saved notebook outputs are compact; full HTML worked examples regenerate on execution.

## Policies

Exact matching remains the production default. The sensitivity policy preserves
original exact matches and their first-match behavior. Otherwise it accepts one
finite positive-density, positive-thickness sample wholly contained in one layer.
Units are normalized, with no added tolerance. Multiple candidates, crossing
intervals, overlapping-layer ambiguity and depth-only samples are not assigned.

Sample, layer, pit, slab and slab–pathway counts have separate denominators.
Detailed causes overlap; first-failure combinations form an exclusive partition.
Legacy coarse plots group processing exclusions with unavailable observations;
the new reason-class tables/figures separate them explicitly. Audits do not newly
filter, deduplicate, repair geometry, select one ECT per pit or screen wetness.

Gaussian distributions and correlations 0/0.5/1 are sensitivity assumptions.
Correlations operate within measurement type across layers; types remain
independent. The same raw observations are shared across pathways, and slope is
shared within each slab. Geometry retains fixed measured tops and uncertain
thicknesses. Draws are never clipped, replaced or resampled. Physical-input,
method-domain and numerical failures partition draws with successes. Successful
draws require positive finite used observations, measured density at most 917
kg m⁻³, hardness within 0.67–6.33, and slope in 0–90° when used. These physical
input checks precede the separately implemented calibration-domain checks. Successful
draw statistics are conditional where rejection occurs, so differences from
first-order estimates also reflect selection. Production density functions rebuild
ufloats; correlated sensitivity therefore uses raw draws rather than assuming
arbitrary covariance survives the calculation interfaces.

D11 interval separation is descriptive, not a significance test or empirical
accuracy assessment. Repeated slabs and shared inputs are not independent samples.
Method uncertainty remains disabled in the primary analysis. Validity checks and
Köchle branch selection use nominal values, without uncertainty clipping.

## Validation

```bash
.venv/bin/python -m pytest --cov=snowpyt_mechparams --cov-branch --cov-report=json:coverage.json
.venv/bin/python tools/check_method_coverage.py coverage.json
.venv/bin/python -m sphinx -b html -W --keep-going docs docs/_build/html
```

The checker requires >98% statements and branches separately per method module
and function. Report fresh counts and measured coverage, not the historical
“780 tests / 100%” claim. Vectorized Monte Carlo equations are compared against
scalar implementations across density coefficient groups and elastic grain/method
combinations, including rejected boundaries. Scientific sensitivity outcomes are
reported, not forced to agree with first-order propagation.

## Behavior changes in this PR

Wautier now accepts PP and its subclasses. Schöttner now rejects nominal densities
outside the author-supplied grain-specific calibration intervals. The parser assigns
grain-size standard deviations of 48% of magnitude; the legacy 0.5 mm constant remains
available but is no longer used by parsing. Default figure destinations are local.
Public calculation signatures, return types, parser entry points, target names and
primary exact density matching are preserved.
