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

The Monte Carlo checks use Gaussian perturbations, a fixed seed, and
20,000 draws per case/pathway/correlation condition. Correlations
0, 0.5 and 1 are hypothetical shared-observer scenarios within a measurement type,
not estimated population correlations. Different measurement types are independent;
the same raw draw is reused across pathways and one slope observation is shared.
Physical-input, method-domain and numerical failures are reported separately.
No draw is clipped, replaced or resampled. Successful-draw summaries are conditional
where draws fail; comparing them directly with unconditioned first-order standard
deviations also reflects selection. Boundary-case success fractions range from
49.3% to 50.7%.
These checks quantify limitations without replacing the production uncertainty engine.
The current density functions reconstruct ufloats; correlated scenarios therefore
operate on shared raw samples rather than assuming those outputs retain covariance.

Selected controls with independent layers (density in kg m⁻³, modulus in MPa,
D11 in N mm; Monte Carlo standard deviations are conditional on successful draws):

| case | pathway | first_order_sigma | conditional_std | success_fraction |
| --- | --- | --- | --- | --- |
| linear_density | Geldsetzer | 30.82 | 30.0641 | 0.9938 |
| nonlinear_density | Geldsetzer | 33.82 | 36.9328 | 0.9987 |
| nonlinear_density | Kim T2 | 37.3302 | 37.7437 | 0.9998 |
| kim_t6_grain_size | Kim T6 | 39.5831 | 33.5423 | 0.8929 |
| homogeneous_D11 | Measured / Wautier / Köchle | 71136648.8044 | 72411531.3915 | 1.0 |
| layered_D11 | Measured / Wautier / Köchle | 481200623.8231 | 487887319.8582 | 1.0 |
| layered_D11 | Measured / Bergfeld / Köchle | 64888740.7496 | 64330277.1888 | 0.9828 |
| kochle_breakpoint_250 | Measured / Köchle | 26.0069 | 38.2201 | 0.9999 |

Across the selected D11 case–pathway pairs, the conditional standard-deviation ratio
for inter-layer correlation 1 versus 0 ranges from 0.925
to 1.327. These are scenario sensitivities, including
changes in domain-crossing selection, rather than empirical correlation estimates.

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
“dominates by ~12x” heuristic is removed. Paired Monte Carlo difference summaries
use the same raw observations across pathways.

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

The recorded validation run passed 841 tests. The 17 checked method/dispatcher modules and 59 named functions attained 100% statement and branch coverage. Across the entire package, coverage was 90.86% of statements and 81.63% of branches. The independent notebook verified 36 pathways on 394 selected slab–pathway cases (3,037 numeric comparisons and 4,711 matched unavailable outputs), plus homogeneous and layered D11 examples. Documentation, method-catalog, lint, notebook and LaTeX-table checks passed. See `validation.json` for the recorded scope.

On the recorded machine, corrected parsing and slab construction took
13.06 s and full-cohort execution of all
three targets took 101.80 s.
Deterministic subset execution timings (seconds; three repeats, fresh engine,
uncontrolled warm filesystem cache) were:

| slabs | count | min | median | max |
| --- | --- | --- | --- | --- |
| 100 | 3 | 0.56 | 0.566 | 0.584 |
| 1000 | 3 | 6.252 | 6.657 | 6.866 |

Auditing, each diagnostic target and rendering are timed separately in the saved
metadata. These measurements do not establish operational or real-time suitability.

The PR intentionally does not add a stability-model demonstration, mixed density
methods within one production pathway, an optimal-pathway recommendation, wet-snow
parameterizations, or a new production uncertainty engine.
