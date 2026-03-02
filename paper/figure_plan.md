# Figure Plan

**Last updated:** 2026-03-02
**Purpose:** Description of each planned figure for the HESS paper. Agreed before
notebooks are rerun so that output format and content targets are clear in advance.

---

## Figure 1 — Conceptual overview

**Section:** §1.1 (Introduction — mechanical models)
**File name:** `fig01`

### What it communicates
The gap this paper fills. Shows the full chain:

> Field observations → Parameterization chain → Mechanical model inputs → Stability assessment

The parameterization chain step is highlighted as the focus of this paper, motivating
why a systematic framework is needed before the methods are introduced.

### Format
- Schematic/flowchart. Full width (`figure*`).
- Vector format (PDF or EPS).
- No data from notebooks required — pure schematic.

### Design notes
- Three main boxes: (1) Field observations (hand hardness, grain form, grain size,
  slope angle, density); (2) Parameterization chain (density → E → ν → D11 via CLT);
  (3) Mechanical model (e.g., WEAC, energy-based stability model).
- Arrows connecting boxes left to right.
- Box (2) visually emphasized (bold border or distinct color) as the focus of this paper.
- Must be color-blind-friendly.
- Single sans-serif font family; fonts embedded.

---

## Figure 2 — Parameterization directed acyclic graph (DAG)

**Section:** §2.4.1 (Representing parameterizations as a directed graph)
**File name:** `fig02`

### What it communicates
The complete structure of the parameterization DAG: all parameter nodes, merge nodes,
method edges, and data flow edges. A reader should be able to trace any of the 32
pathways to D11 through this figure. The OR logic (parameter nodes) and AND logic
(merge nodes) must be visually distinguishable.

### Format
- Directed graph. Full width (`figure*`).
- Vector format (PDF or EPS).
- Two visual zones: layer-level subgraph (upper/left) feeding into slab-level
  subgraph (lower/right).

### Design notes
- Parameter nodes: rounded rectangle
- Merge nodes: different shape (e.g., diamond or filled circle)
- Measured inputs (snow_pit, hand_hardness, grain_form, grain_size, measured_density,
  layer_thickness): visually distinct from calculated outputs (density, E, ν, D11, etc.)
  — e.g., lighter fill or dashed border
- Data flow edges: unlabeled or labeled "data flow"
- Method edges: labeled with method name (e.g., "geldsetzer", "wautier", "kochle")
- Color-blind-friendly palette (test with Coblis); use Scientific colour maps 7.0
- Single sans-serif font; fonts embedded in vector output

### Data source
`src/snowpyt_mechparams/graph/visualize.py` generates a Mermaid diagram that can
serve as a structural starting point. Significant restyling needed for publication quality.

---

## Figure 3 — Coverage overview

**Section:** §3.1 (Coverage and data loss by parameterization)
**File name:** `fig03`

### What it communicates
The big-picture coverage landscape across all parameters and pathways:
- Layer-level coverage for each density, E-mod, and ν method (% of layers where
  the method applies)
- Slab-level coverage for D11 across all 32 pathways (% of ECTP slabs producing
  a valid D11 estimate)

Makes the "data loss through chaining" effect immediately visible: slab-level
coverage is substantially lower than layer-level coverage.

### Format
- Grouped bar chart or heatmap. Single or full width depending on layout.
- Consider: left panel = layer-level coverage by method; right panel = slab-level
  coverage for D11 pathways (organized as a 4×4 heatmap with density method as rows,
  E-mod method as columns, ν method as separate panels or hatching).

### Design notes
- y-axis (or color scale): coverage (% of layers or slabs)
- Organize left-to-right by parameter level (density → E-mod → ν → D11)
- Color-blind-friendly; legend inside figure
- Clearly distinguish layer-level from slab-level results (different x-axis groups or panels)

### Data source
`examples/all_density_pathways.ipynb`, `examples/all_e_mod_pathways.ipynb`,
`examples/all_poissons_ratio_pathways.ipynb`, `examples/all_D11_pathways.ipynb`.
Notebooks must be rerun with the final dataset before this figure can be created.

---

## Figure 4 — Density distributions across methods

**Section:** §3.2 (Density estimates across methods)
**File name:** `fig04`

### What it communicates
The range of density values estimated by the three estimation methods (geldsetzer,
kim_jamieson_table2, kim_jamieson_table5), alongside within-method uncertainty
propagated from input measurements. Shows that method choice produces systematic
differences in estimated density (method means differ by ~208–283 kg m⁻³) beyond
within-method uncertainty.

### Format
- Overlapping histograms or violin plots, one distribution per method.
- Single column width preferred; full width if needed for readability.
- x-axis: density (kg m⁻³). y-axis: normalized frequency or count.

### Design notes
- Three distinct colors (color-blind-friendly) for geldsetzer, kim_table2, kim_table5
- Consider showing both nominal values (no uncertainty) and uncertainty-propagated
  values side by side to illustrate the effect of uncertainty representation
- The data_flow pathway (~2.8% layer coverage) may not warrant a full distribution
  panel; report as a summary statistic in the caption or text if the sample is too small
- Legend inside figure

### Data source
`examples/all_density_pathways.ipynb`. Notebook must be rerun.

---

## Figure 5 — Young's modulus distributions across methods

**Section:** §3.3 (Young's modulus estimates across methods)
**File name:** `fig05`

### What it communicates
The large inter-method spread in E estimates (wautier ~29–69 MPa vs. kochle
~71–252 MPa) and the high within-pathway relative uncertainty (28–92%). This is the
most striking layer-level result and is the primary driver of D11 spread in §3.5.

### Format
- Overlapping histograms or violin plots, one distribution per E-mod method.
- Log scale on x-axis strongly recommended given the approximately one order of
  magnitude range across methods.
- Single or full width.

### Design notes
- Consider aggregating across density sub-pathways per E-mod method (i.e., show
  four distributions, one per E-mod method, pooling across all applicable density methods)
  OR show a representative density method and note sensitivity in the caption
- If showing all 16 pathways individually, a ridgeline plot or heatmap may be
  cleaner than overlapping histograms
- Color-blind-friendly; legend inside figure

### Data source
`examples/all_e_mod_pathways.ipynb`. Notebook must be rerun.

---

## Figure 6 — Poisson's ratio estimates across methods

**Section:** §3.4 (Poisson's ratio estimates across methods)
**File name:** `fig06`

### What it communicates
The simpler picture for ν: two methods (kochle and srivastava), largely categorical
outputs stratified by grain form, with smaller inter-method spread compared to E-mod.
Confirms that ν contributes less to D11 uncertainty than E-mod but is structurally
coupled to density method choice via the shared density node.

### Format
- Bar chart or violin plot by grain form category (RG, FC, DH, PP+DF), with kochle
  and srivastava shown side by side for each grain form.
- Single column width.

### Design notes
- x-axis: grain form category. y-axis: ν value.
- Error bars: ± reported standard error from original publication (kochle and srivastava
  each provide these).
- For srivastava, consider showing one bar per density sub-pathway or report the
  range as a note.
- **Space-saving option:** If Figures 4, 5, and 6 are individually simple enough,
  combine them into a single three-panel figure (panels a, b, c) to save manuscript
  space. Evaluate after notebooks are rerun.
- Color-blind-friendly; legend inside figure.

### Data source
`examples/all_poissons_ratio_pathways.ipynb`. Notebook must be rerun.

---

## Figure 7 — D11 Sankey diagram (headline figure)

**Section:** §3.5 (Bending stiffness D11 of ECT slabs across all pathways)
**File name:** `fig07`

### What it communicates
The central result: across 32 pathways, D11 varies by approximately 3–4× for the
same set of ECTP slabs depending entirely on method choice. The Sankey diagram shows
how density → E-mod → ν method choices flow to D11 value ranges, making the
contribution of each method-choice step to the overall spread visually clear.

### Format
- Sankey/alluvial diagram. Full width (`figure*`).
- Vector format for the main manuscript figure.
- **This is also the HESS key figure**: supply a separate rasterized export at
  80×80 to 600 px resolution alongside the main submission.

### Design notes
- Columns (left to right): density method (4 nodes), E-mod method (4 nodes),
  ν method (2 nodes), D11 output (range or binned median, 1 column)
- Band width: proportional to number of ECTP slabs for which that pathway
  produces a valid D11 result (coverage-weighted)
- Band color: encodes median D11 value for that pathway — use a sequential,
  perceptually uniform colormap (e.g., from Scientific colour maps 7.0)
- Color scheme must be color-blind-friendly; test with Coblis
- Figure must be fully self-contained with a legend inside
- The data_flow density bands will be very thin (low coverage) — either include
  them for completeness or omit with a note in the caption
- Single sans-serif font; fonts embedded in vector output

### Data source
`examples/all_D11_pathways.ipynb`. Notebook already generates a Sankey diagram but
must be rerun with the final dataset and restyled for publication (font, colors,
bandwidth, color scale).

---

## HESS figure submission requirements (summary)

| Requirement | Value |
|---|---|
| Accepted formats | PDF, PS, EPS, JPG, PNG, TIF |
| Minimum resolution (raster) | 300 dpi |
| Minimum width | 8 cm |
| Maximum size per figure | 5 MB |
| Naming convention | `fig01`, `fig02`, … (Arabic numerals, zero-padded) |
| Multi-panel figures | All panels in **one file**; label **(a)**, **(b)**, … |
| Captions | In the `.tex` file — not embedded in the figure file |
| Color accessibility | Test all figures with [Coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/) |
| Recommended colormap | [Scientific colour maps 7.0](https://www.fabiocrameri.ch/colourmaps/) |
| Font | Single sans-serif family; fonts embedded in all vector files |
| Legend | Must be self-contained within each figure |
| Key figure | One figure at 80×80 to 600 px submitted separately after acceptance |

---

## Summary table

| Figure | Section | Notebook required | Status |
|---|---|---|---|
| Fig. 1 — Conceptual flowchart | §1.1 | No (schematic) | Not started |
| Fig. 2 — Parameterization DAG | §2.4.1 | No (graph definition) | Not started |
| Fig. 3 — Coverage overview | §3.1 | Yes — all four pathway notebooks | Not started |
| Fig. 4 — Density distributions | §3.2 | `all_density_pathways.ipynb` | Not started |
| Fig. 5 — E-mod distributions | §3.3 | `all_e_mod_pathways.ipynb` | Not started |
| Fig. 6 — ν distributions | §3.4 | `all_poissons_ratio_pathways.ipynb` | Not started |
| Fig. 7 — D11 Sankey (headline) | §3.5 | `all_D11_pathways.ipynb` | Prototype exists; needs rerun and restyling |
