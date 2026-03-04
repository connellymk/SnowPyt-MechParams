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
