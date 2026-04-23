## Data Models

The `models` module defines the core data structures that represent snow observations and carry results through all calculations in the package. Think of them as standardized containers: field measurements go in, and calculated results accumulate as the data passes through the processing pipeline.

### Overview

A snow pit observation enters the pipeline from a CAAML file and flows through four nested structures:

```
CAAML file → Pit → Slab(s) → Layer(s) → mechanical parameters
```

### Structures

#### `Layer`

Represents a single snow layer in a pit profile. Stores the raw field measurements recorded at the pit — depth, thickness, density (if directly measured), hand hardness, grain form, grain size, and whether the layer was flagged as a layer of concern.

It also holds slots for calculated mechanical properties that are filled in later by the `layer_parameters` module: density (estimated from a parameterization), elastic modulus, shear modulus, and Poisson's ratio.

Three values are derived automatically from the field measurements:

- `depth_bottom`: depth to the bottom of the layer (`depth_top` + `thickness`)
- `hand_hardness_index`: numeric value on the 1–6 HHI scale, looked up from the hand hardness string (e.g., `'P'` → 4.0)
- `main_grain_form`: the two-character basic grain class extracted from the full grain form code (e.g., `'FCxr'` → `'FC'`)

#### `WeakLayer`

A lightweight extension of `Layer` that marks a specific snow layer as the weak layer beneath the slab. It inherits all `Layer` attributes (depth, thickness, density, hand hardness, grain form, grain size) so that the weak layer's physical properties can be read alongside the slab layers. Fracture and strength parameters are not computed from standard pit observations; stability-criterion callers must supply those values directly or rely on criterion-specific defaults where available.

#### `Slab`

Represents the snow slab sitting above a weak layer, as an ordered list of `Layer` objects from the surface down to (but not including) the weak layer. In addition to the layers, the slab holds:

- the **weak layer** (`weak_layer: Optional[WeakLayer]`): a single object that carries the weak layer's field measurements (thickness, density, hand hardness, grain form, grain size). The `WeakLayer` class extends `Layer`, so all `Layer` attributes are available on it.
- **slope angle**
- **metadata** recording which stability test result was used to define the weak layer (test type, score, failure depth), and how many test results of that type exist in the source pit
- **slab stiffness parameters** (*A11*, *A55*, *B11*, *D11*) computed by the `slab_parameters` module and stored here for use in downstream calculations
- **slab-weight parameters** (`slab_weight`, `slab_weight_shear`, `slab_weight_shear_with_elasticity`) populated by graph execution when the selected density pathway succeeds
- **stability results** from the WEAC skier criterion and the Roch natural stability index (*S*_r), once calculated

A slab must contain at least one layer. The `total_thickness` property sums all layer thicknesses.

#### `Pit`

Represents a complete snow pit observation. Stores all layers in the profile (ordered top to bottom), the slope angle, a pit identifier, and the raw results from stability tests (ECT, CT, PST).

The key operation of `Pit` is `create_slabs()`, which identifies the weak layer and assembles a `Slab` for each relevant test result. Three strategies are available:

| Strategy | Weak layer source | Slabs produced |
|---|---|---|
| `None` | — | Empty list; no slab created |
| `"layer_of_concern"` | Layer explicitly flagged in the pit record | One slab |
| `"ECTP_failure_layer"` | ECT result with crack propagation (ECTP) | One per propagating ECTP |
| `"CT_failure_layer"` | CT result with Q1, SC, or SP fracture character | One per qualifying CT |

In each case, the slab layers are all layers shallower than the identified weak layer. When multiple test results exist in one pit, the resulting slabs share the same underlying layer data — this should be accounted for in any statistical analysis.

### Reading data from CAAML files

Field data enters the pipeline through `pit_parser.parse_pit()`, also accessible as the convenience method `Pit.from_snow_pit()`. This function converts a snowpylot `SnowPit` object — parsed from a CAAML file — into a `Pit`. It extracts the slope angle, pit identifier, all layer properties, direct density measurements (matched to layers by depth and thickness), and stability test results.

### Measurement uncertainty

All numeric values in these structures can be either plain numbers or *uncertain numbers* (from Python's `uncertainties` package), which carry both a nominal value and a standard uncertainty. When data is read from a CAAML file, standard measurement uncertainties are automatically attached to each measurement:

| Quantity | Uncertainty |
|---|---|
| Slope angle | ±2° |
| Layer thickness | ±5% of measured value |
| Density | ±10% of measured value |
| Grain size | ±0.5 mm |
| Hand hardness index | ±0.67 HHI units |

These uncertainties then propagate automatically through all subsequent arithmetic, so every calculated mechanical parameter carries an uncertainty estimate derived from the original field measurements.

### Connections to the rest of the package

The model objects are consumed — and written back to — by three groups of downstream modules:

- **`layer_parameters/`** — calculates density, elastic modulus, shear modulus, and Poisson's ratio for each `Layer`, storing results in the layer's calculated-parameter fields.
- **`slab_parameters/`** — integrates layer-level properties through the slab thickness to compute the slab stiffness parameters (*A11*, *A55*, *B11*, *D11*), stored on the `Slab`.
- **`stability_criteria/`** — uses the complete `Slab` (stiffness parameters, slope angle) together with externally supplied weak-layer properties to evaluate avalanche release potential, storing criterion results back on the `Slab`.

The `algorithm` and `execution` modules orchestrate which calculations are run and in what order, reading from and writing to the same `Layer` and `Slab` objects throughout the pipeline.

---

## Slab Layer Parameterizations

The `layer_parameters` module provides empirical methods for estimating the mechanical properties of individual snow layers from field observations. Each property has its own sub-module with one or more methods drawn from the literature. Results are stored back on the `Layer` object (in `density_calculated`, `elastic_modulus`, `poissons_ratio`, and `shear_modulus`) and are used downstream to compute slab-level stiffness parameters.

All methods accept an `include_method_uncertainty` flag. When `True` (the default), the standard error reported in the source paper is combined in quadrature with the uncertainty already propagated from the field measurements. When `False`, only the propagated input uncertainty is retained — useful for isolating the contribution of measurement uncertainty alone.

### Density

Density is used by every downstream calculation that requires a physical layer property, so it is the first parameter calculated. When a layer was not sampled with a density cutter, one of three empirical methods is used to estimate it from hand hardness and grain form (the two observations most consistently recorded in pit profiles).

**`geldsetzer`** (Geldsetzer & Jamieson, 2000)

Estimates density from hand hardness index and grain form using linear regressions fitted to a Canadian dataset. A separate non-linear regression (ρ = A + B·h³·¹⁵) is used for rounded grains (RG), which do not conform well to a linear relationship. Supported grain forms: PP, PPgp, DF, RG, RGmx, FC, FCmx, DH. Method uncertainty is the regression standard error reported in Table 3 of the source paper.

**`kim_jamieson_table2`** (Kim & Jamieson, 2014)

An updated version of the Geldsetzer regressions fitted to an expanded dataset. Uses the same inputs (hand hardness index and grain form) but with revised coefficients and an exponential model (ρ = A·eᴮʰ) for rounded grains. Supported grain forms: PP, PPgp, DF, RG, RGxf, FC, FCxr, DH, MFcr. For RG, the method uncertainty is the standard error of the fitted exponent, propagated through the exponential.

**`kim_jamieson_table5`** (Kim & Jamieson, 2014)

A multi-variable regression that incorporates grain size alongside hand hardness (ρ = A·h + B·gs + C), improving estimates for grain forms where size is an informative predictor. Requires grain size to be recorded in the pit profile. Supported grain forms: FC, FCxr, PP, PPgp, DF, MF. Method uncertainty is the residual standard error of the regression.

### Elastic Modulus

Young's modulus (*E*) controls how much a snow layer deforms under a bending or compressive load. All four methods express *E* as a function of density, scaled relative to the elastic modulus of solid ice.

**`bergfeld`** (Bergfeld et al., 2023)

A power-law relationship (E = 6500 · (ρ/ρᵢ꜀ₑ)⁴·⁴ MPa) whose exponent was fitted by optimizing a layered-slab mechanical model against vertical displacement fields measured during flat-field Propagation Saw Tests (PSTs). Because the fitting is dominated by slab bending, this modulus should be interpreted as a flexural-like quantity. Supported grain forms: PP, RG, DF. Valid density range: 110–363 kg/m³.

**`kochle`** (Köchle & Schneebeli, 2014)

An exponential relationship derived from finite-element (FE) simulations of snow microstructure imaged by X-ray micro-computed tomography (μ-CT). Two separate fits are used depending on density: a lower-density fit (150–250 kg/m³, R² = 0.68) and a higher-density fit (250–450 kg/m³, R² = 0.92). Because the source paper does not report standard errors for the fitted coefficients, no method uncertainty is added beyond what propagates from the input density. Supported grain forms: RG, FC, DH, MF.

**`wautier`** (Wautier et al., 2015)

A power-law relationship (E/Eᵢ꜀ₑ = 0.78 · (ρ/ρᵢ꜀ₑ)²·³⁴) derived from numerical homogenization of the elastic stiffness tensor computed over 3-D μ-CT images of snow. The fit covers a wide density range (103–544 kg/m³) and achieves R² = 0.97. No method uncertainty is added (standard errors for the coefficients are not reported). Supported grain forms: DF, RG, FC, DH, MF.

**`schottner`** (Schöttner et al., 2026)

A power-law relationship (E/Eᵢ꜀ₑ = A · (ρ/ρᵢ꜀ₑ)ⁿ) with grain-type-specific scaling constants *A* and *n* fitted to experimental uniaxial compression tests on snow samples. Grain form groups share coefficients: DF/RG use one set, FC/DH another, and SH a third. Method uncertainty is the standard error of the fitted coefficients *A* and *n*, propagated through the power law. Supported grain forms: DF, RG, FC, DH, SH.

### Poisson's Ratio

Poisson's ratio (*ν*) describes how much a layer expands sideways when compressed vertically. Both available methods find little dependence on density; the dominant predictor is grain type. The result is a grain-type-specific constant with an associated uncertainty reflecting natural variability among samples.

**`kochle`** (Köchle & Schneebeli, 2014)

Grain-type-specific mean values derived from the same FE simulations of μ-CT images used for the elastic modulus method. Values are RG: 0.171 ± 0.026, FC: 0.130 ± 0.040, DH: 0.087 ± 0.063. The large uncertainty for depth hoar reflects the high variability in that grain type. Supported grain forms: RG, FC, DH.

**`srivastava`** (Srivastava et al., 2016)

Grain-type-specific mean values from a separate μ-CT and FE study. Values are RG: 0.191 ± 0.008, PP/DF: 0.132 ± 0.053, FC/DH: 0.17 ± 0.02. Density is not used in the formula (no clear dependence was found in the study) but the method is only valid for densities above 200 kg/m³. Supported grain forms: RG, PP, DF, FC, DH.

### Shear Modulus

The shear modulus (*G*) describes resistance to shear deformation and is used together with Young's modulus and Poisson's ratio in computing the slab-level stiffness parameters. Currently one method is implemented.

**`wautier`** (Wautier et al., 2015)

A power-law relationship (G/Gᵢ꜀ₑ = 0.92 · (ρ/ρᵢ꜀ₑ)²·⁵¹) derived from the same homogenization study as the Wautier elastic modulus method. The fit achieves R² = 0.97 over the density range 103–544 kg/m³. No method uncertainty is added (standard errors not reported). Supported grain forms: DF, RG, FC, DH, MF.

---

## Slab Level Parameterizations

The `slab_parameters` module computes four mechanical stiffness parameters for the slab as a whole by integrating the layer-level properties (elastic modulus, Poisson's ratio, shear modulus, thickness) across the slab's thickness. These slab-level parameters describe how the slab as a unit resists extension, bending, shear, and the coupling between bending and extension. They are the inputs required by the stability criteria.

All four parameters come from a single framework: classical laminate theory from composite mechanics, applied to stratified snow by Weißgraeber & Rosendahl (2023, *The Cryosphere*, 17, 1475–1496). The slab is treated as a beam composed of *N* discrete layers, each assumed to be homogeneous and isotropic. Deformation is governed by first-order shear deformation theory, which — unlike simpler Euler-Bernoulli beam theory — accounts for shear deformations through the thickness. This matters for snow slabs, which are often thick relative to their span.

**Coordinate system.** All four integrals are evaluated with *z* measured from the geometric centroid of the slab (positive upward toward the surface). A slab of total thickness *h* therefore spans *z* = −*h*/2 at the weak layer interface to *z* = +*h*/2 at the snow surface. The centroid is always placed at the geometric midpoint of the total slab thickness, regardless of how the density or stiffness varies between layers.

**Plane-strain modulus.** The term *E*ᵢ/(1 − νᵢ²) — called the plane-strain modulus — appears in the A11, B11, and D11 integrals. It accounts for the constraint that the slab cannot deform sideways out of the slope plane, which stiffens the slab relative to a simple one-dimensional bar.

### Extensional Stiffness (*A*11)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023, Eq. 8a)

*A*11 is the sum of each layer's plane-strain modulus multiplied by its thickness: A11 = Σ Eᵢ/(1 − νᵢ²) · hᵢ. It relates the in-plane normal force per unit width to the in-plane strain — essentially describing how hard it is to stretch or compress the slab along the slope. Each layer contributes in simple proportion to its thickness and stiffness. The units are N/mm.

### Bending-Extension Coupling Stiffness (*B*11)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023, Eq. 8b)

*B*11 is the sum of each layer's plane-strain modulus weighted by the first moment of its position about the centroid: B11 = ½ · Σ Eᵢ/(1 − νᵢ²) · (z²ᵢ₊₁ − z²ᵢ). This coupling term is zero whenever the slab is symmetric or homogeneous, because the positive contributions from layers above the centroid cancel the negative contributions from layers below. When the stiffness distribution is asymmetric — for example, a stiff wind crust near the surface above softer faceted layers — *B*11 is nonzero and an in-plane force will induce bending (and vice versa). This is analogous to the bending of a bimetallic strip under thermal loading. The units are N.

### Bending Stiffness (*D*11)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023, Eq. 8c)

*D*11 is the sum of each layer's plane-strain modulus weighted by the second moment of its position about the centroid: D11 = ⅓ · Σ Eᵢ/(1 − νᵢ²) · (z³ᵢ₊₁ − z³ᵢ). It relates the bending moment per unit width to the curvature of the slab — the snow equivalent of the *EI* flexural rigidity in structural beam theory. Because position enters as the square of the distance from the centroid, a stiff layer far from the centre contributes far more to *D*11 than the same layer near the centre; layering structure therefore has a strong and non-linear influence on bending stiffness. The units are N·mm.

### Shear Stiffness (κ·*A*55)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023, Eq. 8d)

The shear stiffness is computed as A55 = Σ Gᵢ · hᵢ — the sum of each layer's shear modulus multiplied by its thickness — and then multiplied by the shear correction factor κ = 5/6. This factor corrects for the fact that the shear stress is not uniformly distributed through the thickness of a rectangular beam; 5/6 is the standard approximation for this geometry. The result, κ·A55, relates the transverse shear force per unit width to the shear deformation of the slab. Unlike the other three parameters, this integral uses the shear modulus *G* directly rather than the plane-strain modulus E/(1−ν²). The units are N/mm.

---

## Stability Criteria

The `stability_criteria` module evaluates avalanche release potential using the mechanical parameters computed for the slab and weak layer. Two criteria are implemented, representing different physical approaches: the Roch criterion is a classical limit-equilibrium method based on the ratio of weak-layer shear strength to the gravitational shear stress acting on the weak layer; the WEAC criterion uses fracture mechanics to assess whether a crack in the weak layer will nucleate under the combined influence of a skier load and the slab's own weight.

The two criteria handle measurement uncertainty differently. The Roch criterion preserves uncertain-number arithmetic throughout its calculation, so the returned stability index carries an uncertainty estimate propagated from the input layer densities, thicknesses, slope angle, and supplied strength value. The WEAC criterion strips all uncertain numbers to their nominal values at the adapter boundary, because the iterative eigensystem solver inside the `weac` package is incompatible with that arithmetic; the WEAC results are therefore plain floats with no associated uncertainty.

---

### Roch Stability Index

**`calculate_roch`** (Roch, 1966; Föhn, 1987)

Computes the gravitational shear stress on the weak layer and evaluates the ratio of shear strength to that stress. The shear stress is τ = (Σᵢ ρᵢ hᵢ) · g · sin θ, where ρᵢ and hᵢ are the calculated density (kg/m³) and thickness (m) of each slab layer, and θ is the slope angle; this is the component of the slab's weight acting parallel to the slope surface and tending to slide the slab along the weak layer. The weak-layer shear strength τ_c must be supplied by the caller.

Two variants of the stability index are available depending on whether an additional skier stress is provided. In the natural terrain variant (Roch, 1966), the index is S_r = τ_c / τ; values below 1.0 indicate that the gravitational load already exceeds the shear strength and the slope is critically stressed under its own weight alone. In the skier-loaded variant (Föhn, 1987), the index is S_a = τ_c / (τ + δτ), where δτ is the additional shear stress applied by the skier, supplied by the caller; values below 1.0 indicate that the combined gravitational and skier load exceeds the weak-layer shear strength. The natural variant is undefined on flat terrain where τ = 0; the skier variant requires a finite, nonzero δτ. The function returns `None` if the slope angle is missing, any slab layer lacks a thickness or calculated density, the computed shear stress is not a finite number, or these conditions on τ or δτ are not met.

Roch is called directly rather than exposed as a parameter graph target. The natural variant uses only the gravitational shear stress, while the skier variant is computed by calling `calculate_roch` with a caller-supplied δτ. The shear strength τ_c must be supplied by the caller in kPa; `calculate_roch` converts to Pa internally (τ_c_pa = τ_c × 1000) before computing the index. Results are written to `slab.roch_result`.

---

### WEAC Skier Criterion

**`calculate_weac_skier`** (Weißgraeber & Rosendahl, 2023)

Applies the Weak Layer Anticrack Nucleation (WEAC) coupled fracture criterion to assess whether a skier load triggers the onset of crack propagation in the weak layer. The physical model, described in Weißgraeber & Rosendahl (2023, *The Cryosphere*, 17, 1475–1496), represents the stratified snow slab as a layered beam resting on the weak layer, which is treated as an elastic foundation with independent normal and shear stiffnesses. A skier applies a point load to the slab surface, and the model computes the resulting normal and shear stress distribution in the weak layer and the energy release rate of a potential crack of progressively growing length. Anticrack nucleation is predicted when both a stress criterion (the combined normal and shear stresses at the crack tip reach the weak-layer strength envelope) and an energy criterion (the energy release rate reaches the fracture toughness) are simultaneously satisfied. The coupled nature of the criterion means that neither stress nor energy alone is sufficient: the crack must be able to grow in the sense of both conditions at once.

The adapter translates SnowPyt slab data into the input format expected by the `weac` package and runs the coupled criterion iteratively to find the critical configuration. All four mechanical parameters (elastic modulus, shear modulus, Poisson's ratio, and density) and the thickness of every slab layer must be populated; layer thicknesses are converted from centimetres to millimetres at the interface. Weak-layer fracture and strength parameters are taken from `slab.weak_layer`; any parameter absent from that object falls back to WEAC's built-in reference values from Weißgraeber & Rosendahl (2023). Individual parameters can also be overridden by keyword arguments passed directly to the function, which take precedence over both `slab.weak_layer` and the built-in defaults. The model geometry is set up as two equal-length adjacent segments — by default, each as long as the total slab thickness in millimetres — one carrying the skier mass and one unloaded; both segments rest on the weak-layer foundation. The skier mass defaults to `STANDARD_SKIER_MASS_KG` (80 kg) but can be changed by the caller.

The primary output is `g_delta`, the value of the coupled stability criterion: values of 1.0 or greater indicate that anticrack nucleation is predicted for the given skier mass. The result also reports the critical skier mass at which nucleation would be expected, the anticrack half-length at the critical configuration (in mm), the mode-I and mode-II energy release rates *G*_I and *G*_II and their sum *G*_total (in J/m²), and the distances from the current state to both the stress failure envelope and the energy-release-rate failure envelope. The `converged` field records whether the iterative algorithm reached its solution reliably; results from non-converged runs should be treated with caution. On numerically pathological slabs the solver may encounter a recursion depth limit or, if a per-slab time limit is configured, a timeout; in either case the function returns `None` rather than an unreliable result. The `weac` package is an optional dependency and must be installed separately; calling the function without it raises an `ImportError`.

---

## Parameter Graph

The `graph` module defines a directed graph that encodes every possible way to compute snow mechanical parameters from raw pit observations. Each node in the graph represents either a measured quantity or a calculated parameter, and each edge represents either the transfer of a value from one parameter to the next or a specific empirical method that computes one parameter from others. Together, the nodes and edges make all dependency relationships explicit, so the algorithm can automatically discover every valid pathway from measured inputs to any target parameter without those pathways being written out by hand.

The graph connects the computational modules — `models`, `layer_parameters`, and `slab_parameters` — by placing their inputs and outputs as nodes and their calculation methods as edges. This is the mechanism that allows the package to report 32 distinct pathways to D11: rather than maintaining a hand-written list of 32 method combinations, the algorithm traverses the graph and discovers them from its structure. When a new empirical method is added to the package, a single new edge in the graph is sufficient; the algorithm then finds every affected pathway automatically.

### Node types

The graph contains two kinds of node. A **parameter node** represents a named quantity — either a raw field measurement or a calculated result. The single root of the graph is a parameter node called `snow_pit`, representing the pit observation as a whole and having no incoming edges. Six measured-input parameter nodes flow from the root: `measured_density`, `measured_hand_hardness`, `measured_grain_form`, `measured_grain_size`, `measured_layer_thickness`, and `measured_slope_angle`. Calculated outputs at the layer level are density, elastic modulus, Poisson's ratio, and shear modulus. Calculated outputs at the slab level are the stiffness parameters (*A*11, *B*11, *D*11, *A*55) and the slab-weight coverage targets `slab_weight`, `slab_weight_shear`, and `slab_weight_shear_with_elasticity`.

A **merge node** represents the convergence of two or more inputs into a single method call. Because most empirical methods require more than one input, a merge node is interposed between the parameter nodes supplying those inputs and the method edge that produces the result. For example, the four elastic modulus methods each require both density and grain form: the merge node `merge_density_grain_form` collects these two inputs and sits upstream of the four method edges that lead to the elastic modulus parameter node. At the slab level, separate merge nodes aggregate the layer-level results needed for each stiffness integral: `merge_E_nu` combines elastic modulus and Poisson's ratio from all layers, `merge_hi_G` combines thickness and shear modulus for the *A*55 shear integral, and `merge_hi_E_nu` combines thickness with the elastic inputs shared by the *A*11, *B*11, and *D*11 slab integrals. The slab-weight branch uses `merge_slab_weight_inputs` for density plus thickness, `merge_slab_weight_slope_angle` for slab weight plus slope angle, and `merge_slab_weight_shear_elasticity` for slope-parallel slab weight plus elastic modulus and Poisson's ratio.

### Edge types

The graph contains two kinds of edge. A **data-flow edge** connects one node to another and carries no method name, indicating that a quantity is passed through without any calculation. The edges from `snow_pit` to the five measured-input nodes, from `measured_density` directly to the `density` node (representing the case where density was measured directly with a cutter), and from parameter nodes into the merge nodes that require them, are all data-flow edges.

A **method edge** connects a merge node (or in a few cases a single parameter node) to the parameter node it computes, and carries the name of the empirical method that performs the calculation. The edge from `merge_density_grain_form` labelled `bergfeld` arriving at `elastic_modulus` is one example; the edge from `measured_grain_form` labelled `kochle` arriving at `poissons_ratio` is another — the Köchle & Schneebeli (2014) Poisson's ratio method requires grain form but not density, so it departs from the measured grain form node directly rather than from `merge_density_grain_form`.

### Graph topology

The graph flows in a single direction from the root toward the target parameters. From `snow_pit`, data-flow edges fan out to the measured-input parameter nodes. From there, the layer-level parameters are built up in stages: density can be reached via the direct-measurement data-flow edge (when a density cutter was used) or via one of three empirical methods that work from hand hardness, grain form, and optionally grain size; elastic modulus, Poisson's ratio, and shear modulus each follow from density and grain form through the `merge_density_grain_form` node, except that the kochle Poisson's ratio method branches from grain form alone. Once layer-level parameters are available, the graph continues upward to slab stiffnesses and slab-weight targets. `slab_weight` integrates calculated density through layer thickness, `slab_weight_shear` projects that weight by slope angle, and `slab_weight_shear_with_elasticity` records the same slope-parallel weight only for pathways where elastic modulus and Poisson's ratio are also available.

---

## Parameterization Algorithm

The `algorithm` module takes the parameter graph and a target parameter node and returns a list of all valid calculation pathways from the measured pit inputs to that target. Each pathway is a complete, self-consistent assignment of one method to every parameter along the route — a recipe that fully specifies how to compute the target from field observations. For the target parameter D11, there are 32 such recipes, arising from the product of 4 density methods, 4 elastic modulus methods, and 2 Poisson's ratio methods.

The central function is **`find_parameterizations`**, which performs a backward traversal of the graph starting from the target node and working toward the root `snow_pit`. The backward direction is natural for this problem: by starting from what needs to be computed and asking "what does this require?", the algorithm naturally gathers all the ingredients for each pathway.

### Data structures

A **`PathSegment`** is the smallest unit: it records one step of a calculation pathway as a triple — the source node, the name of the method (or `data_flow` if the edge carries no method), and the destination node. A segment such as `merge_density_grain_form → bergfeld → elastic_modulus` means that the Bergfeld method takes the assembled inputs from `merge_density_grain_form` and produces a value for elastic modulus.

A **`Branch`** is an ordered list of `PathSegment` objects forming a single linear thread through the graph. When no merges are needed, the full pathway from `snow_pit` to the target is a single branch. When the traversal encounters a merge node, each input to that merge becomes its own branch, all converging at the merge point.

A **`Parameterization`** assembles the full picture. It holds a list of branches and a list of merge points. Each merge point records which branches converge at it, the name of the merge node, and a continuation path — the sequence of steps that proceeds from the merge onward toward the target. Branches and merge points together fully specify which inputs are required and in what order they must be combined to reach the target.

### Finding all pathways

**`find_parameterizations`** applies two rules depending on the type of node it visits during the backward traversal. At a **parameter node**, the algorithm applies OR logic: each incoming edge represents an independent alternative method for computing that parameter, so the traversal forks and pursues each edge separately, generating one sub-pathway per alternative. At a **merge node**, the algorithm applies AND logic: all incoming edges are required simultaneously, so the traversal takes the Cartesian product of the alternatives for each input, combining every possible choice for one input with every possible choice for every other. Dynamic programming caches each node's sub-pathways after they are first computed, so a node that appears in multiple branches of the graph — such as the shared `merge_density_grain_form` node, which feeds both elastic modulus and the Srivastava Poisson's ratio method — is only traversed once.

Because `density` is a single shared node feeding both `elastic_modulus` and the Srivastava Poisson's ratio method through the same merge node, the Cartesian-product logic can produce structurally different traversals that resolve to the same combination of methods. Before returning, `find_parameterizations` computes a fingerprint for each traversal — a sorted list of its (parameter, method) pairs — and discards duplicates, so every entry in the final list represents a genuinely distinct recipe. For D11, the four density alternatives combine independently with the four elastic modulus alternatives and the two Poisson's ratio alternatives, yielding 4 × 4 × 2 = 32 unique pathways. `slab_weight` and `slab_weight_shear` each have 4 pathways, one per density method. `slab_weight_shear_with_elasticity` has 32 pathways because it adds elastic modulus and Poisson's ratio availability to the slab-weight branch.

A `Parameterization` object is structurally valid by construction — it was discovered by traversing the graph — but it makes no claim about whether the required measurements are present in any particular pit. That question is answered only at execution time, when the executor reads from the actual `Layer` and `Slab` objects.

---

## Execution

The `execution` module takes parameterizations from the algorithm and runs the actual calculations on real slab data. Where the algorithm works abstractly on the graph structure, the execution module works concretely on `Layer` and `Slab` objects: it reads field measurements from those objects, calls the empirical methods implemented in `layer_parameters`, `slab_parameters`, and `stability_criteria`, and writes the computed values back to the same objects.

The main entry point is **`ExecutionEngine`**. Its `execute_all()` method accepts a slab and a target parameter name, calls `find_parameterizations` internally to obtain the full list of valid pathways, runs each pathway on the slab in turn, and collects the results in a single container. An optional `pathways` argument lets the caller supply a pre-filtered list of `Parameterization` objects; when provided, the engine executes exactly those pathways instead of finding all valid pathways internally. Its `execute_single()` method accepts an explicit (parameter → method) mapping from the caller and runs only the matching pathway, which is useful when a specific combination of methods is required rather than all of them.

### Execution order

Running a parameterization on a slab proceeds in two phases. In the first phase, the executor iterates over each layer in the slab and computes the required layer-level parameters in dependency order: density is always computed first, because elastic modulus, Poisson's ratio, and shear modulus all take density as an input. Each layer is treated independently — the result for one layer does not affect the calculations for any other layer in this phase.

In the second phase, the executor computes the requested slab-level parameter. *A*11, *B*11, *D*11, and *A*55 integrate layer-level properties across the full thickness of the slab, so they cannot be computed until all required layer-level parameters are available on every layer. The slab-weight targets similarly require the selected density pathway to have produced `density_calculated` on every layer before weight is integrated through thickness; the direct-measurement density pathway satisfies this by first copying `density_measured` into `density_calculated`. Roch and WEAC are still available as direct stability-criterion functions for callers that supply the required weak-layer inputs, but they are not exposed as parameter graph targets.

### Missing inputs

A `Parameterization` is a structural claim derived from the graph: it asserts that a particular sequence of methods is a valid route to the target parameter. Whether the input measurements that route requires are actually recorded in a given pit is a separate question, settled only when the executor tries to read them from the `Layer` object. A pit in which grain size was not recorded, for example, will cause the Kim & Jamieson Table 5 density method to fail at runtime for every layer, even though that method forms a perfectly valid pathway in the graph. Constraints on valid ranges produce runtime failures in the same way: the Bergfeld elastic modulus method is only valid for certain grain forms, and the Srivastava Poisson's ratio method requires density above 200 kg/m³; a layer that does not satisfy these conditions returns no result for the affected method.

Failures of this kind are captured without interrupting the execution of other pathways. The executor records every individual method call — whether successful or not — and moves on. For a layer-level target, a pathway is considered to have failed if the target method could not produce a value for every layer in the slab: partial success (the method worked on some layers but not others) is treated as pathway failure, because a pathway specifies a single method applied uniformly across all layers.

### Result structures

Three nested structures carry the results. A **`ComputationTrace`** records a single method call: the parameter it targeted, the method used, the layer index (or `None` for slab-level and weak-layer calculations), the computed output value, a success flag, and an error message if the call failed. A **`PathwayResult`** collects all the computation traces for one pathway together with the computed slab — which by the end of execution holds all layer-level and slab-level parameter values written by the executor — and a record of which method was used for each parameter in this pathway. A `PathwayResult` is marked successful if at least the target parameter was computed; unsuccessful pathways are retained alongside successful ones so that the pattern of failures across the dataset can be examined. The top-level **`ExecutionResults`** container holds all pathway results indexed by a human-readable description of each pathway, and reports cache statistics recording how many density computations were reused across pathways rather than recalculated.

### Configuration

Execution behaviour is controlled by an **`ExecutionConfig`** object passed to `execute_all()` or `execute_single()`. When `verbose` is `True`, the engine prints a progress line for each pathway as it begins, which is useful when monitoring large batch runs over many pits. The `include_method_uncertainty` flag (default `True`) controls whether each empirical method contributes its own regression standard error to the output uncertainty; setting it to `False` retains only the uncertainty propagated from the input field measurements, which is useful for isolating the contribution of measurement error independently of model error. The `weac_timeout_seconds` field is retained only as deprecated compatibility surface; current graph execution does not route WEAC criterion targets through the execution engine.

---

## Slab Weight Input Analysis

The analysis notebook `slab_weight_inputs.ipynb` characterises slab-weight input coverage across the ECTP slab dataset. It focuses on two computable graph targets rather than executing Roch or WEAC criteria through the graph.

**`slab_weight_shear`** reports which slabs have calculated density, layer thickness, and slope angle available across the 4 density pathways. The direct-measurement `data_flow` pathway is counted only when measured density is present and has been written into `density_calculated` by that pathway.

**`slab_weight_shear_with_elasticity`** adds elastic modulus and Poisson's ratio availability on every slab layer, producing the same 32 density × elastic modulus × Poisson's ratio pathway combinations used by D11-style elastic analyses.

The analysis is based on ECTP slabs drawn from the SnowPilot dataset and uses `include_method_uncertainty=False` so that the reported relative uncertainties reflect only propagated field measurement uncertainty, not empirical regression error.

### Coverage definition

*Coverage* is defined as the fraction of ECTP slabs for which **all layers** in the slab have successful calculations for the inputs required by a target pathway. A slab is counted as covered only when every layer passes; partial success is not sufficient because slab-level quantities integrate across the full slab.

For `slab_weight_shear`, the target pathway succeeds only when the selected density method succeeds for every layer, every layer has thickness, and the slab has a slope angle. For `slab_weight_shear_with_elasticity`, every layer must additionally have elastic modulus and Poisson's ratio for the selected method combination. Roch and WEAC criteria remain available as direct functions for analyses that supply the required weak-layer inputs explicitly.
