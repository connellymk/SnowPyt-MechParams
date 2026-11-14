# Evidence for the reviewer responses

This analysis supplements the reviewer-response copies. It does not edit either
manuscript or replace the original notebooks. Successful execution describes the
implemented calculation policy; it does not establish physical validity.

## Reproduce

Use the repository environment and `uv.lock`. From the repository root:

```sh
.venv/bin/python paper_analysis/reviewer_response_analysis.py --output paper_analysis/reviewer_response_results
.venv/bin/python paper_analysis/reviewer_uncertainty.py --output paper_analysis/reviewer_response_results
.venv/bin/python paper_analysis/reviewer_historical_check.py paper_analysis/reviewer_response_results
.venv/bin/jupyter nbconvert --to notebook --execute paper_analysis/hand-verification_reviewer.ipynb --inplace
.venv/bin/python -m pytest --cov=snowpyt_mechparams --cov-branch
```

The first script requires the fixed `examples/data/*.xml` cohort. It checks the
50,278-file and 14,776-slab counts; `input_manifest.csv.gz` identifies each file
by SHA-256, parsed ID, and recorded date. `ectp_selection.csv.gz` records every
propagating ECT, its inclusion/exclusion, source index, and resulting slab ID.
An empty input or a different cohort should be investigated, not silently accepted.

The retained notebook is a **copy** with PP added to its independent Wautier
table and the currently supported I−/I/I+ numeric hardness codes included. Its
coefficients and uncertainty equations are written independently of the library.
It verifies 36 pathways on 394 selected slab–pathway cases, including ten
unfiltered examples per pathway and a successful witness wherever available.
The completed run gives 3,073 numerical comparisons (each checks nominal value
and SD) and 4,697 matched unavailable outputs, with tolerances 1e-10 relative
and 1e-12 absolute. This is not manual verification of every slab in the cohort.

## Corrections and numerical results

- Wautier et al. (2015), Figure 2, includes PP. Its omission in the implementation
  had no source-supported justification. PP and its subclasses now use the same
  equation and nominal density restriction, 103–544 kg m−3. That interval is the
  pooled sample envelope, not validation of every grain type throughout it.
- The PP correction adds five successful slab–pathway combinations for each of
  elastic-input availability and D11. Union coverage remains 772 and 823 slabs,
  respectively. Shear-weight coverage is unchanged (best 5,470; union 5,535).
- Current code produces 316 slabs common to the 16 highest-coverage D11 pathways;
  257 have one layer, and all layer parent grain classes are RG. There are 5,056
  slab–pathway values. Median max/min spread is 31.778 (range 25.699–62.966).
  The median of SD/abs(D11), pooled over these values, is 0.78435 (IQR
  0.55844–0.85159). Slabs sharing a pit are not independent replicates.
- The original saved notebook's 317-slab result came from a measured-density
  fallback removed by commit `88cd4811`. `reviewer_historical_check.py` restores
  that behavior **only inside its diagnostic process**, then restores the normal
  dispatcher in a `finally` block. It reproduces exactly 8,858 successful D11
  attempts and 317 common slabs after also masking the original PP exclusion.
  There are 141 fallback-dependent attempts on 20 slabs. The production code
  continues to require the selected density method to succeed.
- JSON fields named `original` in `summary.json` mean current code **before the
  PP correction**, not the saved manuscript notebook. The separate historical
  check distinguishes these baselines.

The same geometric reference is used in every pathway. With recorded top depths
`d_i` and thicknesses `h_i`, the reference depth is `d_0 + sum(h_i)/2` and z is
positive upward. For contiguous layers this is the geometric midplane, not
necessarily the elastic neutral axis. E in MPa and lengths converted from cm to
mm give D11 in N mm; multiply by 0.001 for N m. Density reuse and thickness reuse
within the calculation preserve the corresponding algebraic correlations.

## Data processing audit

The primary analysis preserves the original file cohort and processing policy.
It does not add a date, wetness, duplicate-record, geometry, or density-positivity
filter. This is explicit to avoid silently changing the study population.

- The nominal export interval in the manuscript spans 11 years, not 10. However,
  42 recorded dates predate 2014-09-01 and 21 records have no date. Available dates
  range from 1998-12-17 to 2025-08-26. A manifest, not a date-only query, defines
  the reproducible cohort.
- There are 17 records without a pit ID. These are identical exports with no
  layers and contribute no slabs; there are no duplicate nonempty pit IDs. In
  total 131 parsed records have no layers. The 14,776 slab IDs are unique and
  come from 12,347 pits; 2,113 pits contribute multiple slabs.
- Of 15,256 propagating ECT records, 283 lack a matching recorded layer and 197
  have no overlying layer. Layer membership uses `top <= failure_depth < bottom`,
  with no tolerance. The entire containing weak layer is omitted; an internal
  failure does not truncate that layer. Repeated tests remain separate slabs.
- The all-layer audit finds 15 adjacent gaps and 21 overlaps; no layer has a
  missing top or nonpositive/missing thickness. These are diagnostics, not
  evidence that all source observations passed research-grade quality control.
- Of 19,118 density observations, 10,468 match exact depth and thickness records;
  the remaining 8,650 lack usable sample geometry. There are no additional
  positive, finite, explicitly bounded samples wholly contained within a layer.
  Exact matching compares the recorded units as well as numerical values.
- The alternative gives exact matches priority; otherwise it thickness-weights
  non-overlapping, positive, finite samples wholly contained in a layer. A
  crossing sample is excluded and an overlapping contained set is rejected.
  The tested alternative changes zero layers/slabs and therefore no coverage.
  A point sample without thickness cannot receive a thickness weight without
  another representativeness assumption. This result does not establish that
  exact matching is universally preferable.
- Seventy-one density observations are nonpositive or nonfinite. The positive
  candidate rule is used only for the alternative; it does not retroactively
  clean the baseline. The candidate count of 10,425 exact positive records is
  therefore distinct from the parser's 10,468 exact matches.
- Wetness is not screened: 10,894 slabs have no layer wetness codes, 2,154 have D
  on every layer, 585 have only D and missing codes, and 1,143 have at least one
  non-D code. The cohort must not be described as a verified dry-snow population.

`detailed_funnel.csv` counts disjoint combinations of missing observations,
unsupported grain forms, and numerical restrictions at the **first** failed step
of Kim T2 → Wautier → Köchle. Counts sum to 14,776. Surviving counts are
5,907 → 5,470 → 2,100 → 687. The staged order is a reporting convention, not a
claim that the graph's independent branches execute in that order. Other method
reason files retain overlapping causes; their rows must not be summed as unique
slabs without deduplication.

## Applicability sensitivity

- Köchle and Schneebeli (2014) include MF samples but note their distinct grouping
  and give no separate MF E fit. MF support is retained as an implementation
  assumption. Neither implemented Poisson-ratio method accepts MF, so removing
  MF from this E method changes no complete elastic-availability or D11 result.
  It can matter for E-only targets, which are not claimed invariant.
- Köchle's equation text and Figure 3 caption give different density intervals.
  The implementation follows the equation text: 150–250 and 250–450 kg m−3,
  with the upper branch selected at 250. No coefficient continuity is imposed.
- Schöttner et al. (2026), Figure 7a, p. 9, shows finite sampled ranges; its
  conclusion explicitly says the limits of validity remain uncertain. No
  numerical density limits are added to the production method. A sensitivity
  uses **approximate, outward-rounded graphical envelopes** of 140–360 for
  DF/RG, 140–470 for FC/DH, and 60–180 kg m−3 for SH. These are not precise
  digitized endpoints or author-established cutoffs. They reduce successful
  elastic-availability attempts from 8,144 to 7,986 and D11 attempts from 8,722
  to 8,558, leaving the respective union counts (772 and 823) unchanged.
- Bergfeld's 110–363 kg m−3 sample envelope describes mean slab densities. Its
  per-layer use here is an implementation restriction, not independent
  calibration of every layer in that interval.

## Uncertainty experiments and interpretation

The assigned values are **assumed SDs**: density 10%, thickness 5%, slope 2°,
grain size 0.5 mm, and hardness index 0.67. They are illustrative, not calibrated
observer-error distributions. Grain-form misclassification, spatial variability,
and model/parameterization error are not quantified. The pooled grain-size
distribution of Langlois et al. is not substituted for the error of a recorded
layer-average grain size.

`reviewer_uncertainty.py` uses 100,000 draws per scenario and seed 20261010. The
three original example pits are 1057, 50003, and 14909. Additional cases include a
three-layer synthetic slab and density boundaries at 103, 150, 200, 249, 250,
251, 363, 450, and 544 kg m−3. There are 768 scenarios. NumPy equations and
finite-difference local derivatives agree with 108 available framework D11
nominal/SD results (1e-10 and 1e-6 relative tolerances, respectively).

Normal and uniform input distributions have the same nominal means and SDs.
Uniform supports are mean ± sqrt(3) SD. Layer correlations are 0, 0.5, or 1
within each variable family; thickness and hardness/density families remain
independent. Normal draws use a shared Gaussian component; uniform draws use a
shared-versus-independent mixture with the specified Pearson correlation.
Observations are reused across E/nu/density choices; single-layer correlation
scenarios reuse identical draws because interlayer correlation cannot matter.

Negative/nonfinite thickness or input values and densities outside (0,917) are
recorded as physical failures. Other draws violating a method restriction are
recorded separately as domain failures. No values are clipped, resampled, or
silently discarded. Reported Monte Carlo means, SDs, and 16th/50th/84th
percentiles are conditional on admissible draws. First-order estimates instead
check the nominal domain and use the derivative of the selected Köchle branch.
Consequently, differences mix nonlinearity and explicit domain conditioning;
they are not all attributable to Taylor approximation alone.

For the original three examples under independent normal inputs, the conditional
MC SD / first-order SD ratio spans about 0.80–3.23 and domain-failure fractions
span 0.065%–57.141%. These checks do not calibrate the true observation errors or
establish population-wide MC intervals. Correlation affects multilayer results;
the experiment intentionally does not claim that any chosen correlation is
empirically correct. Recorded layer tops are fixed; thickness draws also move
the reference plane. A complete shared-boundary observation model is not used.

The extrema's first-order ±1 SD intervals are disjoint in all 316 common slabs,
but matched method pairs can overlap. With density and nu held fixed, overlaps
occur in 92.09% of Bergfeld/Köchle pairs, 38.13% of Köchle/Schöttner pairs, and
100% of Bergfeld/Schöttner pairs. Each percentage uses 1,264 comparisons; these
are descriptive and correlated, not statistical-significance tests. Do not use
the old “dominates by 12×” statistic or treat ±1 SD as a confidence interval.

## Verification and runtime

The full suite passes 789 tests (no failures or skips). Numerical method modules,
their numerical helpers, and the dispatcher have 100% statement and branch
coverage; this claim does **not** apply to the entire package. The verification
notebook also checks source immutability. See `validation.json` for the recorded
summary and `environment_packages.json` for installed versions.

`summary.json` records measured times for parsing/QC, all four shear-weight
pathways, all 32 elastic-availability pathways, and all 32 D11 pathways. This run
used Python 3.13.11 on an Apple M5 Mac with warm filesystem caches. It includes
the scripts' stated diagnostics; it is a reproducible workload observation, not
a controlled benchmark or a real-time performance guarantee. At fixed pathway
inventory, work grows with profiles/layers; adding methods also grows the
number of alternatives, and operational performance must be measured separately.

## Source references

- Wautier et al. (2015), §4.1, Eq. 5 and Fig. 2:
  https://doi.org/10.1002/2015GL065227
- Köchle and Schneebeli (2014), equations and Figs. 3–4:
  https://doi.org/10.3189/2014JoG13J220
- Schöttner et al. (2026), Fig. 7 and conclusion:
  https://doi.org/10.1016/j.actamat.2025.121657
- Bergfeld et al. (2023): https://doi.org/10.5194/nhess-23-293-2023
- Gerling et al. (2017), physical distinction between P-wave modulus and E:
  https://doi.org/10.1002/2017GL075110
- Weißgraeber and Rosendahl (2023): https://doi.org/10.5194/tc-17-1475-2023
- Langlois et al. (2020): https://doi.org/10.3389/feart.2019.00347
