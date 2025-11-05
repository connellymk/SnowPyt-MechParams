"""
Implementation of parameter calculation graph using data structures.

This module creates a directed graph representing all possible calculation paths
for snow mechanical parameters. The graph includes:
- Parameter nodes: represent measured or calculated parameters
- Merge nodes: combine multiple parameters as inputs to a method
- Edges: represent data flow or method transformations

Key principle: Merge nodes are shared between methods that use the same input
parameters, regardless of which output parameter they calculate.
"""

from data_structures import GraphBuilder

# Initialize builder
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

# Calculated parameter nodes (outputs)
density = build_graph.param("density")
elastic_modulus = build_graph.param("elastic_modulus")
poissons_ratio = build_graph.param("poissons_ratio")
shear_modulus = build_graph.param("shear_modulus")

# ==============================================================================
# STEP 2: Create merge nodes for shared input combinations
# ==============================================================================

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

# ==============================================================================
# STEP 3: Build the graph structure
# ==============================================================================

# Snow pit to measured parameters (data flow)
build_graph.flow(snow_pit, measured_density)
build_graph.flow(snow_pit, measured_hand_hardness)
build_graph.flow(snow_pit, measured_grain_form)
build_graph.flow(snow_pit, measured_grain_size)

# --- Density calculation paths ---

# Direct measurement path
build_graph.flow(measured_density, density)

# Path 1: hand_hardness + grain_form -> density
build_graph.flow(measured_hand_hardness, merge_hh_gf)
build_graph.flow(measured_grain_form, merge_hh_gf)
build_graph.method_edge(merge_hh_gf, density, "geldsetzer")
build_graph.method_edge(merge_hh_gf, density, "kim_jamieson_table2")

# Path 2: hand_hardness + grain_form + grain_size -> density
build_graph.flow(measured_hand_hardness, merge_hh_gf_gs)
build_graph.flow(measured_grain_form, merge_hh_gf_gs)
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

# Single input method
build_graph.method_edge(measured_grain_form, poissons_ratio, "kochle")

# Method using density + grain_form (reuses merge_d_gf)
build_graph.method_edge(merge_d_gf, poissons_ratio, "srivastava")

# --- Shear modulus calculation paths ---

# Method using density + grain_form (reuses merge_d_gf)
build_graph.method_edge(merge_d_gf, shear_modulus, "wautier")

# ==============================================================================
# Build the final graph
# ==============================================================================

graph = build_graph.build()
