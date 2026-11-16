# Reviewer response support

These are suggested responses and evidence from the pinned repository baseline
and corrected implementation. They do not modify the manuscript or Word responses.
All statistical comparisons below are descriptive, with repeated ECTP slabs retained.

## Applicability corrections — R2 major 3

We corrected Wautier's implementation to accept precipitation particles and applied
Schöttner's grain-specific inclusive nominal-density limits. Jakob Schöttner supplied
observed volume-fraction extrema in author correspondence: SH 0.074–0.191,
DF/RG 0.162–0.388, and FC/DH 0.164–0.505. Multiplication by his specified
916.7 kg m⁻³ gives 67.8358–175.0897, 148.5054–355.6796, and
150.3388–462.9335 kg m⁻³. Thresholds are unrounded internally. These bounds
describe the observed calibration domain, not demonstrated accuracy throughout it.
The equations retain their existing 917 kg m⁻³ normalization. Köchle melt-form
support remains a qualified implementation choice because the source describes
distinct melt-form behavior without a separate fit.

## Coverage — R1 coverage comment; R2 major 5

The starting cohort remains 14,776 slabs from
12,347 contributing pits. Union coverage
counts slabs reached by at least one pathway; it is not the maximum individual
pathway coverage. Individual changes are visible even where union coverage stays constant.

| Target | baseline | corrected | contained |
| --- | --- | --- | --- |
| Shear weight | 5535 | 5535 | 5535 |
| Shear weight + elastic inputs | 772 | 772 | 772 |
| D11 | 823 | 823 | 823 |

Changed individual-pathway counts:

| target | pathway | baseline | corrected | corrected_minus_baseline |
| --- | --- | --- | --- | --- |
| D11 | Kim T2 / Schöttner / Köchle | 735 | 625 | -110 |
| D11 | Geldsetzer / Schöttner / Köchle | 732 | 694 | -38 |
| D11 | Geldsetzer / Schöttner / Srivastava | 448 | 421 | -27 |
| D11 | Kim T2 / Wautier / Srivastava | 445 | 450 | 5 |
| D11 | Measured / Schöttner / Köchle | 17 | 14 | -3 |
| D11 | Measured / Schöttner / Srivastava | 12 | 11 | -1 |
| Shear weight + elastic inputs | Kim T2 / Schöttner / Köchle | 687 | 580 | -107 |
| Shear weight + elastic inputs | Geldsetzer / Schöttner / Köchle | 684 | 647 | -37 |
| Shear weight + elastic inputs | Geldsetzer / Schöttner / Srivastava | 418 | 393 | -25 |
| Shear weight + elastic inputs | Kim T2 / Wautier / Srivastava | 415 | 420 | 5 |
| Shear weight + elastic inputs | Measured / Schöttner / Köchle | 17 | 14 | -3 |
| Shear weight + elastic inputs | Measured / Schöttner / Srivastava | 12 | 11 | -1 |

The `*_first_failure_classes.csv` tables partition failed attempts at their first
unsuccessful requirement into combinations of missing observations, processing
exclusions, unsupported grain forms and numerical-domain limits. Each attempt is
counted once. Detailed reason counts overlap and must not be summed. Stage loss
percentages use the original cohort denominator. Shear weight with elasticity is
an availability requirement for shear weight plus E and ν in every layer.

## Density matching and cohort audit — R2 major 4

The export contains 19,118 density observations and
371,429 stratigraphic layers. 10,468
observations have normalized intervals exactly matching a layer;
8,650 observations have no usable
positive-thickness interval. 8,481
of those point records can be located by depth in a layer, but their sampling
extent remains unknown. The alternative policy retains exact matches and assigns
only a single valid positive-thickness sample wholly contained in one unambiguous
layer. It does not interpret a depth-only observation as a representative layer mean.
The policy counts and partial coverage fractions are retained in the layer audit.
See `coverage_comparison.csv` for its effects; zero differences are valid results,
not evidence that all excluded density records lack potential scientific value.

The audit found 16 duplicate-content excess
files and 16 duplicate-ID excess records. No new
deduplication or quality filtering was applied. 2,113
pits yield multiple slabs, including 1,265
additional occurrences of identical observed slab stratigraphy within a pit.
These are not independent observations. Slab-construction exclusions were
{'failure_depth_outside_layers': 283, 'no_overlying_layer': 197}. A failure belongs to the first layer satisfying
top ≤ failure depth < bottom; the whole containing layer is omitted from the slab.
Checks reported here are local audits, not claims about SnowPilot website validation.
There is no new wetness screening and no claim that all selected observations are dry.

## Assigned uncertainty — R1 uncertainty comments; R2 major 6

Suggested replacement table (assigned symmetric standard deviations for the
first-order calculation, rather than demonstrated coverage intervals):

| Observation | Assigned standard deviation | Basis and limitation |
| --- | --- | --- |
| Direct density | 10% of magnitude | Existing literature-informed assumption |
| Slope angle | 2° | Existing observational assumption |
| Hand hardness index | 0.67 | Two subclasses; F−=0.67, K+=5.33, I+=6.33 |
| Grain size | 48% of magnitude | Symmetric approximation to asymmetric −48%/+122% bounds |
| Layer thickness | 5% of magnitude | Existing observational assumption |

The proposed grain-size bounds are asymmetric. A ufloat carries a single symmetric
standard deviation and first-order derivatives, so we assign 48% of recorded grain
size symmetrically. This uses the lower relative width and does not reproduce the
upper +122% bound or the underlying percentile distribution. It is a modeling
approximation, not a newly established measurement-error distribution. Other
assumed ranges are likewise used as assigned standard deviations. Grain-form
misclassification and empirical parameterization uncertainty are excluded.
Validity and the Köchle branch are evaluated at nominal density; uncertainty
crossing a boundary is not truncated. Uncertainty need not grow monotonically
along a calculation pathway.

## Limited propagation checks — supplementary evidence

This is a limited assessment of the current first-order approximation, not a new
production uncertainty engine or population-wide validation. Cases comprise a linear
density control, homogeneous/layered D11 controls, the three D11 spread-quantile
illustrations (30th, 60th and 90th percentiles), and the first multilayer slab by
slab ID with a successful Kim T6 D11 pathway, where available. All nominally successful
D11 pathways for each selected real slab are retained; none are selected by agreement
with Monte Carlo. Exact inputs, selections and seeds are in
`corrected/monte_carlo_cases.json`; pathway-level results are in `corrected/monte_carlo.csv`.

Each condition uses 20,000 Gaussian raw-input draws with the assigned
standard deviations above. Independent-layer results are compared with first-order
estimates. Different measurement types are independent; raw observations are shared
across pathways. Measured layer tops remain fixed while thicknesses vary. Physical-input,
method-domain and numerical failures are counted separately. No draw is clipped,
replaced or resampled. All Monte Carlo summaries below condition on successful draws:
smaller standard deviations after rejection do not establish that first-order
propagation overestimates uncertainty. Neither method establishes empirical accuracy.

### Table S1 Independent-layer comparison

SD ratio is conditional Monte Carlo SD / first-order SD. Ranges and medians summarize
all evaluated pathways within each case, not pooled slabs. Numerical summaries,
including mean ratios, are in `corrected/monte_carlo_comparison.csv`.

| Case | Layers | Pathways | SD ratio: median [min, max] | Successful draws: min–max |
| --- | --- | --- | --- | --- |
| Homogeneous D11 control | 1 | 1 | 1.018 [1.018, 1.018] | 100.0%–100.0% |
| Layered D11 control | 2 | 2 | 1.003 [0.991, 1.014] | 98.3%–100.0% |
| Linear density control | 1 | 1 | 0.975 [0.975, 0.975] | 99.4%–99.4% |
| 1057_slab_0 | 1 | 16 | 0.991 [0.755, 1.641] | 80.1%–97.7% |
| 14909_slab_0 | 1 | 16 | 1.651 [1.092, 2.628] | 52.0%–100.0% |
| 29863_slab_0 | 2 | 18 | 0.648 [0.408, 0.915] | 32.5%–91.0% |
| 50003_slab_0 | 2 | 16 | 1.023 [0.794, 1.680] | 41.2%–97.5% |

Across the 66 pathway comparisons for 4
selected real slabs, SD ratios range from 0.41 to
2.63; 38
differ from one by more than 20%. Agreement for simple controls therefore does not
establish adequacy for the selected nonlinear pathways. These cases are illustrative,
and repeated pathways and slabs are not independent observations.

Boundary checks use measured density with 10% SD. For Köchle, conditional MC/first-order
SD ratios are 0.33× at 249, 1.47× at 250, 1.45× at 251 kg m⁻³. Production selects the branch at nominal
density; MC evaluates the branch separately for each draw. At the six Schöttner
grain-group endpoints, 49.3%–50.7%
of draws succeed. The latter comparisons reflect both nonlinearity and selection
at the calibration limits. These checks remain in the raw results without a separate figure.

### Table S2 Multilayer correlation sensitivity

Correlations 0.5 and 1 are hypothetical shared-observer scenarios within each
measurement type across layers. SD ratio here is correlated MC SD / independent MC SD
for the same case/pathway; Table S1 supplies the independent success fractions.
Only multilayer D11 cases are evaluated. Single-layer slabs have no inter-layer
correlation to vary. Numerical summaries are in `corrected/monte_carlo_correlation.csv`.

| Case | Layers | Pathways | Correlation | SD ratio: median [min, max] | Successful draws: min–max |
| --- | --- | --- | --- | --- | --- |
| Layered D11 control | 2 | 2 | 0.5 | 1.152 [1.140, 1.164] | 97.9%–100.0% |
| Layered D11 control | 2 | 2 | 1 | 1.284 [1.264, 1.304] | 98.2%–100.0% |
| 29863_slab_0 | 2 | 18 | 0.5 | 1.137 [1.104, 1.168] | 39.7%–91.6% |
| 29863_slab_0 | 2 | 18 | 1 | 1.256 [1.166, 1.327] | 48.5%–93.0% |
| 50003_slab_0 | 2 | 16 | 0.5 | 1.097 [1.069, 1.184] | 40.1%–97.6% |
| 50003_slab_0 | 2 | 16 | 1 | 1.113 [0.925, 1.260] | 38.8%–97.6% |

These are scenario sensitivities, including changes in domain-crossing selection,
not estimated population correlations. Density methods rebuild ufloats, so the
correlated checks operate on raw observations rather than assuming covariance
survives the production interfaces.

### Suggested response to Reviewer 1 major comment 8

We agree that first-order propagation and the independence assumption require
qualification. We added limited Monte Carlo checks for the Figure 10 examples,
a multilayer Kim T6 example, and simple controls (Table S1). Some nonlinear pathways
show substantial differences despite close agreement for simple controls. We also
tested hypothetical inter-layer correlations of 0.5 and 1 for multilayer cases
(Table S2). For the selected real multilayer cases, correlation 1 versus 0 changes
conditional SD by factors of 0.93–1.33.
These sensitivities include changes in which draws remain applicable and do not
estimate observer correlations. We retain first-order propagation and will describe
its outputs as approximate propagated measurement SDs, conditional on the selected
relationships and assigned input uncertainties. Negative lower error-bar endpoints
indicate a limitation of the symmetric approximation, not physically negative D11.
A general Monte Carlo implementation remains future work.

### Suggested response to Reviewer 2 major comment 6

We added the assigned-uncertainty table and a limited numerical assessment of
first-order propagation (Tables S1–S2), with specified Gaussian input distributions,
recorded seeds, and explicit failure counts. Across the selected real-slab pathways,
conditional MC/first-order SD ratios span 0.41–2.63.
We also checked the Köchle breakpoint and Schöttner calibration endpoints. In production,
applicability and branch selection use nominal inputs; uncertainty extending beyond
a boundary is not clipped. In the checks, each draw is evaluated separately and
reported statistics condition on successful draws. We will explicitly state the
independent-layer assumption, fixed measured tops with uncertain thicknesses,
and the shared observations across pathways and repeated ECT slabs. Grain-form
misclassification and parameterization uncertainty remain excluded. These checks
qualify interpretation of the current approximation; a general Monte Carlo engine
is deferred. The 78.4% statistic is defined below as a pooled median over
slab–pathway pairs, rather than a median of per-slab medians.

## D11 comparison and interpretation — R1 Figures 9–10; R2 major 6–7

The corrected top-16 common subset contains 316 slabs from 283
pits; 257 slabs have one layer. Grain-form combinations
in this subset are ['RG']. There are 395
layer occurrences representing 351 distinct source
layers, and 29 repeated slab stratigraphies
within pits. The pooled median relative propagated
measurement uncertainty is 78.44%, with IQR
55.84%–85.16%, across 5,056 slab–pathway values.
This is not a median of per-slab medians. Per-slab summaries are provided separately.
The median max/min spread is 31.778, with range
25.699–62.966 and 90th percentile
62.966.

Across the full common subset, the median absolute range divided by the largest
full ±1σ interval width is 0.867.
The median fraction of the 120 pathway pairs with disjoint ±1σ intervals is
50.0%; 316
slabs have at least one disjoint pair. This describes interval separation, not
statistical significance or pathway accuracy. There are
1,044 negative lower interval endpoints; these remain
visible as a limitation of the uncertainty approximation. The previous aggregate
“dominates by ~12x” heuristic is removed. These first-order interval summaries do
not validate the error bars or establish that pathway spread generally dominates
measurement uncertainty.

Suggested response to Reviewer 1's comment on lines 377–382: We extended the
descriptive comparison to all 316 common-subset slabs, using all 120 pathway pairs
per slab. The median range/largest full ±1σ width is
0.867, and the median fraction of disjoint
interval pairs is 50.0%. We will replace the
claim that pathway differences far exceed measurement uncertainty with these
qualified comparisons. They use approximate first-order error bars and are not
significance tests. Uncertainty need not increase monotonically along a pathway.

Suggested abstract replacement for the spread/uncertainty sentence: For 316
rounded-grain slabs where all 16 selected bending-stiffness pathways are valid,
nominal estimates vary by a median factor of 31.8.
The pooled median relative first-order propagated measurement SD is
78.4%; these approximate uncertainties exclude parameterization
uncertainty and are sensitive to nonlinear propagation and dependence assumptions.

Reproducibility discrepancy: rerunning the requested baseline revision gives
316 common slabs, whereas the previously
saved D11 notebook/manuscript reported 317. This discrepancy predates this PR;
the pinned baseline is the comparator, and historical notebook outputs are not
treated as fresh execution evidence. `comparison.json` records both newly ranked
and original-pathway comparisons and membership changes.

The stiffness calculation uses an upward-positive z coordinate, with reference
depth equal to the first layer top plus half the sum of layer thicknesses. Measured
layer tops remain fixed while thickness uncertainty propagates. Gaps are retained,
so this reference is not the midpoint of the bounding interval in a gapped profile.
The reference plane is not generally the stiffness-weighted neutral axis. D11 is
reported in N mm (divide by 1000 for N m). Reversing coordinate orientation with
consistent integration limits leaves D11 unchanged. Observation orientation is
unknown; no unsupported vertical-to-slope-normal conversion is made.

## Verification and reproducibility — R1 verification; R2 minor 6

Run `.venv/bin/python paper_analysis/run_review.py` from the repository, then
execute `paper_analysis/hand-verification.ipynb`. A `--smoke` run writes separate
outputs. The pinned baseline is extracted into a temporary directory; raw data
remain unchanged. Input checksums, source hashes, environment versions, stage
times and repeat timings are saved alongside the results. Graph calculation and
method-domain verification establish implementation agreement, not empirical
accuracy.

The earlier validation run at `eb53d7453b8ff406cfd934cb7d3307d55a39ab12` passed 841 tests. The 17 checked method/dispatcher modules and 59 named functions attained 100% statement and branch coverage. Across the entire package, coverage was 90.86% of statements and 81.63% of branches. The independent notebook verified 36 pathways on 394 selected slab–pathway cases (3,037 numeric comparisons and 4,711 matched unavailable outputs), plus homogeneous and layered D11 examples. Documentation, method-catalog, lint, notebook and LaTeX-table checks passed. See `validation.json` for the recorded scope.

For this limited-propagation revision, 848 tests passed. Fresh checks and source hashes are recorded separately under `limited_propagation_revision`; historical coverage measurements above have not been relabeled as a new measurement.

On the recorded machine, corrected parsing and slab construction took
14.97 s and full-cohort execution of all
three targets took 106.22 s.
Deterministic subset execution timings (seconds; three repeats, fresh engine,
uncontrolled warm filesystem cache) were:

| slabs | count | min | median | max |
| --- | --- | --- | --- | --- |
| 100 | 3 | 0.641 | 0.645 | 0.654 |
| 1000 | 3 | 6.926 | 7.267 | 7.531 |

Auditing, each diagnostic target and rendering are timed separately in the saved
metadata. These measurements do not establish operational or real-time suitability.

The PR intentionally does not add a stability-model demonstration, mixed density
methods within one production pathway, an optimal-pathway recommendation, wet-snow
parameterizations, or a new production uncertainty engine.
