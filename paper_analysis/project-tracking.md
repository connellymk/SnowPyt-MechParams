## 261021 Notes

loss analysis nb
- Look into losses due to "Other errors"
    - All "other errors" were caused by I hand hardness (I-, I, I+). Ice forms were not included in the hhi mapping. 
    - I added [I-, I, I+] to the hhi mapping in constants.py (K=5 so I=6)
- Paper will include: Loss histograms (as a table?) and stepwise loss figures
- Clean up figures
- Stepwise loss
    - Use different color palette than methods in the paper
    - Use a color or style (hatched?) to represent "mixed causes" loss, that combines the color or style of missing measurements and validity
- Remove thickness / integrated weight step from shear weight stepwise losses (Thickness is always available so it will always be the same.)

## 261025 Loss-analysis update

- Audited both targets on all 14,776 ECTP slabs: zero first-failure attempts and zero detailed diagnostic reasons classified as "Other errors". Blocked downstream calculations remain separate. Stepwise plots now show other errors whenever nonzero.
- Removed the standalone thickness / integrated-weight reporting step for shear weight; thickness is still checked. Both targets now report the same density and shear-weight requirements before any elasticity requirements.
- Updated figure labels to the paper's method names, observation terminology, and parameter symbols. Loss colors are independent of method colors; mixed causes combine the missing-observation fill with validity-limit hatching.
- Prepared the successful-pathway distribution as a paper table (counts and percentages), retaining histograms as notebook diagnostics. Exported the full LaTeX table (all counts from 0 through 32) and full-bin CSV to both paper table directories, and the two selected-pathway stepwise figures as PDF/PNG to both paper figure directories.
- Reproduced the manuscript coverage and the Kim T2 → Wautier → Köchle sequence of 5,907 → 5,470 → 1,901 → 687 slabs. Manuscript integration remains a separate editing step.

- Added `successful_pathway_distribution.pdf` / `.png`: two mechanical-target panels, each pairing the full count/percentage table with horizontal bars on the same 0–15,000 slab scale. The figure is also displayed in the loss-analysis notebook.

- Updated the stepwise figures as horizontal bars: method names in the title are followed by their calculated parameter in parentheses; axis labels contain parameters without method names and use "Join:" for combined inputs. A final target bar shows the successful output count with zero additional losses.

- Combined the horizontal stepwise loss charts in `loss_stepwise_comparison.pdf` / `.png`, with a shared slab-count scale, matched bar heights and final-target positions, and one legend; standalone exports remain available.

- Removed the duplicate final-target bar from shear weight (standalone and combined); the elasticity target retains its final zero-loss bar.

- Added percentages beside stepwise loss counts, using the starting cohort as the denominator for every step (including the final 0.0% loss); the legend states this denominator.
