"""
Parameter graph definition for SnowPyt-MechParams.

This module defines the complete parameter dependency graph, including:
- Layer-level parameters (density, elastic modulus, Poisson's ratio, shear modulus)
- Slab-level parameters (A11, B11, D11, A55 plate theory stiffnesses)

Graph Structure
---------------

Layer-Level:
    snow_pit → measured_* → density → elastic_modulus
                                    → poissons_ratio
                                    → shear_modulus

    snow_pit → measured_layer_thickness (thickness)

Slab-Level:
    measured_layer_thickness → zi (spatial information)
    elastic_modulus + poissons_ratio → merge_E_nu
    
    zi + merge_E_nu → merge_zi_E_nu → D11
    measured_layer_thickness + shear_modulus → merge_hi_G → A55
    measured_layer_thickness + merge_E_nu → merge_hi_E_nu → A11, B11

Methods Available
-----------------

Layer Parameters:

**Density** (kg/m³):
- data_flow: Direct measurement
- geldsetzer: From hand hardness and grain form [Geldsetzer et al. 2009]
- kim_jamieson_table2: From hand hardness and grain form [Kim & Jamieson 2010]
- kim_jamieson_table5: From hand hardness, grain form, and grain size [Kim & Jamieson 2010]

**Elastic Modulus** (MPa):
- bergfeld: From density and grain form [Bergfeld et al. 2023]
- kochle: From density and grain form [Köchle & Schneebeli 2014]
- wautier: From density and grain form [Wautier et al. 2015]
- schottner: From density and grain form [Schöttner et al. 2024]

**Poisson's Ratio** (dimensionless):
- kochle: From grain form only [Köchle & Schneebeli 2014]
- srivastava: From density and grain form [Srivastava et al. 2016]

**Shear Modulus** (MPa):
- wautier: From density and grain form [Wautier et al. 2015]

Slab Parameters (Plate Theory):

**weissgraeber_rosendahl** method calculates all four parameters using classical
laminate theory [Weißgraeber & Rosendahl 2023]:

- **A11** (N/mm): Extensional stiffness
  Formula: Σ [E_i/(1-ν_i²)] * h_i
  
- **B11** (N): Bending-extension coupling stiffness
  Formula: (1/2) * Σ [E_i/(1-ν_i²)] * (z_{i+1}² - z_i²)
  
- **D11** (N·mm): Bending stiffness
  Formula: (1/3) * Σ [E_i/(1-ν_i²)] * (z_{i+1}³ - z_i³)
  
- **A55** (N/mm): Shear stiffness with correction factor κ = 5/6
  Formula: κ * Σ G_i * h_i

where:
- E_i: Elastic modulus of layer i
- ν_i: Poisson's ratio of layer i
- G_i: Shear modulus of layer i
- h_i: Thickness of layer i
- z_i: Vertical coordinate of layer i (from geometric centroid)

Key Concepts
------------

**Layer Properties**: Layer thickness is already available on Layer objects as
`layer.thickness`. The node `measured_layer_thickness` represents it in the graph
but requires no calculation - it is direct data flow from measurements.

**Slab Parameters**: A11, B11, D11, A55 require ALL layers to have necessary
properties computed. The execution engine handles this by completing all
layer-level calculations before attempting slab-level calculations.

**Merge Nodes**: Special nodes that combine multiple inputs:
- zi: Represents spatial/thickness information for layers
- merge_E_nu: Combines E and ν from all layers (for plane-strain modulus)
- merge_zi_E_nu: Combines spatial info with E/ν (for D11 bending calculation)
- merge_hi_G: Combines thickness with shear modulus (for A55)
- merge_hi_E_nu: Combines thickness with E/ν (for A11, B11)

**Shared Density Node**: The ``density`` node is an input to both
``elastic_modulus`` (via ``merge_density_grain_form``) and to the
``srivastava`` Poisson's ratio method (also via ``merge_density_grain_form``).
Because it is a single shared node, any pathway that uses ``srivastava`` for
Poisson's ratio must use the *same* density method as is used for elastic
modulus — there is no independent density choice for Poisson's ratio. This
constrains D11 to 4 density × 4 E × 2 ν = **32 unique pathways**.
``find_parameterizations`` enforces this through deduplication; see
``snowpyt_mechparams.algorithm._method_fingerprint`` for details.

Adding New Methods
------------------

To add a new calculation method:

1. Add the method implementation to the appropriate module in `layer_parameters/`
   or `slab_parameters/`
2. Register the method in `execution/dispatcher.py`
3. Add the method edge to this graph definition
4. Write tests in `tests/`

Example:

```python
# In graph/definitions.py
build_graph.method_edge(merge_d_gf, elastic_modulus, "new_method")

# In execution/dispatcher.py
self._register(MethodSpec(
    parameter="elastic_modulus",
    method_name="new_method",
    level=ParameterLevel.LAYER,
    function=lambda density, grain_form: calculate_elastic_modulus(
        "new_method", density=density, grain_form=grain_form
    ),
    required_inputs=["density", "grain_form"],
    optional_inputs={}
))
```

References
----------
Bergfeld, B., van Herwijnen, A., Bobillier, G., Larose, E., & Gaume, J. (2023).
    Temporal evolution of crack propagation propensity in snow. The Cryosphere,
    17(5), 1487–1502. https://doi.org/10.5194/tc-17-1487-2023

Geldsetzer, T., Jamieson, J. B., & Schweizer, J. (2009). Snow density and crystal
    form. Unpublished work.

Kim, H., & Jamieson, J. B. (2010). Multivariate characterization of avalanche
    weak layers. Cold Regions Science and Technology, 60(3), 202–213.
    https://doi.org/10.1016/j.coldregions.2009.11.001

Köchle, B., & Schneebeli, M. (2014). Three-dimensional microstructure and
    numerical calculation of elastic properties of alpine snow with a focus on
    weak layers. Journal of Glaciology, 60(222), 705–713.
    https://doi.org/10.3189/2014JoG13J220

Schöttner, L., Hagenmuller, P., & Proksch, M. (2024). A micromechanical finite
    element model for density and microstructure evolution during dry snow
    metamorphism. The Cryosphere, 18(4), 1579–1600.
    https://doi.org/10.5194/tc-18-1579-2024

Srivastava, P. K., Mahajan, P., Satyawali, P. K., & Kumar, V. (2016). Observation
    of temperature gradient metamorphism in snow by X-ray computed microtomography.
    Cold Regions Science and Technology, 125, 63–70.
    https://doi.org/10.1016/j.coldregions.2016.01.010

Wautier, A., Geindreau, C., & Flin, F. (2015). Linking snow microstructure to its
    macroscopic elastic stiffness tensor: A numerical homogenization method and its
    application to 3-D images from X-ray tomography. Geophysical Research Letters,
    42(19), 8031–8041. https://doi.org/10.1002/2015GL065227

Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for layered snow
    slabs. The Cryosphere, 17(4), 1475–1496.
    https://doi.org/10.5194/tc-17-1475-2023

See Also
--------
snowpyt_mechparams.algorithm : Functions to find calculation pathways
snowpyt_mechparams.graph.structures : Graph data structures
"""

from snowpyt_mechparams.graph.structures import GraphBuilder

# ==============================================================================
# Initialize builder
# ==============================================================================

build_graph = GraphBuilder()

# ==============================================================================
# STEP 1: Create all parameter nodes
# ==============================================================================

# Snow pit node (root)
snow_pit = build_graph.param("snow_pit")

# Measured parameter nodes (inputs)
measured_density = build_graph.param("measured_density")
measured_hand_hardness = build_graph.param("measured_hand_hardness")
measured_grain_form = build_graph.param("measured_grain_form")
measured_grain_size = build_graph.param("measured_grain_size")

# Layer property nodes (measured, data flow from snow_pit)
measured_layer_thickness = build_graph.param("measured_layer_thickness")  # hi (thickness)

# Calculated layer parameter nodes (outputs)
density = build_graph.param("density", level="layer")
elastic_modulus = build_graph.param("elastic_modulus", level="layer")
poissons_ratio = build_graph.param("poissons_ratio", level="layer")
shear_modulus = build_graph.param("shear_modulus", level="layer")

# Calculated slab parameter nodes (outputs)
A11 = build_graph.param("A11", level="slab")  # Extensional stiffness
B11 = build_graph.param("B11", level="slab")  # Bending-extension coupling
D11 = build_graph.param("D11", level="slab")  # Bending stiffness
A55 = build_graph.param("A55", level="slab")  # Shear stiffness

# ==============================================================================
# STEP 2: Create merge nodes for shared input combinations
# ==============================================================================

# --- Layer-level merge nodes ---

# Merge node for: hand_hardness + grain_form
# Used by: density.geldsetzer, density.kim_jamieson_table2
merge_hh_gf = build_graph.merge("merge_hand_hardness_grain_form")

# Merge node for: hand_hardness + grain_form + grain_size
# Used by: density.kim_jamieson_table5
merge_hh_gf_gs = build_graph.merge("merge_hand_hardness_grain_form_grain_size")

# Merge node for: density + grain_form
# Used by: elastic_modulus.{bergfeld,kochle,wautier,schottner}, 
#          poissons_ratio.srivastava, shear_modulus.wautier
merge_d_gf = build_graph.merge("merge_density_grain_form")

# --- Slab-level merge nodes ---

# Merge node for: spatial/thickness information
# Used to represent layer positions (calculated from thickness)
zi = build_graph.merge("zi")

# Merge node for: E and nu from all layers
# Used by: merge_zi_E_nu (for D11), merge_hi_E_nu (for A11, B11)
merge_E_nu = build_graph.merge("merge_E_nu")

# Merge node for: spatial info + E + nu (for D11)
# D11 needs layer positions because bending stiffness depends on distance
# from neutral axis (z² weighting)
merge_zi_E_nu = build_graph.merge("merge_zi_E_nu")

# Merge node for: thickness + shear modulus (for A55)
# A55 = κ * Σ G_i * h_i
merge_hi_G = build_graph.merge("merge_hi_G")

# Merge node for: thickness + E + nu (for A11, B11)
# A11 and B11 involve integrating plane-strain modulus over thickness
merge_hi_E_nu = build_graph.merge("merge_hi_E_nu")

# ==============================================================================
# STEP 3: Build the graph structure - Layer level
# ==============================================================================

# Snow pit to measured parameters (data flow)
build_graph.flow(snow_pit, measured_density)
build_graph.flow(snow_pit, measured_hand_hardness)
build_graph.flow(snow_pit, measured_grain_form)
build_graph.flow(snow_pit, measured_grain_size)

# Snow pit to layer properties (data flow)
build_graph.flow(snow_pit, measured_layer_thickness)

# --- Density calculation paths ---

# Direct measurement path
build_graph.flow(measured_density, density)

# Path 1: hand_hardness + grain_form -> density
build_graph.flow(measured_hand_hardness, merge_hh_gf)
build_graph.flow(measured_grain_form, merge_hh_gf)
build_graph.method_edge(merge_hh_gf, density, "geldsetzer")
build_graph.method_edge(merge_hh_gf, density, "kim_jamieson_table2")

# Path 2: (hand_hardness + grain_form) + grain_size -> density
# This merge node takes the RESULT of merge_hh_gf and combines it with grain_size
build_graph.flow(merge_hh_gf, merge_hh_gf_gs)
build_graph.flow(measured_grain_size, merge_hh_gf_gs)
build_graph.method_edge(merge_hh_gf_gs, density, "kim_jamieson_table5")

# --- Elastic modulus calculation paths ---

# Setup merge node: density + grain_form
build_graph.flow(density, merge_d_gf)
build_graph.flow(measured_grain_form, merge_d_gf)

# Methods using density + grain_form
build_graph.method_edge(merge_d_gf, elastic_modulus, "bergfeld")
build_graph.method_edge(merge_d_gf, elastic_modulus, "kochle")
build_graph.method_edge(merge_d_gf, elastic_modulus, "wautier")
build_graph.method_edge(merge_d_gf, elastic_modulus, "schottner")

# --- Poisson's ratio calculation paths ---

# Single input method: grain_form only
build_graph.method_edge(measured_grain_form, poissons_ratio, "kochle")

# Method using density + grain_form (reuses merge_d_gf, same as elastic modulus)
build_graph.method_edge(merge_d_gf, poissons_ratio, "srivastava")

# --- Shear modulus calculation paths ---

# Method using density + grain_form (reuses merge_d_gf)
build_graph.method_edge(merge_d_gf, shear_modulus, "wautier")

# ==============================================================================
# STEP 4: Build the graph structure - Slab level
# ==============================================================================

# --- Merge 1: zi (spatial/thickness information) ---
build_graph.flow(measured_layer_thickness, zi)

# --- Merge 2: merge_E_nu (elastic properties from all layers) ---
build_graph.flow(elastic_modulus, merge_E_nu)
build_graph.flow(poissons_ratio, merge_E_nu)

# --- Merge 3: merge_zi_E_nu (spatial + elastic properties for D11) ---
build_graph.flow(zi, merge_zi_E_nu)
build_graph.flow(merge_E_nu, merge_zi_E_nu)

# --- Merge 4: merge_hi_G (thickness + shear for A55) ---
build_graph.flow(measured_layer_thickness, merge_hi_G)
build_graph.flow(shear_modulus, merge_hi_G)

# --- Merge 5: merge_hi_E_nu (thickness + elastic properties for A11, B11) ---
build_graph.flow(measured_layer_thickness, merge_hi_E_nu)
build_graph.flow(merge_E_nu, merge_hi_E_nu)

# --- Slab parameter calculations ---

# D11: Requires spatial position + E + nu for all layers
build_graph.method_edge(merge_zi_E_nu, D11, "weissgraeber_rosendahl")

# A55: Requires thickness + G for all layers
build_graph.method_edge(merge_hi_G, A55, "weissgraeber_rosendahl")

# A11: Requires thickness + E + nu for all layers
build_graph.method_edge(merge_hi_E_nu, A11, "weissgraeber_rosendahl")

# B11: Similar to A11 (uses same merge, different calculation)
build_graph.method_edge(merge_hi_E_nu, B11, "weissgraeber_rosendahl")

# ==============================================================================
# Build the final graph
# ==============================================================================

graph = build_graph.build()

# ==============================================================================
# Parameter classification sets — derived from node-level tags
# ==============================================================================
# Adding a new parameter to the graph with level="layer" or level="slab"
# automatically makes it appear in the corresponding set here.

LAYER_PARAMS: frozenset = graph.layer_params
SLAB_PARAMS: frozenset = graph.slab_params

# ==============================================================================
# Export all nodes for convenient access
# ==============================================================================

__all__ = [
    'graph',
    # Root
    'snow_pit',
    # Measured parameters
    'measured_density',
    'measured_hand_hardness',
    'measured_grain_form',
    'measured_grain_size',
    # Layer properties (measured)
    'measured_layer_thickness',
    # Layer parameters (calculated)
    'density',
    'elastic_modulus',
    'poissons_ratio',
    'shear_modulus',
    # Slab parameters (calculated)
    'A11',
    'B11',
    'D11',
    'A55',
    # Parameter classification sets
    'LAYER_PARAMS',
    'SLAB_PARAMS',
]
