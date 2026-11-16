# Manuscript and reviewer-response handoff

The code PR does not edit the submitted manuscript, the manuscript repository,
or the attached Word responses. Apply the agreed prose restructuring and editorial
changes there, using the evidence index in this directory and the canonical
repository-local figures. These notes identify factual reconciliation needed in
addition to the already drafted responses.

- Replace remaining 317/258 common/single-layer counts with 316/257. All common
  slab layers resolve to RG. Fresh pinned baseline also gives 316; do not describe
  this correction as attrition caused by the new Schöttner limits.
- Use 5,056 results for the pooled relative measurement SD: median 78.44%, IQR
  55.84–85.16%. This is not a median of per-slab medians. Median max/min spread is
  31.78; range is approximately 25.70–62.97 and the 90th percentile is 62.97.
- Replace claims that pathway spread far exceeds measurement uncertainty with
  the descriptive full-subset comparison: median range/largest full ±1 SD width
  0.867, median disjoint pair fraction 50%, 1,044 negative lower endpoints, and
  at least one disjoint pair for every common slab. Neither interval separation
  nor the three illustrations establishes significance or pathway accuracy.
- The embedded uncertainty table currently shows −48%/+122% and calls uncertainty
  a plausible range. The implementation uses **symmetric SD = 48% of magnitude**.
  Clearly distinguish the asymmetric source percentiles from this assigned SD.
  Grain-form identification error is not quantified by a dropdown or propagated.
- Correct the hand-hardness example: 4F− = 1.67, **4F = 2**, 4F+ = 2.33. F = 1;
  K = 5 and I = 6. The implementation's supported index range reaches I+ = 6.33,
  not K+ = 6.33. Two subclasses correspond to assigned SD 0.67.
- Coverage numerators and the 14,776 denominator count **slabs**, not unique pits.
  There are 12,347 contributing pits and 2,113 yield multiple slabs. Keep repeated
  ECT results and acknowledge dependence rather than suggesting independent samples.
- The actual code uses upward-positive z about the first layer top plus half the
  summed thickness. This is generally not the stiffness-weighted neutral axis;
  gaps are retained. Measured tops are fixed while thickness uncertainty propagates.
  Reversing z and integration limits together preserves D11, but the response's
  claim that the code directly uses a downward-positive axis is inaccurate.
  Numerical outputs are N·mm; divide by 1,000 for N·m. No vertical/slope-normal
  observation conversion is inferred from unavailable metadata.
- Reviewer 2's opening says a limited propagation comparison was completed, while
  the detailed chosen response defers Monte Carlo and correlation sensitivity.
  Remove the opening claim and retain the stated first-order limitations.
- Use fresh verification counts and notebook timings from `reviewer_results/`.
  The worked notebook selects ten unfiltered slabs per pathway and adds successful
  witnesses where available; failures are independently checked, too. Do not call
  all selected cases successful, or reuse “780 tests”/PR-15's “841 tests”.
- Describe the actual source export dates and eleven-year duration without silently
  changing the dataset to fit a water-year convention. The responses' corrected
  October–September convention differs from the submitted September–August dates.
- Local audits find duplicate records, layer gaps/overlaps, and some implausible
  values. Avoid claiming that the SnowPilot UI guarantees their absence; describe
  the implemented checks and exclusions. No new wetness or geometry filters apply.
- Update affected Schöttner/Wautier pathway counts from `coverage_comparison.csv`.
  The best elastic-input count remains 687, but the former Schöttner tie is removed.
  The Wautier stage of the illustrated pathway retains 2,100 slabs rather than 1,901.

Figure handoff: retain the original manuscript numbering as the mapping reference,
then renumber after restructuring. Figure 3 now has one method per panel; Figure 6
shows active edges only; Figure 9 uses a shared-label ratio plot; Figure 10 uses
three side-by-side panels and symmetric approximate measurement SDs. Update their
captions accordingly. Correct the Figure 2 PST/Rutschblock caption discrepancy and
Figure 5 “slab weigh” in the separate manuscript sources. The response's uncertainty
and applicability table screenshots should be replaced using the editable tables.

Keep the agreed scientific scope: no stability-model evaluation, mixed density
strategy, wet-snow analysis, automatic best-pathway ranking, or assertion that
uncertainty/spread necessarily grows with pathway length.
