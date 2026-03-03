# Paper & Project Reference Document
**Last updated:** 2026-03-03
**Purpose:** Comprehensive reference for future Claude sessions working on this paper and project.
**HESS submission page:** https://www.hydrology-and-earth-system-sciences.net/submission.html

---

## Paper Identity

| Field | Value |
|---|---|
| **Title** | An algorithmic framework to ascertain and compare mechanical properties from common snowpit observations |
| **Journal** | Hydrology and Earth System Sciences (HESS) |
| **Template** | `copernicus.cls`, `\documentclass[hess, manuscript]{copernicus}` |
| **Correspondence** | Mary Kate Connelly (connellymarykate@gmail.com) |
| **Running title** | Algorithmic framework for snow mechanical properties |
| **Target submission** | ~2 months from 2026-03-03 |
| **Scope** | Framework only — no claim about relationship between estimated D11 and ECT outcome; ECTP slabs used purely as a source of field-observed slab stratigraphies |

### Authors & Affiliations
| # | Name | Affiliation |
|---|---|---|
| 1 | Mary Kate Connelly | 205 Cobleigh Hall, Montana State University, Bozeman, MT, USA 59717 |
| 2 | Philipp Rosendahl | TU Darmstadt (**full address needed**) |
| 3 | Valentin Adam | SLF Davos (**full address needed**) |
| 4 | Samuel Verplanck | Montana State University |

---

## Key File Locations

### Paper files
| File | Purpose |
|---|---|
| `paper/outline.tex` | **Primary working draft** — the paper in progress (formerly `mkc_sections.tex`) |
| `paper/working_draft.tex` | Older draft — mine for equations, table drafts, and prose; do not write to this file; migrate content to `outline.tex` |
| `paper/figure_plan.md` | Figure plan — what each figure communicates, format, design notes, data source |
| `paper/references.bib` | Bibliography |
| `paper/paper_info.md` | **This file** |

### This project: SnowPyt-MechParams
| File | Purpose |
|---|---|
| `src/snowpyt_mechparams/constants.py` | Physical constants, measurement uncertainties, grain form validation |
| `src/snowpyt_mechparams/layer_parameters/density.py` | Density parameterizations |
| `src/snowpyt_mechparams/layer_parameters/elastic_modulus.py` | Young's modulus parameterizations |
| `src/snowpyt_mechparams/layer_parameters/poissons_ratio.py` | Poisson's ratio parameterizations |
| `src/snowpyt_mechparams/layer_parameters/shear_modulus.py` | Shear modulus (derived from E and ν) |
| `src/snowpyt_mechparams/slab_parameters/D11.py` | Classical laminate theory: A11, B11, D11, A55 |
| `src/snowpyt_mechparams/algorithm.py` | Pathway enumeration algorithm (backward traversal + memoization) |
| `src/snowpyt_mechparams/execution/engine.py` | ExecutionEngine: runs all pathways, manages result cache |
| `src/snowpyt_mechparams/graph/definitions.py` | GraphBuilder: constructs the full parameterization DAG |

### Related project: SnowPylot
| Path | Description |
|---|---|
| `../snow/snowpylot/` | SnowPylot Python library (CAAML parsing — separate repo) |
| `../snow/snowpylot/demos/western_snow_conference/` | WSC 2025 poster and abstract (good background prose) |

### Example notebooks (primary source of results)
| Notebook | What it shows |
|---|---|
| `examples/dataset_stats.ipynb` | SnowPilot database summary statistics |
| `examples/all_density_pathways.ipynb` | Coverage, distributions for 4 density pathways |
| `examples/all_e_mod_pathways.ipynb` | Coverage, distributions for 16 E-mod pathways |
| `examples/all_poissons_ratio_pathways.ipynb` | Coverage, distributions for 5 ν pathways |
| `examples/all_D11_pathways.ipynb` | **Headline result**: 32 D11 pathways × 14,951 ECT slabs |
| `examples/paper_figures.ipynb` | **Consolidation notebook**: Fig. 3 (coverage overview) + HESS style reference |

### Figure output directory
`examples/figures/` — all publication figures saved here at 300 dpi.

---

## Project: SnowPyt-MechParams

### Purpose
A Python library that implements a **parameterization graph** and execution engine to systematically enumerate and execute all valid calculation pathways from standard snowpit field observations to target mechanical parameters. The two core contributions are:

1. **The parameterization graph**: a directed acyclic graph (DAG) representing all implemented methods and their input/output relationships
2. **The execution engine**: runs every valid pathway for a given slab, with caching, failure tracking, and uncertainty propagation

The library is designed to be used with data parsed by **SnowPylot** (the companion parsing library in `../snow/snowpylot/`).

### Package structure
```
src/snowpyt_mechparams/
├── constants.py                  # Physical constants + measurement uncertainties
├── algorithm.py                  # Pathway enumeration (find_parameterizations)
├── graph/
│   └── definitions.py            # GraphBuilder — constructs the full DAG
├── execution/
│   └── engine.py                 # ExecutionEngine — runs all pathways
├── layer_parameters/
│   ├── density.py                # calculate_density(method, **kwargs)
│   ├── elastic_modulus.py        # calculate_elastic_modulus(method, **kwargs)
│   ├── poissons_ratio.py         # calculate_poissons_ratio(method, **kwargs)
│   └── shear_modulus.py          # calculate_shear_modulus(method, **kwargs)
└── slab_parameters/
    └── D11.py                    # weissgraeber_rosendahl(layers) → A11, B11, D11, A55
```

### Core algorithm: parameterization graph

The parameterization graph is a **directed acyclic graph (DAG)** with two node types:

- **Parameter nodes**: represent quantities — either directly observed inputs (e.g., `hand_hardness`, `grain_form`, `snow_pit`) or derived outputs (e.g., `density`, `elastic_modulus`, `D11`). Parameter nodes implement **OR logic**: any one incoming method is sufficient to compute the parameter.
- **Method/merge nodes**: represent a specific calculation method. They implement **AND logic**: all required inputs must be available. Each merge node has exactly one outgoing edge to its output parameter node.

Data flows: `snow_pit` (root) → input parameters → method nodes → output parameters → higher-level method nodes → target parameter (leaf).

**Shared density node**: This is the key structural constraint. The `density` parameter feeds both `elastic_modulus` methods and the `poissons_ratio` (Srivastava) method. This means density method is chosen once per pathway and shared — preventing logically inconsistent combinations.

### Pathway enumeration (`algorithm.py`)

```
find_parameterizations(graph, target_node) → List[Parameterization]
```

- **Backward traversal**: starts at `target_node`, recurses toward `snow_pit` root
- **Dynamic programming**: memoization prevents recomputing shared subgraphs
- **OR logic**: at each parameter node, enumerate all incoming methods → one branch per method
- **AND logic**: at each merge node, collect all required input branches → one branch tree
- **Deduplication**: `_method_fingerprint()` collapses structurally different traversals with identical method choices into one canonical pathway

**Result for D11**: 32 unique pathways (4 density × 4 E-mod × 2 ν, constrained by shared density node)

Key data classes in `algorithm.py`:
- `PathSegment` — one step from parameter → method → output
- `Branch` — a tree of PathSegments for a single pathway
- `Parameterization` — a fully resolved pathway with human-readable description
- `PathTree` — all pathways to a given target

### Execution engine (`execution/engine.py`)

```python
engine = ExecutionEngine(graph, dispatcher, cache)
results = engine.execute_all(slab, target_parameter, config)
```

- **Cache lifecycle**: cleared at the start of each new slab, persists across pathways within a slab. This ensures shared intermediate results (e.g., density computed once for multiple E-mod pathways) are not redundantly recalculated.
- **Failure handling**: a pathway fails silently for a given slab/layer if any required input is missing or falls outside a method's validity range (grain form not supported, density out of range, etc.). Failures are logged with reason.
- **Config options**: `include_method_uncertainty` (bool) — propagate input measurement uncertainty only (`False`), or also add method regression standard error in quadrature (`True`).

### Uncertainty propagation

Uses the Python [`uncertainties`](https://pythonhosted.org/uncertainties/) package. Every input is stored as a `ufloat` (value ± uncertainty). Uncertainty propagates automatically via first-order Taylor expansion through all calculations.

Two components tracked separately:
1. **Input measurement uncertainty**: from the adopted field observation uncertainties (see table below)
2. **Method uncertainty**: regression standard error from the original publication

These can be combined in quadrature or reported independently.

### Physical constants (`constants.py`)

| Constant | Value |
|---|---|
| ρ_ice | 917 kg/m³ |
| E_ice | 10,000 MPa (10 GPa) |
| G_ice | 3,846.15 MPa (= E_ice / 2(1+0.3)) |

### Adopted measurement uncertainties (`constants.py`)

| Observation | Uncertainty | Justification |
|---|---|---|
| Hand hardness | ±0.67 HHI (±2 sub-classes) | Höller (2010); author judgement |
| Slope angle | ±2° | Adapted from McCammon (2023); direct measurement assumed more precise than ±4° for screen |
| Grain size | ±0.5 mm | Author estimate |
| Layer thickness | ±5% relative | Author estimate (no published study) |
| Density (if measured) | ±10% relative | Conger & McClung (2009); Proksch et al. (2016) |

Uncertainties reviewed by an experienced field observer (Birkeland, 2025).

---

## Project: SnowPylot

### Purpose
Open-source Python library that parses SnowPilot CAAML XML files into structured Python objects. Developed to make the SnowPilot database accessible for programmatic research. Cited as `connelly2025` in the paper.

### Object hierarchy
```
SnowPit
├── core_info
│   ├── pit_id, pit_name, date, comment, caaml_version
│   ├── user (user_id)
│   └── location (slope_angle, aspect, elevation, country,
│                  pit_near_avalanche, pit_near_avalanche_location)
├── snow_profile
│   ├── measurement_direction, profile_depth, height_of_snowpack
│   ├── layers: List[layer]
│   │   └── layer: hardness, grain_form_primary, grain_form_secondary,
│   │               thickness, grain_size
│   ├── density_obs: List[density_obs]
│   └── temp_obs, surface_condition
└── stability_tests
    ├── CT:  List[ct_result]  (score, failure_depth, fracture_character)
    ├── ECT: List[ect_result] (score, failure_depth, fracture_character)
    ├── PST: List[pst_result]
    └── RB:  List[rb_result]
```

### Data handling decisions (relevant to paper)
1. **Density alignment**: SnowPilot allows density as a layer attribute OR as a separate density profile. Only layer-attributed density measurements are used. Stand-alone density profile entries that cannot be unambiguously aligned to a layer boundary are excluded.
2. **Grain form resolution**: Compound subform codes (e.g., `RGmx`) are resolved to primary base codes (e.g., `RG`) before parameterization lookup. This is done in `constants.py`.
3. **One malformed file**: `snowpits-55240-caaml.xml` failed to parse and was excluded, leaving 51,138 snowpits.

---

## Dataset Statistics
> Source: `examples/dataset_stats.ipynb`. Dataset: 1 September 2014 – 1 September 2025.

### Snowpits
| Metric | Value |
|---|---|
| Total pits parsed | 51,138 |
| Failed to parse | 1 (`snowpits-55240-caaml.xml`) |
| Unique users | 5,440 |
| Countries represented | 35 |
| Pits with slope angle | 46,226 (90.4%) |
| Pits within 50 m of avalanche | 1,586 (3.1%) |
| — at avalanche crown | 802 (1.6%) |
| — at avalanche flank | 406 (0.8%) |

### Layers
| Metric | Value |
|---|---|
| Total layers | 377,729 |
| Layers with hand hardness | 342,690 (90.7%) |
| Layers with primary grain form | 309,232 (81.9%) |
| Layers with grain size | 179,342 (47.5%) |
| Layers with density observation | 10,692 (2.8%) — confirmed from `all_density_pathways.ipynb` (data_flow pathway count) |

### Stability Tests
| Test | Count |
|---|---|
| Compression Test (CT) | 52,305 |
| Extended Column Test (ECT) | 48,391 |
| Propagation Saw Test (PST) | 6,326 |
| ECT slabs used in D11 analysis | 14,951 (ECTP propagating only) — ⚠️ previously stated as 14,776; confirmed from notebook output; update §2.5, §3.5, and key results table |

---

## Paper Structure & Section Labels

### Status key: ✅ Written | 🔲 Comment/outline only

Structure reflects the revised `outline.tex` as of 2026-03-03.

```
\section{Introduction}
  \subsection{Mechanical models of snow stability and their input parameters}   🔲
      % D11 introduced as headline target parameter; gap statement required
  \subsection{Snowpits and the SnowPilot database}                              🔲  (Table 1 here)
      % Bridging sentence: SnowPilot as underutilized resource motivating this work
  \subsection{Objectives and scope}                                             🔲
      % Two contributions; scope; paper structure

\section{Data and methods}                           \label{sec:data_methods}
  \subsection{Data: SnowPilot and SnowPylot}         \label{sec:snowpylot}      🔲
      % SnowPylot: prior published tool (connelly2025); three data handling decisions
      % NOTE: whether SnowPylot is listed as a paper contribution (§1.3) or only
      %   cited as prior work (§2.1) is an open decision -- resolve before writing §1.3
  \subsection{Measurement uncertainties}             \label{sec:uncertainties}  🔲
      % Two components (input vs. method); input-only reported; ufloat representation
  \subsection{Parameterizations for mechanical properties}
                                                     \label{sec:parameterizations}  🔲
    \subsubsection{Density}                                                     🔲
    \subsubsection{Effective, isotropic Young's modulus}                        🔲
    \subsubsection{Effective, isotropic Poisson's ratio}                        🔲
    \subsubsection{Shear modulus}                                               🔲  (one sentence: G derived)
    \subsubsection{Plate theory parameters for composite slabs}                 🔲
  \subsection{Parameterization graph and calculation pathways}  \label{sec:graph}  🔲
    \subsubsection{Representing parameterizations as a directed graph}          🔲
        % Shared density node constraint explained; 32 pathways for D11
    \subsubsection{Finding calculation pathways}                                🔲
    \subsubsection{Executing parameterizations}                                 🔲
        % Two-phase execution; density caching; failure handling; provenance tracking
  \subsection{Constructing slabs from ECT observations}  \label{sec:ectp_slabs}  🔲
      % ECTP only; framework-only scope stated explicitly; no ECT outcome claim

\section{Results}
  \subsection{Coverage and data loss by parameterization}  \label{sec:coverage}         🔲
      % Overview only; per-parameter detail in §3.2--3.5
  \subsection{Density estimates across methods}       \label{sec:density_results}       🔲
      % Closes with: implications for downstream E-mod estimation
  \subsection{Young's modulus estimates across methods}  \label{sec:emod_results}       🔲
      % Closes with: dominant driver of D11 spread
  \subsection{Poisson's ratio estimates across methods}  \label{sec:nu_results}         🔲
      % Layer-level AND as part of D11 pathway (5 sub-pathways for srivastava)
      % Closes with: structural coupling via shared density node
  \subsection{Bending stiffness (D11) of ECT slabs across all pathways}
                                                     \label{sec:D11_results}            🔲
      % Three paragraphs: (1) coverage, (2) spread/violin, (3) pathway detail

\section{Discussion}
  \subsection{Implications of method-dependent uncertainty for mechanical models}
                                       \label{sec:discussion_implications}             🔲  [NEW]
      % Closes the loop to §1.1; 3--4x D11 spread means fundamentally different
      %   model predictions from same field data
  \subsection{Toward a preferred calculation pathway}
                                       \label{sec:discussion_best_pathway}             🔲
  \subsection{Should mechanical properties be measured directly in the snowpit?}
                                       \label{sec:discussion_direct_measurement}       🔲
  \subsection{Limitations and assumptions}           \label{sec:limitations}           🔲
  \subsection{Extensions and future work}            \label{sec:extensions}            🔲
      % Merges "gaps in knowledge" and "more parameters, more problems" from prior draft

\section{Conclusions}                                                                   🔲
```

### Tables
| Label | Location | Status |
|---|---|---|
| `tab:snowpilot` | §1.2 (SnowPilot database) | Drafted in `working_draft.tex` — confirm numbers from rerun of `dataset_stats.ipynb` before migrating |
| `tab:geldesetzer` | §2.3.1 (density) | Drafted in `working_draft.tex` — migrate and update |
| `tab:E_applicability` | §2.3.2 (E-mod) | Drafted in `working_draft.tex` — add Schöttner column; confirm Schöttner grain forms from `elastic_modulus.py` |

### Figures
See `paper/figure_plan.md` for full figure descriptions, format requirements, and data sources.

| Label | Section | Status |
|---|---|---|
| Fig. 1 `fig:intro_flowchart` | §1.1 | Not started (schematic) |
| Fig. 2 `fig:dag` | §2.4.1 | Not started |
| Fig. 3 `fig:coverage` | §3.1 | Draft code in `paper_figures.ipynb`; run to generate `figures/fig03_coverage.png` |
| Fig. 4 `fig:density_results` | §3.2 | Draft matplotlib cell added to `all_density_pathways.ipynb`; run to generate `figures/fig04_density_distributions.png` |
| Fig. 5 `fig:emod_results` | §3.3 | Draft matplotlib cell added to `all_e_mod_pathways.ipynb`; run to generate `figures/fig05_emod_distributions.png` |
| Fig. 6 `fig:nu_results` | §3.4 | Draft matplotlib cell added to `all_poissons_ratio_pathways.ipynb`; run to generate `figures/fig06_nu_distributions.png` |
| Fig. 7 `fig:D11_violin` | §3.5 | Draft matplotlib violin cell added to `all_D11_pathways.ipynb`; run to generate `figures/fig07_D11_distributions.png` |

---

## Parameterizations: Full Detail

### Density (4 pathways to density)

| Method key | Citation | Inputs | Grain forms covered | Layer coverage |
|---|---|---|---|---|
| `data_flow` | Direct measurement | measured ρ | all | 2.8% |
| `geldsetzer` | Geldsetzer & Jamieson (2000) | HHI + grain form | PP, PPgp, DF, RG, RGmx, FC, FCmx, DH | 54.0% |
| `kim_jamieson_table2` | Kim & Jamieson (2014) Table 2 | HHI + grain form | broader | 63.4% |
| `kim_jamieson_table5` | Kim & Jamieson (2014) Table 5 | HHI + grain form + grain size | broader | 28.1% |

Regression forms vary by grain form: linear `ρ = A + B·h`, exponential `ρ = A·e^(B·h)`, power `ρ = A + B·h^x` (RG in geldsetzer).

Excluded: MM (machine-made), SH (surface hoar), IF (ice formations), wet/melt forms except MFcr.

Relative input uncertainty from measurement propagation: 10–18%.

### Young's Modulus E (4 methods; 4 × 4 = 16 pathways to E)

All methods take density as input; density method is chosen upstream.

| Method key | Citation | Additional input | Grain forms | Density range | Notes |
|---|---|---|---|---|---|
| `kochle` | Köchle & Schneebeli (2014) | grain form | RG, FC, DH | 150–250 and 250–450 kg/m³ | Two exponential eqns; higher E estimates (~71–252 MPa) |
| `wautier` | Wautier et al. (2015) | grain form | wide | 103–544 kg/m³ | Power law: E/E_ice = (ρ/ρ_ice)^n; R²=0.97; lower E (~29–69 MPa) |
| `bergfeld` | Bergfeld et al. (2023) | grain form | PP, DF, RG | 110–363 kg/m³ | Only method with formal published uncertainty: C1=4.4±0.18 |
| `schottner` | Schöttner et al. (2026) | grain form | [confirm] | [confirm] | Newest; add details from `elastic_modulus.py` |

Relative input uncertainty from measurement propagation: 28–92%.

Best layer coverage: `kim_jamieson_table2 → wautier` = 55.3%

### Poisson's Ratio ν (2 methods; 5 pathways because Srivastava depends on density)

| Method key | Citation | Inputs | Grain forms | Values | Notes |
|---|---|---|---|---|---|
| `kochle` | Köchle & Schneebeli (2014) | grain form only | RG, FC, DH | RG: 0.171±0.026 / FC: 0.130±0.040 / DH: 0.087±0.063 | No density dependence; MFcr excluded |
| `srivastava` | Srivastava et al. (2016) | grain form + density range | RG, PP+DF, FC+DH | RG: 0.191±0.008 (200<ρ<580) / PP+DF: 0.132±0.053 (ρ>200) / FC+DH: 0.17±0.02 (ρ>200) | Validity ranges on density |

Layer coverage: kochle 42.2%; srivastava combined ~69.2%.

Input uncertainty: ~0% for all ν methods (grain form is categorical; ± values are method scatter, not input propagation).

Wautier et al. (2015) computed orthotropic ν but not an effective isotropic form → not implemented.

### Shear Modulus G (1 method; derived)

`G = E / (2(1+ν))` — standard isotropic elastic relationship.
Wautier et al. (2015) provides a direct G parameterization (future extension).
G is used only for computing A55.

### Plate Theory Parameters (1 method: Weißgraeber & Rosendahl 2023)

Classical laminate theory. Slab layers assumed homogeneous, isotropic, linearly elastic, perfectly bonded.

Define reduced stiffness per layer: `Q_i = E_i / (1 − ν_i²)`

| Parameter | Units | Formula | Physical meaning |
|---|---|---|---|
| A11 | N/mm | Σ Q_i · h_i | Extensional stiffness |
| B11 | N | (1/2) Σ Q_i · (z_{i+1}² − z_i²) | Bending-extension coupling |
| D11 | N·mm | (1/3) Σ Q_i · (z_{i+1}³ − z_i³) | **Bending stiffness** (headline parameter) |
| A55 | N/mm | κ Σ G_i · h_i, κ=5/6 | Transverse shear stiffness |

z_i = distance of bottom face of layer i from bottom of slab (upward positive).

Static stress at weak layer:
- Normal: σ_zz = Σ ρ_i g h_i cos(θ)
- Shear: σ_xz = Σ ρ_i g h_i sin(θ)

D11 is the primary result: stiffer/thicker slabs store more elastic energy and drive crack propagation more effectively.

---

## Key Numerical Results (from notebooks)

### D11 — Headline analysis
32 unique pathways × 14,951 ECTP slabs = 478,432 attempted calculations. (⚠️ updated from 14,776 — confirmed from notebook output)

| Pathway | Slab success | Avg D11 | Avg rel. uncertainty |
|---|---|---|---|
| geldsetzer → wautier → kochle | 756 / 14,951 (5.1%) | 2.26×10⁹ N·m | 38.1% |
| kim_table2 → wautier → kochle | 756 / 14,951 (5.1%) | 2.19×10⁹ N·m | 37.3% |
| geldsetzer → schottner → kochle | 756 / 14,951 (5.1%) | 8.93×10⁷ N·m | 74.8% |
| kim_table2 → schottner → kochle | 756 / 14,951 (5.1%) | 8.72×10⁷ N·m | 73.3% |
| geldsetzer → kochle → kochle | 507 / 14,951 (3.4%) | 2.49×10⁸ N·m | 88.0% |
| data_flow pathways | ~17 slabs max (0.1%) | — | — |

D11 spread across pathways: ~3.6×10⁷ to ~2.3×10⁹ N·m (~64× from method choice alone at the extremes; ~3–4× for the main estimation pathways).

### Density results
- Estimated means across methods: 193–283 kg/m³ (method-dependent; geldsetzer=193, kim_t2=208, kim_t5=199, data_flow=283)
- kim_jamieson_table2 produces lower, more consistent estimates than geldsetzer

### E-mod results
- wautier: ~29–69 MPa | kochle: ~71–252 MPa
- Relative input uncertainty: 28–92% (pathway-dependent)

### Poisson's ratio results
- kochle: ν ≈ 0.087–0.171 (grain-form-dependent) | srivastava: ν ≈ 0.132–0.191

---

## LaTeX Writing Conventions

| Item | Convention |
|---|---|
| Cross-references | `Sect.~\ref{label}`, `Table~\ref{label}`, `Fig.~\ref{label}` |
| En-dashes | `--` |
| Large numbers (no line break at comma) | `51{,}138` |
| Thin space before unit | `51\,138 snowpits` |
| Python class/object names | `\texttt{SnowPit}`, `\texttt{core\_info}` |
| Grain form codes | `\texttt{RG}`, `\texttt{RGmx}` |
| Pathway notation | `geldsetzer → wautier → kochle` |
| Uncertainty notation | ± in text; relative uncertainty as % |
| Float barriers | `\FloatBarrier` after tables to keep them in section |
| Table format | `booktabs` (`\toprule`, `\midrule`, `\bottomrule`); `threeparttable` for footnotes |

---

## Citation Keys in Use

| Key | Reference |
|---|---|
| `fierz2009` | Fierz et al. (2009) — ICSSG grain classification |
| `greene2022` | Greene et al. (2022) — field observation guide |
| `caatechnicalcommittee2024` | CAA Technical Committee (2024) — CAAML standard |
| `norwegianwaterresourcesandenergydirectorate2022` | NVE (2022) — observation protocols |
| `chabot2004` | Chabot et al. (2004) — SnowPilot original |
| `chabot2016` | Chabot et al. (2016) — SnowPilot update |
| `connelly2025` | Connelly et al. (2025) — SnowPylot library |
| `weissgraeber2023` | Weißgraeber & Rosendahl (2023) — CLT for snow slabs |
| `bergfeld2023` | Bergfeld et al. (2023) — E parameterization |
| `kochle2014` | Köchle & Schneebeli (2014) — E and ν parameterization |
| `wautier2015` | Wautier et al. (2015) — E (and G) parameterization |
| `schottner2026` | Schöttner et al. (2026) — E parameterization |
| `srivastava2016` | Srivastava et al. (2016) — ν parameterization |
| `conger2009` | Conger & McClung (2009) — density measurement uncertainty |
| `proksch2016` | Proksch et al. (2016) — density measurement uncertainty |
| `holler2010` | Höller (2010) — hand hardness |
| `mccammonSLOPEMEASUREMENTHUMANS2023` | McCammon (2023) — slope angle uncertainty |
| `birkeland2025` | Birkeland (2025) — personal communication, uncertainty review |
| `lebigot2010uncertainties` | Lebigot — Python `uncertainties` package |
| `heierli2008` | Heierli et al. (2008) — avalanche initiation model |
| `rosendahl2020` | Rosendahl & Weißgraeber (2020) — WEAC |
| `siron2023` | Siron et al. (2023) — stability model |
| `reiweger2015` | Reiweger et al. (2015) — failure criterion |

---

## HESS Submission Requirements

> Source: https://www.hydrology-and-earth-system-sciences.net/submission.html (fetched 2026-03-02)

### Manuscript file for review
- Submit as **PDF, 1-column format, portrait orientation, embedded fonts, max 50 MB**
- All pages must have **consecutive page numbers and line numbers**
- Use the `manuscript` document class (already set: `\documentclass[hess, manuscript]{copernicus}`)
- LaTeX template version 7.13 (22 January 2026); use `template.tex` as the base
- Abstract also pasted separately into the submission form

### Required section order
The manuscript must contain these sections in this exact order:
1. Title page (title, authors with **full first names**, affiliations, correspondence email)
2. Abstract
3. Introduction
4. Numbered body sections (up to **3 heading levels**: `1`, `1.1`, `1.1.1`)
5. Conclusions
6. Appendices (if needed, labeled A, B, C…)
7. Code availability
8. Data availability
9. Interactive computing environment *(if applicable — e.g., Jupyter notebooks with DOI)*
10. Author contribution *(mandatory)*
11. Competing interests *(mandatory)*
12. Statement on inclusivity in global research *(optional, max 100 words)*
13. Acknowledgements
14. Financial support
15. References

> **Note:** "Sample availability," "Video supplement," and "Team list" sections also exist but are unlikely to apply here.

### Abstract
- Must be intelligible to a **general reader without reference to the text**
- Should include: topic introduction, key points, prospective research directions
- **Minimal citations; no unexplained abbreviations**
- Must also prepare a **500-character plain-language summary** for the submission form

### Heading levels
- Maximum **3 levels**: `\section{}`, `\subsection{}`, `\subsubsection{}`
- `\paragraph{}` is **not permitted** — use `\subsubsection{}` instead
- Heading style: **sentence case** (capitalize first word and proper nouns only)

### LaTeX-specific rules
- Use braced commands only: `\textrm{TEXT}` not `{\rm TEXT}`
- **No `\subfloat`** — collect all panels of a multi-panel figure into a single file
- **No `\newcommand` definitions** (no custom command definitions)
- **No colored table cells**
- BibTeX via `copernicus.bst` (already in use)

### Figures
| Rule | Requirement |
|---|---|
| File formats | PDF, PS, EPS, JPG, PNG, or TIF |
| Resolution | ≥ 300 dpi |
| Minimum width | 8 cm |
| Max size per figure | 5 MB |
| Max total submission (excl. supplements) | 30 MB |
| Naming | `fig01`, `fig02`, … (Arabic numerals, zero-padded) |
| Multi-panel | All panels in **one file**; label panels **(a), (b), …** (lowercase, parentheses) |
| Captions | In the `.tex` file, not embedded in figure file |
| Color accessibility | **Must be color-blind-friendly** — test with [Coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/); use [Scientific colour maps 7.0](https://www.fabiocrameri.ch/colourmaps/) |
| Legend | Must be self-contained within the figure (all symbols explained inside the figure) |
| Font | Single sans-serif font family preferred; fonts must be embedded in vector graphics |

### Figure style (implemented in notebooks)
All HESS-compliant figures use:
- **Colors**: Wong (2011) colorblind-safe palette — consistent across notebooks
- **Font**: DejaVu Sans / Helvetica / Arial via `mpl.rcParams`
- **Resolution**: 300 dpi PNG saved to `examples/figures/`
- **No embedded titles** — captions in `.tex`
- **Single column** = 3.35 in (8.5 cm); **double column** = 7.0 in (17.8 cm)
- `cmcrameri` package installed in venv for future colormap use

Consistent method color assignments (Wong palette):
- Density — kim_t2: `#009E73`, geldsetzer: `#0072B2`, kim_t5: `#E69F00`, data_flow: `#CC79A7`
- E-mod — wautier: `#009E73`, kochle: `#0072B2`, bergfeld: `#E69F00`, schottner: `#D55E00`
- ν — kochle: `#0072B2`, srivastava: `#E69F00`

### Tables
- Numbered sequentially with Arabic numerals
- Must be **self-explanatory** with a descriptive caption
- Submit as LaTeX (in `.tex` file) — **not as PDF or image**
- Use **horizontal lines only**: above table, below header row, below table (`\toprule`, `\midrule`, `\bottomrule`) — already using `booktabs` ✅
- **No colored cells** ✅
- Never abbreviate "Table" when referencing in text (write "Table 1" not "Tab. 1")

### Equations
- Numbered sequentially with Arabic numerals in parentheses: `(1)`, `(2)`, …
- Reference in text as: "Eq. (14)" or "Equation (14)" at sentence start
- Chemical reaction equations numbered separately: `(R1)`, `(R2)`, …
- Mathematical symbols in **italics**; function names, units, chemical formulas in **roman (upright)**
- Matrices in **boldface**; vectors in **boldface italics**

### Numbers, units, and punctuation
| Rule | Example |
|---|---|
| Words for integers < 10 | "three methods", "nine layers" |
| Numerals for ≥ 10 | "32 pathways", "14,951 slabs" |
| Numerals always with units | "1 m", "5 kg" |
| Spell out numbers that start sentences | "Thirty-two unique pathways…" |
| SI units required; negative exponents in denominators | `W m⁻²` not `W/m²` |
| Space between number and unit | "10 km", "1 %" |
| Date format | 1 September 2014 (day month year) |
| Time format | 15:17:02 (hh:mm:ss) |
| En dash for ranges (no spaces) | 1–10, 103–544 kg m⁻³ |
| Degree sign with space for coordinates | 30° N |
| Use CE/BCE not AD/BC | — |

### Capitalization
- **Section/figure/table headings**: sentence case (first word + proper nouns only)
- Cardinal directions: capitalized only in proper nouns ("South Dakota" but "eastern France")
- "Table" always capitalized when referencing a specific table

### Abbreviations
- Define in the **abstract** (if used there) and at **first use in the text**
- Avoid unexplained abbreviations in the abstract
- Plural abbreviations generally add –s: e.g., GCMs
- Units do not need definition

### English and italics
- Any standard English variety accepted; be **consistent throughout**
- Oxford spelling (–ize variants) encouraged
- Common Latin phrases **not** italicized: *et al.*, *cf.*, *e.g.*, *i.e.*, *in situ*, *a priori*
- Foreign words not in English dictionaries should be italicized

### In-text citations
| Case | Format |
|---|---|
| Author integrated in sentence | `Smith (2009)` |
| Author not in sentence | `(Smith, 2009)` |
| Multiple references | `(Smith, 2009; Mueller et al., 2010)` |
| Same first author, same year | Add letters: `(Smith, 2009a, b)` |

### Reference list format
- Ordered **alphabetically by first author's last name**
- For same first author: single-author papers first (chronological), then co-author papers (alpha by second author), then multi-author (chronological)
- Supply **full author lists** (last name then initials)
- Include volume, page numbers, **DOI**, and year
- Abbreviate journal names

**Journal article:**
```
Author, A. B. and Author, C. D.: Title of paper, J. Abbrev., 10, 100–110,
https://doi.org/10.xxxx/xxxxx, 2020.
```
**Software/code:**
```
Author, A. B.: Software name, Repository [code], https://doi.org/10.xxxx/xxxxx, 2020.
```
**Dataset:**
```
Author, A. B.: Dataset name, Repository [data set], https://doi.org/10.xxxx/xxxxx, 2020.
```
**Preprint:**
```
Author, A. B.: Title, arXiv [preprint], https://arxiv.org/abs/xxxx.xxxxx, DD Month YYYY.
```

### Code and data availability (mandatory sections)
- Both SnowPyt-MechParams and SnowPylot must be **deposited in a FAIR-aligned repository with a DOI** (e.g., Zenodo) before submission
- The `\codeavailability{}` section must explain how to access the code and cite the repository DOI
- If Jupyter notebooks are deposited with a DOI, add an `Interactive computing environment` section
- The `\dataavailability{}` section must explain SnowPilot data access; note that the raw CAAML files are from snowpilot.org (publicly accessible)
- Both code and data must be **cited in the reference list** using their DOIs

### Author contribution (mandatory)
- Required section before Acknowledgements
- Recommended to use the **CRediT** (Contributor Roles Taxonomy) framework
- Example format: "MKC designed the study, developed the software, and wrote the paper. PR contributed to the theoretical framework. VA contributed to the dataset. SV contributed to the analysis. All authors reviewed and edited the manuscript."

### Competing interests (mandatory)
- Required even if no conflicts exist
- Standard declaration: "The authors declare that they have no conflict of interest."
- If any author is on an editorial board: must state which journal

### AI usage
- If any AI tools were used to generate manuscript text: describe usage in **Methods** or **Acknowledgements**

### Supplementary material
- Use for items unsuitable for the main text: large images, videos, large datasets, code
- **No additional scientific interpretations** beyond the main manuscript
- Size limit: 50 MB
- Larger datasets/code should go in a repository with a DOI instead
- Supplement receives its own DOI
- Number supplement equations, figures, tables with S prefix: (S1), Fig. S5, Table S6

### Key figure for post-acceptance
- After acceptance, must supply one **"key figure"** representing the work: 80×80 to 600 pixels maximum
- Submit figures as individual files in a ZIP archive (no subfolders), named `f01`, `f02`, …

### Pre-submission checklist (from HESS guidelines)
- [ ] LaTeX template is version 7.13; using `\documentclass[hess, manuscript]{copernicus}`
- [ ] All pages numbered; line numbers enabled
- [ ] Full first names for all authors
- [ ] Abstract is self-contained (no unexplained abbreviations, minimal citations)
- [ ] 500-character plain-language summary prepared
- [ ] All figures are color-blind-friendly (test with Coblis)
- [ ] Figure files named `fig01`, `fig02`, … with panels collected into single files
- [ ] No `\subfloat`, no `\paragraph{}`, no `\newcommand`, no colored table cells
- [ ] All abbreviations defined at first use in abstract and text
- [ ] All references include DOIs and are formatted correctly
- [ ] Code (SnowPyt-MechParams + SnowPylot) deposited with DOI
- [ ] Data availability statement written
- [ ] Code availability statement written
- [ ] Author contribution section written (CRediT recommended)
- [ ] Competing interests declaration written
- [ ] Acknowledgements and Financial support sections written
- [ ] AI usage declared (if applicable)

---

## Outstanding TODOs

### Dataset — confirm before writing
- [ ] **ECTP slab count discrepancy**: notebooks produce 14,951 slabs; paper previously stated 14,776. Update §2.5, §3.5, headline result table, and abstract once confirmed.
- [ ] **Density layer count** confirmed as 10,692 (2.8%) from `all_density_pathways.ipynb` data_flow pathway count. Verify via `dataset_stats.ipynb` density cell (checks `layer.density` attribute).

### Content — before writing begins
- [ ] **Schöttner et al. citation year**: `graph/definitions.py` cites "(2024)" but `paper_info.md` and `outline.tex` use "(2026)"; check `elastic_modulus.py` for the correct year and citation key, then make consistent throughout
- [ ] **Schöttner et al. details**: read `elastic_modulus.py` to fill in grain forms, density range, and equation for §2.3.2 and `tab:E_applicability`
- [ ] **SnowPylot contribution status**: decide whether SnowPylot is listed as a paper contribution in §1.3 (as currently drafted by MKC) or cited only as prior published work in §2.1 (as recommended in structural review); this affects the framing of the paper's contributions

### Writing — administrative
- [ ] **Author affiliations**: full addresses for Rosendahl (TU Darmstadt) and Adam (SLF Davos)
- [ ] **Abstract**: not yet drafted
- [ ] **Author contributions**: fill in `\authorcontribution{}` (CRediT format recommended)
- [ ] **Competing interests**: fill in `\competinginterests{}`
- [ ] **Acknowledgements**: fill in `\begin{acknowledgements}`
- [ ] **Financial support**: fill in `\financialsupport{}`
- [ ] **500-character plain-language summary**: required for HESS submission form (prepare alongside abstract)

### Tables
- [ ] **Table `tab:snowpilot`**: migrate from `working_draft.tex`; confirm all numbers from rerun of `dataset_stats.ipynb`; convert to `booktabs` format (`\toprule`, `\midrule`, `\bottomrule`)
- [ ] **Table `tab:geldesetzer`**: migrate from `working_draft.tex` and verify numbers
- [ ] **Table `tab:E_applicability`**: migrate from `working_draft.tex` and add Schöttner column

### Figures
- [ ] **Figs. 3–7**: rerun all pathway notebooks (`all_density_pathways.ipynb`, `all_e_mod_pathways.ipynb`, `all_poissons_ratio_pathways.ipynb`, `all_D11_pathways.ipynb`) and then `paper_figures.ipynb` to generate PNG files in `examples/figures/`
- [ ] **Evaluate Figs. 4–6 consolidation**: after notebook rerun, decide whether density/E-mod/nu distributions fit in a single three-panel figure (see §5 of `paper_figures.ipynb`)
- [ ] **Fig. 1** (conceptual flowchart): create schematic; no notebook required
- [ ] **Fig. 2** (DAG): style output from `graph/visualize.py` for publication; color-blind-friendly; see `figure_plan.md`
- [ ] **Color-blind check**: test all figures with Coblis before submission

### Pre-submission
- [ ] **Code/data availability URLs**: replace `[URL TBD]` in `\codeavailability{}` (deposit on Zenodo before submission)
- [ ] **Jupyter notebooks DOI**: if deposited, add `Interactive computing environment` section
- [ ] **AI usage declaration**: declare Claude Code assistance in Methods or Acknowledgements per HESS policy
- [ ] **Delete duplicate** `paper_info.md` at project root (was created before user specified `paper/` directory)
- [ ] **Color-blind check**: test all figures with Coblis before submission
