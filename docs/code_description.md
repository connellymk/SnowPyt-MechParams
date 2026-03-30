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

A lightweight container for the six fracture and strength parameters required by the WEAC skier stability criterion: total fracture energy (*G*_c), mode-I and mode-II fracture toughness (*G*_Ic, *G*_IIc), tensile normal strength (*σ*_c), shear strength (*τ*_c), and compressive strength (*σ*_comp). All fields are optional — WEAC uses its own built-in defaults for any that are not provided.

This structure is a SnowPyt-specific representation and is distinct from WEAC's own internal weak layer object.

#### `Slab`

Represents the snow slab sitting above a weak layer, as an ordered list of `Layer` objects from the surface down to (but not including) the weak layer. In addition to the layers, the slab holds:

- the **weak layer** (`weak_layer: Optional[WeakLayer]`): a single object that carries both the layer's field measurements (thickness, density, hand hardness, grain form, grain size) and the six fracture/strength parameters (`G_c`, `G_Ic`, `G_IIc`, `sigma_c`, `tau_c`, `sigma_comp`). The `WeakLayer` class extends `Layer`, so all `Layer` attributes are available on it. The fracture/strength fields start as `None` and are populated by the execution engine when a stability criterion target is requested.
- **slope angle**
- **metadata** recording which stability test result was used to define the weak layer (test type, score, failure depth), and how many test results of that type exist in the source pit
- **slab stiffness parameters** (*A11*, *A55*, *B11*, *D11*) computed by the `slab_parameters` module and stored here for use in stability calculations
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
- **`stability_criteria/`** — uses the complete `Slab` (stiffness parameters, slope angle, and `WeakLayer` fracture properties) to evaluate avalanche release potential, storing criterion results back on the `Slab`.

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

## Weak Layer Parameterizations

The `weak_layer_parameters` module provides methods for estimating the six fracture and strength parameters of the weak layer that are required by WEAC's coupled fracture criterion. These parameters characterize how the weak layer resists cracking and collapse, and are stored in the `WeakLayer` data model before being passed to the stability criteria.

Three of the six parameters have only one method available, which returns a constant reference value from Weißgraeber & Rosendahl (2023). These constants were used when fitting WEAC to field experiments and serve as a sensible starting point when no site-specific measurements are available. They are also WEAC's built-in defaults. Parameters with additional methods offer density-based alternatives that can draw on pit-measured or estimated layer density.

### Total Fracture Energy (*G*_c)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023)

Returns the reference value *G*_c = 1.0 J/m². This is the total energy per unit area required to propagate a crack through the weak layer under the mixed-mode loading assumed by WEAC, and is the default value used by WEAC when no measurement is available. No uncertainty is assigned. No inputs are required.

### Mode-I Fracture Toughness (*G*_Ic)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023)

Returns the reference value *G*_Ic = 0.56 J/m². Mode I refers to crack opening driven by tensile normal stress — the weak layer being pulled apart perpendicular to its plane. This is WEAC's built-in default. No uncertainty is assigned. No inputs are required.

### Mode-II Fracture Toughness (*G*_IIc)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023)

Returns the reference value *G*_IIc = 0.79 J/m². Mode II refers to crack sliding driven by shear stress along the weak layer plane, the dominant mode in slab avalanche initiation. This is WEAC's built-in default. No uncertainty is assigned. No inputs are required.

### Shear Strength (τ_c)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023)

Returns the reference value τ_c = 5.09 kPa. This is the shear stress at which the weak layer fails under pure shear loading, used alongside the tensile normal strength in WEAC's coupled tensile–shear failure criterion. This is WEAC's built-in default. No uncertainty is assigned. No inputs are required.

### Tensile Normal Strength (σ_c+)

**`weissgraeber_rosendahl`** (Weißgraeber & Rosendahl, 2023)

Returns the reference value σ_c+ = 6.16 kPa. This is the tensile stress at which the weak layer fails under pure opening, used alongside shear strength in the coupled failure criterion. This is WEAC's built-in default. No uncertainty is assigned. No inputs are required.

**`sigrist`** (Sigrist, 2006; cited in Weißgraeber & Rosendahl, 2023, Eq. 22)

A power-law relationship based on density: σ_c+ = 240 · (ρ/ρ_ice)²·⁴⁴ kPa. The coefficients were derived from fracture-mechanical experiments on snow samples. Because tensile strength scales with density to a power greater than 2, it is strongly sensitive to density — increasing roughly 35-fold from fresh snow (∼100 kg/m³) to dense snow (∼400 kg/m³). No method uncertainty is added (standard errors not reported). Valid for densities between 0 and 917 kg/m³. Input required: `density_weak_layer` (the estimated density of the weak layer itself). When this method is selected, the executor first estimates `density_weak_layer` from the weak layer's hand hardness and grain form using the same density methods available for slab layers, then passes the result to `calculate_sigma_c_plus("sigrist")`.

### Compressive Strength (σ_c−)

**`reiweger`** (Reiweger et al., 2015; cited in Weißgraeber & Rosendahl, 2023)

Returns the reference value σ_c− = 2.6 kPa. This is a characteristic compressive strength for weak snow layers under rapid loading — much lower than for consolidated slab layers — and is used to assess the potential for weak-layer collapse under compressive stress. It is also WEAC's built-in default. No uncertainty is assigned. The method accepts an optional density argument for API consistency but does not use it. No inputs are required.

**`mellor`** (Mellor, 1975)

A power-law relationship based on density: σ_c− = 5000 · (ρ/ρ_ice)²·⁵ kPa. This is a general parameterization for compressive snow strength compiled from experimental data by Mellor (1975), appropriate for a wider range of snow types than the weak-layer-specific Reiweger value. The coefficient (5000 kPa) and exponent (2.5) are representative values for rapid loading; the original compilation reports a range of approximately C = 3000–10000 kPa and n = 2.0–3.0 depending on loading rate and snow type. No method uncertainty is added (standard errors not reported). Valid for densities between 0 and 917 kg/m³. Input required: `density_weak_layer` (same mechanism as the sigrist method above).

---

## Stability Criteria

The `stability_criteria` module evaluates avalanche release potential using the mechanical parameters computed for the slab and weak layer. Two criteria are implemented, representing different physical approaches: the Roch criterion is a classical limit-equilibrium method based on the ratio of weak-layer shear strength to the gravitational shear stress acting on the weak layer; the WEAC criterion uses fracture mechanics to assess whether a crack in the weak layer will nucleate under the combined influence of a skier load and the slab's own weight.

The two criteria handle measurement uncertainty differently. The Roch criterion preserves uncertain-number arithmetic throughout its calculation, so the returned stability index carries an uncertainty estimate propagated from the input layer densities, thicknesses, slope angle, and supplied strength value. The WEAC criterion strips all uncertain numbers to their nominal values at the adapter boundary, because the iterative eigensystem solver inside the `weac` package is incompatible with that arithmetic; the WEAC results are therefore plain floats with no associated uncertainty.

---

### Roch Stability Index

**`calculate_roch`** (Roch, 1966; Föhn, 1987)

Computes the gravitational shear stress on the weak layer and evaluates the ratio of shear strength to that stress. The shear stress is τ = (Σᵢ ρᵢ hᵢ) · g · sin θ, where ρᵢ and hᵢ are the calculated density (kg/m³) and thickness (m) of each slab layer, and θ is the slope angle; this is the component of the slab's weight acting parallel to the slope surface and tending to slide the slab along the weak layer. The weak-layer shear strength τ_c must be supplied by the caller and is typically drawn from the parameters computed by the `weak_layer_parameters` module.

Two variants of the stability index are available depending on whether an additional skier stress is provided. In the natural terrain variant (Roch, 1966), the index is S_r = τ_c / τ; values below 1.0 indicate that the gravitational load already exceeds the shear strength and the slope is critically stressed under its own weight alone. In the skier-loaded variant (Föhn, 1987), the index is S_a = τ_c / (τ + δτ), where δτ is the additional shear stress applied by the skier, supplied by the caller; values below 1.0 indicate that the combined gravitational and skier load exceeds the weak-layer shear strength. The natural variant is undefined on flat terrain where τ = 0; the skier variant requires a finite, nonzero δτ. The function returns `None` if the slope angle is missing, any slab layer lacks a thickness or calculated density, the computed shear stress is not a finite number, or these conditions on τ or δτ are not met.

In the parameter graph, only the natural variant is exposed as a graph node: *s*_r (method `roch_natural`), reached via the merge node `merge_roch_inputs`, which aggregates only the layer-level density parameter and the weak-layer shear strength τ_c. Because τ_c is a single constant (from `weissgraeber_rosendahl`) and density has four methods, there are exactly 4 distinct pathways — one per density method. Elastic modulus, Poisson's ratio, shear modulus, and the slab stiffness parameters are not required. The skier variant (S_a) is not exposed as a graph node; it is computed by calling `calculate_roch` directly with a caller-supplied δτ after the engine has populated τ_c. The shear strength τ_c is read from `slab.weak_layer.tau_c` in kPa and passed directly to `calculate_roch`, which converts to Pa internally (τ_c_pa = τ_c × 1000) before computing the index. Results are written to `slab.roch_result`.

---

### WEAC Skier Criterion

**`calculate_weac_skier`** (Weißgraeber & Rosendahl, 2023)

Applies the Weak Layer Anticrack Nucleation (WEAC) coupled fracture criterion to assess whether a skier load triggers the onset of crack propagation in the weak layer. The physical model, described in Weißgraeber & Rosendahl (2023, *The Cryosphere*, 17, 1475–1496), represents the stratified snow slab as a layered beam resting on the weak layer, which is treated as an elastic foundation with independent normal and shear stiffnesses. A skier applies a point load to the slab surface, and the model computes the resulting normal and shear stress distribution in the weak layer and the energy release rate of a potential crack of progressively growing length. Anticrack nucleation is predicted when both a stress criterion (the combined normal and shear stresses at the crack tip reach the weak-layer strength envelope) and an energy criterion (the energy release rate reaches the fracture toughness) are simultaneously satisfied. The coupled nature of the criterion means that neither stress nor energy alone is sufficient: the crack must be able to grow in the sense of both conditions at once.

The adapter translates SnowPyt slab data into the input format expected by the `weac` package and runs the coupled criterion iteratively to find the critical configuration. All four mechanical parameters (elastic modulus, shear modulus, Poisson's ratio, and density) and the thickness of every slab layer must be populated; layer thicknesses are converted from centimetres to millimetres at the interface. Weak-layer fracture and strength parameters are taken from `slab.weak_layer`; any parameter absent from that object falls back to WEAC's built-in reference values from Weißgraeber & Rosendahl (2023). Individual parameters can also be overridden by keyword arguments passed directly to the function, which take precedence over both `slab.weak_layer` and the built-in defaults. The model geometry is set up as two equal-length adjacent segments — by default, each as long as the total slab thickness in millimetres — one carrying the skier mass and one unloaded; both segments rest on the weak-layer foundation. The skier mass defaults to `STANDARD_SKIER_MASS_KG` (80 kg) but can be changed by the caller.

The primary output is `g_delta`, the value of the coupled stability criterion: values of 1.0 or greater indicate that anticrack nucleation is predicted for the given skier mass. The result also reports the critical skier mass at which nucleation would be expected, the anticrack half-length at the critical configuration (in mm), the mode-I and mode-II energy release rates *G*_I and *G*_II and their sum *G*_total (in J/m²), and the distances from the current state to both the stress failure envelope and the energy-release-rate failure envelope. The `converged` field records whether the iterative algorithm reached its solution reliably; results from non-converged runs should be treated with caution. On numerically pathological slabs the solver may encounter a recursion depth limit or, if a per-slab time limit is configured, a timeout; in either case the function returns `None` rather than an unreliable result. The `weac` package is an optional dependency and must be installed separately; calling the function without it raises an `ImportError`.

---

## Parameter Graph

The `graph` module defines a directed graph that encodes every possible way to compute snow mechanical parameters from raw pit observations. Each node in the graph represents either a measured quantity or a calculated parameter, and each edge represents either the transfer of a value from one parameter to the next or a specific empirical method that computes one parameter from others. Together, the nodes and edges make all dependency relationships explicit, so the algorithm can automatically discover every valid pathway from measured inputs to any target parameter without those pathways being written out by hand.

The graph connects the five computational modules — `models`, `layer_parameters`, `slab_parameters`, `weak_layer_parameters`, and `stability_criteria` — by placing their inputs and outputs as nodes and their calculation methods as edges. This is the mechanism that allows the package to report 32 distinct pathways to D11: rather than maintaining a hand-written list of 32 method combinations, the algorithm traverses the graph and discovers them from its structure. When a new empirical method is added to the package, a single new edge in the graph is sufficient; the algorithm then finds every affected pathway automatically.

### Node types

The graph contains two kinds of node. A **parameter node** represents a named quantity — either a raw field measurement or a calculated result. The single root of the graph is a parameter node called `snow_pit`, representing the pit observation as a whole and having no incoming edges. Five measured-input parameter nodes flow from the root: `measured_density`, `measured_hand_hardness`, `measured_grain_form`, `measured_grain_size`, and `measured_layer_thickness`. All calculated outputs — density, elastic modulus, Poisson's ratio, and shear modulus at the layer level; *A*11, *B*11, *D*11, and *A*55 at the slab level; the seven weak-layer parameters (`G_c`, `G_Ic`, `G_IIc`, `sigma_c`, `tau_c`, `sigma_comp`, and the new `density_weak_layer`); and the stability criterion outputs *g*_delta (WEAC skier criterion) and *s*_r (Roch natural stability index) — are also parameter nodes, each tagged with a computation level that tells the execution engine at which phase of the pipeline it can first be computed. The `density_weak_layer` node represents the estimated density of the weak layer itself (as distinct from `density`, which is computed per slab layer), and serves as the input to the density-dependent strength methods `sigrist` (for `sigma_c`) and `mellor` (for `sigma_comp`).

A **merge node** represents the convergence of two or more inputs into a single method call. Because most empirical methods require more than one input, a merge node is interposed between the parameter nodes supplying those inputs and the method edge that produces the result. For example, the four elastic modulus methods each require both density and grain form: the merge node `merge_density_grain_form` collects these two inputs and sits upstream of the four method edges that lead to the elastic modulus parameter node. At the slab level, separate merge nodes aggregate the layer-level results needed for each stiffness integral: `merge_E_nu` combines elastic modulus and Poisson's ratio from all layers, `merge_zi_E_nu` adds layer-position information required for the *D*11 bending integral, `merge_hi_G` combines thickness and shear modulus for the *A*55 shear integral, and `merge_hi_E_nu` combines thickness and the plane-strain modulus for the *A*11 and *B*11 integrals. The large `merge_weac_inputs` node aggregates all four layer-level mechanical parameters together with all seven weak-layer parameters before the WEAC criterion can be evaluated. The `merge_roch_inputs` node is a leaner counterpart that collects only the density parameter and the weak-layer shear strength τ_c, which are the sole prerequisites for both Roch stability index variants. The weak-layer density infrastructure introduces two additional merge nodes: `merge_wl_hand_hardness_grain_form` combines the weak layer's hand hardness and grain form inputs (mirroring the slab-layer `merge_hand_hardness_grain_form`), and `merge_wl_hand_hardness_grain_form_grain_size` adds grain size for the kim_jamieson_table5 density method.

### Edge types

The graph contains two kinds of edge. A **data-flow edge** connects one node to another and carries no method name, indicating that a quantity is passed through without any calculation. The edges from `snow_pit` to the five measured-input nodes, from `measured_density` directly to the `density` node (representing the case where density was measured directly with a cutter), and from parameter nodes into the merge nodes that require them, are all data-flow edges.

A **method edge** connects a merge node (or in a few cases a single parameter node) to the parameter node it computes, and carries the name of the empirical method that performs the calculation. The edge from `merge_density_grain_form` labelled `bergfeld` arriving at `elastic_modulus` is one example; the edge from `measured_grain_form` labelled `kochle` arriving at `poissons_ratio` is another — the Köchle & Schneebeli (2014) Poisson's ratio method requires grain form but not density, so it departs from the measured grain form node directly rather than from `merge_density_grain_form`. Similarly, each weak-layer parameter is connected to the `snow_pit` node by a method edge labelled with the source reference, requiring no additional measured inputs beyond what the pit record already supplies.

### Graph topology

The graph flows in a single direction from the root toward the target parameters. From `snow_pit`, data-flow edges fan out to all five measured-input parameter nodes. From there, the layer-level parameters are built up in stages: density can be reached via the direct-measurement data-flow edge (when a density cutter was used) or via one of three empirical methods that work from hand hardness, grain form, and optionally grain size; elastic modulus, Poisson's ratio, and shear modulus each follow from density and grain form through the `merge_density_grain_form` node, except that the kochle Poisson's ratio method branches from grain form alone. Once all layer-level parameters are available, the graph continues upward: the slab stiffness parameters are computed through the slab-level merge nodes, and the WEAC stability criterion is computed through `merge_weac_inputs`. The leaf nodes — the parameters that a user can request as targets — are the layer-level parameters, the slab stiffness parameters, the weak-layer parameters, *g*_delta, and *s*_r. The Roch path is a short circuit through the graph: from `snow_pit`, density flows through one of four density method edges to the `density` node, τ_c flows from `snow_pit` via the `weissgraeber_rosendahl` constant, both converge at `merge_roch_inputs`, and a single method edge leads to *s*_r. No slab stiffness computation is involved. The weak-layer density path mirrors the slab-layer density path: `density_weak_layer` can be reached via direct measurement or via one of the three estimation methods using the weak layer's hand hardness and grain form, and then feeds the `sigrist` and `mellor` method edges to `sigma_c` and `sigma_comp` respectively.

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

Because `density` is a single shared node feeding both `elastic_modulus` and the Srivastava Poisson's ratio method through the same merge node, the Cartesian-product logic can produce structurally different traversals that resolve to the same combination of methods. Before returning, `find_parameterizations` computes a fingerprint for each traversal — a sorted list of its (parameter, method) pairs — and discards duplicates, so every entry in the final list represents a genuinely distinct recipe. For D11, the four density alternatives combine independently with the four elastic modulus alternatives and the two Poisson's ratio alternatives, yielding 4 × 4 × 2 = 32 unique pathways. Because shear modulus is not required for the *D*11 bending integral (it enters only into *A*55), it does not contribute to the pathway count. For the Roch stability index target *s*_r, the pathway count is 4: τ_c is a single constant and density has four methods, so 4 × 1 = 4 pathways. Elastic modulus, Poisson's ratio, shear modulus, and the slab stiffness parameters are not traversed. For the WEAC stability criterion *g*_delta, the pathway count is 416: 4 (slab density) × 4 (elastic modulus) × 2 (Poisson's ratio) × 13 (sigma_c × sigma_comp × density_weak_layer combinations). The 13 comes from the four alternatives for (sigma_c, sigma_comp): σ_c=weissgraeber_rosendahl and σ_comp=reiweger (1 combination, no weak-layer density needed); σ_c=sigrist and σ_comp=reiweger (4 combinations, one per density_weak_layer method); σ_c=weissgraeber_rosendahl and σ_comp=mellor (4 combinations); and σ_c=sigrist and σ_comp=mellor (4 combinations, sharing the same density_weak_layer choice). The deduplication step ensures that pathways differing only in the shared density_weak_layer method are counted correctly.

A `Parameterization` object is structurally valid by construction — it was discovered by traversing the graph — but it makes no claim about whether the required measurements are present in any particular pit. That question is answered only at execution time, when the executor reads from the actual `Layer` and `Slab` objects.

---

## Execution

The `execution` module takes parameterizations from the algorithm and runs the actual calculations on real slab data. Where the algorithm works abstractly on the graph structure, the execution module works concretely on `Layer` and `Slab` objects: it reads field measurements from those objects, calls the empirical methods implemented in `layer_parameters`, `slab_parameters`, `weak_layer_parameters`, and `stability_criteria`, and writes the computed values back to the same objects.

The main entry point is **`ExecutionEngine`**. Its `execute_all()` method accepts a slab and a target parameter name, calls `find_parameterizations` internally to obtain the full list of valid pathways, runs each pathway on the slab in turn, and collects the results in a single container. An optional `pathways` argument lets the caller supply a pre-filtered list of `Parameterization` objects; when provided, the engine executes exactly those pathways instead of finding all valid pathways internally — useful for running a specific subset such as the 32 slab-only *g*_delta pathways without triggering the full 416-pathway combinatorial space. Its `execute_single()` method accepts an explicit (parameter → method) mapping from the caller and runs only the matching pathway, which is useful when a specific combination of methods is required rather than all of them.

### Execution order

Running a parameterization on a slab proceeds in two phases. In the first phase, the executor iterates over each layer in the slab and computes the required layer-level parameters in dependency order: density is always computed first, because elastic modulus, Poisson's ratio, and shear modulus all take density as an input. Each layer is treated independently — the result for one layer does not affect the calculations for any other layer in this phase.

In the second phase, the executor computes the requested slab-level parameter. *A*11, *B*11, *D*11, and *A*55 integrate layer-level properties across the full thickness of the slab, so they cannot be computed until all layer-level parameters are available on every layer. The two-phase order guarantees this prerequisite is met before the slab-level calculation is attempted. For weak-layer or stability targets, the executor additionally computes the required weak-layer fracture and strength parameters — populating the `weak_layer` field on the slab — before running the stability criterion. Within the weak-layer phase, `density_weak_layer` is always computed first (before any other weak-layer parameter), because the density-dependent methods `sigrist` and `mellor` read `slab.weak_layer.density_calculated`, which is written by the `density_weak_layer` step. For the WEAC criterion (*g*_delta), the result is stored in `slab.weac_result`; for the Roch natural criterion (*s*_r), in `slab.roch_result`. A single slab can carry both stability results simultaneously if both targets are executed.

### Missing inputs

A `Parameterization` is a structural claim derived from the graph: it asserts that a particular sequence of methods is a valid route to the target parameter. Whether the input measurements that route requires are actually recorded in a given pit is a separate question, settled only when the executor tries to read them from the `Layer` object. A pit in which grain size was not recorded, for example, will cause the Kim & Jamieson Table 5 density method to fail at runtime for every layer, even though that method forms a perfectly valid pathway in the graph. Constraints on valid ranges produce runtime failures in the same way: the Bergfeld elastic modulus method is only valid for certain grain forms, and the Srivastava Poisson's ratio method requires density above 200 kg/m³; a layer that does not satisfy these conditions returns no result for the affected method.

Failures of this kind are captured without interrupting the execution of other pathways. The executor records every individual method call — whether successful or not — and moves on. For a layer-level target, a pathway is considered to have failed if the target method could not produce a value for every layer in the slab: partial success (the method worked on some layers but not others) is treated as pathway failure, because a pathway specifies a single method applied uniformly across all layers.

### Result structures

Three nested structures carry the results. A **`ComputationTrace`** records a single method call: the parameter it targeted, the method used, the layer index (or `None` for slab-level and weak-layer calculations), the computed output value, a success flag, and an error message if the call failed. A **`PathwayResult`** collects all the computation traces for one pathway together with the computed slab — which by the end of execution holds all layer-level and slab-level parameter values written by the executor — and a record of which method was used for each parameter in this pathway. A `PathwayResult` is marked successful if at least the target parameter was computed; unsuccessful pathways are retained alongside successful ones so that the pattern of failures across the dataset can be examined. The top-level **`ExecutionResults`** container holds all pathway results indexed by a human-readable description of each pathway, and reports cache statistics recording how many density computations were reused across pathways rather than recalculated.

### Configuration

Execution behaviour is controlled by an **`ExecutionConfig`** object passed to `execute_all()` or `execute_single()`. When `verbose` is `True`, the engine prints a progress line for each pathway as it begins, which is useful when monitoring large batch runs over many pits. The `include_method_uncertainty` flag (default `True`) controls whether each empirical method contributes its own regression standard error to the output uncertainty; setting it to `False` retains only the uncertainty propagated from the input field measurements, which is useful for isolating the contribution of measurement error independently of model error. For the WEAC stability criterion, `weac_timeout_seconds` sets a per-slab wall-clock time limit on the iterative solver; slabs on which the solver does not converge within the budget are treated as pathway failures and excluded from the results, preventing a numerically pathological pit from blocking the processing of an entire dataset.

---

## Stability Criteria Analysis

Three analysis notebooks examine how the Roch natural criterion (*S*_r) and the WEAC skier criterion (*g*_delta) behave in practice on the full ECTP slab dataset. The first notebook, `stability_criteria_inputs.ipynb`, characterises the **slab-level input requirements**: how many distinct slab-layer calculation pathways reach each criterion, what fraction of ECTP slabs have all required slab inputs available (coverage), and how the per-parameter nominal values and relative uncertainties vary by method. The second notebook, `stability_criteria_weak_layer.ipynb`, is a focused comparison of the **13 weak-layer parameterisation combinations**: with the slab fixed to a single high-coverage pathway, it reports how many slabs have the necessary weak-layer measurements available and how the choice of σ_c and σ_comp method affects the g_delta output. The third notebook, `stability_criteria_outputs.ipynb`, characterises the **outputs**: how often each criterion successfully returns a stability index, how those outputs are distributed, and how the two criteria agree or disagree when both produce a result for the same slab.

The analysis is based on **14,776 ECTP slabs** drawn from 50,278 snow pits (371,429 layers total). Slabs were identified using the `ECTP_failure_layer` strategy — one slab per propagating ECTP result. All calculations use `include_method_uncertainty=False` so that the reported relative uncertainties reflect only the propagation of field measurement uncertainties, not regression model error.

**Analysis design.** Although the full parameter graph contains **416** *g*_delta pathways (32 slab combinations × 13 weak-layer combinations), the two analyses are intentionally separated. The slab analysis runs the 32 pathways that use the original constant weak-layer defaults (σ_c = `weissgraeber_rosendahl`, σ_comp = `reiweger`), which are always available and never constrain coverage. The weak-layer analysis then holds the slab fixed to the highest-coverage slab pathway and varies only the 13 weak-layer combinations, isolating the contribution of weak-layer measurement availability from the slab-layer coverage question. Combining all 416 pathways is possible in principle and is equivalent to the Cartesian product of the two separate analyses.

---

### Input Parameter Analysis (`stability_criteria_inputs.ipynb`)

#### Pathway counts

The two criteria require fundamentally different sets of layer-level inputs, which leads to very different pathway counts. The Roch natural criterion requires only density (to compute the gravitational shear stress τ) and the weak-layer shear strength τ_c (a single constant from `weissgraeber_rosendahl`, always available). Because τ_c contributes no alternatives, the pathway count equals the number of density methods: **4 pathways** (one each for `data_flow`, `geldsetzer`, `kim_jamieson_table2`, and `kim_jamieson_table5`). The WEAC skier criterion requires all four layer-level mechanical parameters — density, elastic modulus, Poisson's ratio, and shear modulus — for every slab layer, plus weak-layer strength parameters. With four density methods, four elastic modulus methods, two Poisson's ratio methods, and one shear modulus method, there are **32 slab-level pathways**. The full graph contains 416 distinct g_delta pathways once the 13 weak-layer combinations are included (32 × 13), but the slab and weak-layer dimensions are analysed separately (see above). This notebook runs only the 32 slab pathways, with weak-layer parameters fixed to the constant defaults.

#### Coverage definition

*Coverage* is defined as the fraction of ECTP slabs for which **all layers** in the slab have a successful calculation for a given parameter. A slab is counted as covered by a pathway only when every layer passes — partial success is not sufficient, because the stability calculation requires complete information about the slab. For the Roch criterion, this reduces to full density coverage across all slab layers. For WEAC, all four parameters must succeed on all layers simultaneously.

#### Roch natural input coverage

The four Roch pathways achieve substantially different coverage rates, determined entirely by how widely each density method applies across the grain forms and hand hardness values present in the dataset:

| Density method | Coverage (slabs / 14,776) | Coverage rate | Mean density (kg/m³) | Mean rel. uncertainty |
|---|---|---|---|---|
| `kim_jamieson_table2` | 5,951 | 40.3% | 177.2 | 19.1% |
| `geldsetzer` | 4,539 | 30.7% | 162.1 | 19.4% |
| `kim_jamieson_table5` | 1,145 | 7.7% | 159.4 | 21.4% |
| `data_flow` | 109 | 0.7% | 190.9 | 10.0% |

The `data_flow` pathway, which applies only when density was measured directly with a cutter, achieves the lowest coverage because direct density measurements are rarely recorded for every layer in the slab. It also yields the lowest relative uncertainty (10.0%), reflecting the absence of regression model spread. The three estimation methods all carry around 19–21% relative uncertainty from the propagated field measurement errors. The `kim_jamieson_table5` method has the highest uncertainty partly because it requires grain size to be recorded, restricting it to a narrower subset of pits, and the `kim_jamieson_table2` method reaches the most slabs of the three estimators because its supported grain forms span the widest range of the observations in the dataset.

Because τ_c is a constant that does not depend on any pit measurement, all-inputs coverage for each Roch pathway is identical to its density coverage.

#### WEAC skier input coverage

WEAC input coverage is substantially lower than Roch input coverage, because all four layer-level parameters must succeed on every layer simultaneously. The elastic modulus, Poisson's ratio, and shear modulus methods each have their own grain form restrictions and density validity ranges, and these restrictions compound: a slab that passes the density check for a given pathway may still fail the elastic modulus or Poisson's ratio check for one or more of its layers. The best achievable input coverage across all 32 slab pathways is **5.0%** (approximately 739 slabs), compared with 40.3% for the best Roch pathway — a gap of **35.3 percentage points**. The top pathways by all-inputs coverage share a common structure: `kim_jamieson_table2` or `geldsetzer` for density (the widest grain form coverage) combined with an elastic modulus method that applies to the same grain forms. Pathways that require `kim_jamieson_table5` density (which additionally requires grain size) achieve no valid WEAC inputs across the entire dataset. These figures reflect the slab analysis with constant weak-layer defaults; coverage for the density-dependent weak-layer methods is reported separately in `stability_criteria_weak_layer.ipynb`.

---

### Weak-Layer Pathway Comparison (`stability_criteria_weak_layer.ipynb`)

This notebook isolates the effect of the 13 weak-layer method combinations on the *g*_delta output by holding the slab parameterisation constant. The slab is fixed to the highest-coverage slab pathway: `kim_jamieson_table2` density, `wautier` elastic modulus, `kochle` Poisson's ratio.

#### The 13 weak-layer combinations

The 13 combinations arise from the choices for (σ_c method, σ_comp method, density_weak_layer method):

| σ_c | σ_comp | density_wl | Notes |
|---|---|---|---|
| `weissgraeber_rosendahl` | `reiweger` | — | constant, always available |
| `weissgraeber_rosendahl` | `mellor` | `geldsetzer` / `kim_jamieson_table2` / `kim_jamieson_table5` / `data_flow` | 4 combinations |
| `sigrist` | `reiweger` | `geldsetzer` / `kim_jamieson_table2` / `kim_jamieson_table5` / `data_flow` | 4 combinations |
| `sigrist` | `mellor` | `geldsetzer` / `kim_jamieson_table2` / `kim_jamieson_table5` / `data_flow` | 4 combinations |

The `density_weak_layer` input for the non-constant combinations is estimated from the weak layer's own measured hand hardness, grain form, and (for `kim_jamieson_table5`) grain size — using the same density methods as for slab layers, but applied to the single weak-layer record rather than to each slab layer.

#### Coverage and output rates

For the constant combination (`weissgraeber_rosendahl` + `reiweger`), the slab-level constraint is the binding one: the slab coverage under the fixed `kim_jamieson_table2 → wautier → kochle` pathway determines the fraction of slabs that can even reach the WEAC solver. For the 12 density-dependent combinations, coverage is additionally limited by the availability of weak-layer measurements: the weak layer must have hand hardness and grain form recorded (for `geldsetzer` and `kim_jamieson_table2`), or also grain size (for `kim_jamieson_table5`), or a directly measured density (for `data_flow`). The notebook reports, for each of the 13 combinations, how many slabs have both the slab inputs and the weak-layer inputs required, and how many of those produce a valid *g*_delta.

---

### Output Comparison (`stability_criteria_outputs.ipynb`)

#### Success rates

Having all required inputs is necessary but not sufficient for a criterion to return a valid output. The Roch criterion can fail if the resulting shear stress or stability index is not a finite number (for instance, on a slab with zero slope or missing thickness). The WEAC criterion additionally depends on the iterative eigensystem solver converging within the configured time budget (`weac_timeout_seconds=5.0` in this analysis); slabs on which the solver times out or encounters a numerical pathology return no result.

For the Roch criterion, the output success rate is close to but slightly below the input coverage rate for each pathway, with the `data_flow` pathway showing perfect correspondence:

| Density method | Valid S_r (slabs / 14,776) | Output success rate |
|---|---|---|
| `kim_jamieson_table2` | 5,512 | 37.3% |
| `geldsetzer` | 4,229 | 28.6% |
| `kim_jamieson_table5` | 1,080 | 7.3% |
| `data_flow` | 109 | 0.7% |

For the WEAC criterion, the gap between input coverage and output success is severe. Even the highest-coverage pathways produced valid *g*_delta values for only a handful of slabs: the best-performing pathways (`data_flow → schottner → kochle` and `kim_jamieson_table2 → schottner → kochle`) yielded at most 12 valid results across the full dataset (0.1%), despite having far more slabs with all inputs available. Most pathways returned zero or single-digit valid results. This reflects the difficulty of the WEAC iterative solver on the snow structure and slab geometry typical of the dataset: even when all four mechanical parameters are computable for all layers, the coupled stress and energy conditions are rarely satisfied simultaneously within the solver's convergence and time constraints. These figures reflect the 32 slab pathways with constant weak-layer defaults.

#### Output value distributions

For the Roch criterion, the *S*_sk distributions are right-skewed across all four pathways, with the bulk of the density concentrated below the instability threshold of *S*_sk = 1.0. The three estimation-based pathways produce similar distribution shapes, consistent with their comparable mean density values. The `data_flow` pathway produces a higher mean *S*_sk, consistent with its higher mean measured density (190.9 kg/m³); denser snow yields a larger gravitational shear stress τ, which — all else being equal — reduces *S*_sk.

Because valid WEAC *g*_delta outputs are so sparse (at most 12 per pathway), the *g*_delta distributions are not statistically informative; the violin plots for WEAC are included for completeness but cannot be interpreted as representative of the full population of ECTP slabs.

#### Classification agreement

A direct comparison of the two criteria is possible only for slabs where both return a valid result, matched on `slab_id` and `density_method` (so that density is computed identically for both criteria in the matched pair). Multiple WEAC pathways per slab are included — one row per slab × density method × E-mod method × ν method combination. Across the 32 slab pathways this yields 131 matched records.

Because the WEAC output set is so sparse, all 131 matched slabs are classified as stable by the Roch criterion (*S*_sk ≥ 1). WEAC, however, classifies 84 of these 131 as unstable (*g*_delta ≥ 1) and only 47 as stable (*g*_delta < 1). The overall agreement rate is **35.9%** (47 of 131 records). The disagreement is entirely of one type: slabs that Roch classifies as stable but WEAC classifies as unstable. No slab in the matched set is classified as unstable by Roch and stable by WEAC.

This pattern suggests that WEAC is more sensitive to the conditions required for anticrack nucleation than the Roch limit-equilibrium criterion — or, equivalently, that the gravitational shear stress already exceeding the weak-layer shear strength (the Roch failure condition) is a more demanding threshold than the WEAC coupled stress-and-energy nucleation condition. However, the small and self-selected nature of the matched set — the slabs for which WEAC happens to converge — means this comparison cannot be taken as representative of the broader ECTP slab population, and the finding should be interpreted with caution.
