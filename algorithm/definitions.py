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

from data_structures import Node, Edge, Graph

all_nodes = []
all_edges = []

# ==============================================================================
# STEP 1: Create all parameter nodes
# ==============================================================================

# Starting measured parameter nodes (inputs)
measured_density = Node(type="parameter", parameter="measured_density")
measured_hand_hardness = Node(type="parameter", parameter="measured_hand_hardness")
measured_grain_form = Node(type="parameter", parameter="measured_grain_form")
measured_grain_size = Node(type="parameter", parameter="measured_grain_size")

# Calculated parameter nodes
density = Node(type="parameter", parameter="density")
elastic_modulus = Node(type="parameter", parameter="elastic_modulus")
poissons_ratio = Node(type="parameter", parameter="poissons_ratio")
shear_modulus = Node(type="parameter", parameter="shear_modulus")

# ==============================================================================
# STEP 2: Create merge nodes based on unique input parameter combinations
# ==============================================================================

# Merge node for: hand_hardness + grain_form
# Used by: density.geldsetzer, density.kim_jamieson_table2
merge_hand_hardness_grain_form = Node(type="merge", parameter="merge_hand_hardness_grain_form")

# Merge node for: hand_hardness + grain_form + grain_size
# Used by: density.kim_jamieson_table5
merge_hand_hardness_grain_form_grain_size = Node(type="merge", parameter="merge_hand_hardness_grain_form_grain_size")

# Merge node for: density + grain_form
# Used by: elastic_modulus.bergfeld, elastic_modulus.kochle, elastic_modulus.wautier,
#          poissons_ratio.srivastava, shear_modulus.wautier
merge_density_grain_form = Node(type="merge", parameter="merge_density_grain_form")

# Merge node for: elastic_modulus + shear_modulus
# Used by: poissons_ratio.from_elastic_and_shear_modulus
merge_elastic_modulus_shear_modulus = Node(type="merge", parameter="merge_elastic_modulus_shear_modulus")

# Merge node for: elastic_modulus + poissons_ratio
# Used by: shear_modulus.from_elastic_modulus_and_poissons_ratio
merge_elastic_modulus_poissons_ratio = Node(type="merge", parameter="merge_elastic_modulus_poissons_ratio")

# ==============================================================================
# STEP 3: Create edges for density calculations
# ==============================================================================

# Direct edge from measured_density to density (if density is directly measured)
edge_measured_density_to_density = Edge(
    start=measured_density,
    end=density,
    method_name=None  # Direct data flow, no transformation
)

# Edges to merge_hand_hardness_grain_form (shared by geldsetzer and kim_jamieson_table2)
edge_hand_hardness_to_merge_hh_gf = Edge(
    start=measured_hand_hardness,
    end=merge_hand_hardness_grain_form,
    method_name=None
)
edge_grain_form_to_merge_hh_gf = Edge(
    start=measured_grain_form,
    end=merge_hand_hardness_grain_form,
    method_name=None
)

# Edge from merge node to density using geldsetzer method
edge_merge_hh_gf_to_density_geldsetzer = Edge(
    start=merge_hand_hardness_grain_form,
    end=density,
    method_name="geldsetzer"
)

# Edge from merge node to density using kim_jamieson_table2 method
edge_merge_hh_gf_to_density_kim_table2 = Edge(
    start=merge_hand_hardness_grain_form,
    end=density,
    method_name="kim_jamieson_table2"
)

# Edges to merge_hand_hardness_grain_form_grain_size (kim_jamieson_table5 only)
edge_hand_hardness_to_merge_hh_gf_gs = Edge(
    start=measured_hand_hardness,
    end=merge_hand_hardness_grain_form_grain_size,
    method_name=None
)
edge_grain_form_to_merge_hh_gf_gs = Edge(
    start=measured_grain_form,
    end=merge_hand_hardness_grain_form_grain_size,
    method_name=None
)
edge_grain_size_to_merge_hh_gf_gs = Edge(
    start=measured_grain_size,
    end=merge_hand_hardness_grain_form_grain_size,
    method_name=None
)

# Edge from merge node to density using kim_jamieson_table5 method
edge_merge_hh_gf_gs_to_density_kim_table5 = Edge(
    start=merge_hand_hardness_grain_form_grain_size,
    end=density,
    method_name="kim_jamieson_table5"
)

# ==============================================================================
# STEP 4: Create edges for elastic modulus calculations
# ==============================================================================

# Edges to merge_density_grain_form (shared by multiple methods)
edge_density_to_merge_d_gf = Edge(
    start=density,
    end=merge_density_grain_form,
    method_name=None
)
edge_grain_form_to_merge_d_gf = Edge(
    start=measured_grain_form,
    end=merge_density_grain_form,
    method_name=None
)

# Edge from merge node to elastic_modulus using bergfeld method
edge_merge_d_gf_to_elastic_modulus_bergfeld = Edge(
    start=merge_density_grain_form,
    end=elastic_modulus,
    method_name="bergfeld"
)

# Edge from merge node to elastic_modulus using kochle method
edge_merge_d_gf_to_elastic_modulus_kochle = Edge(
    start=merge_density_grain_form,
    end=elastic_modulus,
    method_name="kochle"
)

# Edge from merge node to elastic_modulus using wautier method
edge_merge_d_gf_to_elastic_modulus_wautier = Edge(
    start=merge_density_grain_form,
    end=elastic_modulus,
    method_name="wautier"
)

# ==============================================================================
# STEP 5: Create edges for Poisson's ratio calculations
# ==============================================================================

# Edge for kochle method (single input, no merge node needed)
edge_grain_form_to_poissons_ratio_kochle = Edge(
    start=measured_grain_form,
    end=poissons_ratio,
    method_name="kochle"
)

# Edge from merge_density_grain_form to poissons_ratio using srivastava method
# (reuses the same merge node as elastic modulus methods)
edge_merge_d_gf_to_poissons_ratio_srivastava = Edge(
    start=merge_density_grain_form,
    end=poissons_ratio,
    method_name="srivastava"
)

# Edges to merge_elastic_modulus_shear_modulus
edge_elastic_modulus_to_merge_E_G = Edge(
    start=elastic_modulus,
    end=merge_elastic_modulus_shear_modulus,
    method_name=None
)
edge_shear_modulus_to_merge_E_G = Edge(
    start=shear_modulus,
    end=merge_elastic_modulus_shear_modulus,
    method_name=None
)

# Edge from merge node to poissons_ratio
edge_merge_E_G_to_poissons_ratio = Edge(
    start=merge_elastic_modulus_shear_modulus,
    end=poissons_ratio,
    method_name="from_elastic_and_shear_modulus"
)

# ==============================================================================
# STEP 6: Create edges for shear modulus calculations
# ==============================================================================

# Edge from merge_density_grain_form to shear_modulus using wautier method
# (reuses the same merge node as elastic modulus and poissons_ratio methods)
edge_merge_d_gf_to_shear_modulus_wautier = Edge(
    start=merge_density_grain_form,
    end=shear_modulus,
    method_name="wautier"
)

# Edges to merge_elastic_modulus_poissons_ratio
edge_elastic_modulus_to_merge_E_nu = Edge(
    start=elastic_modulus,
    end=merge_elastic_modulus_poissons_ratio,
    method_name=None
)
edge_poissons_ratio_to_merge_E_nu = Edge(
    start=poissons_ratio,
    end=merge_elastic_modulus_poissons_ratio,
    method_name=None
)

# Edge from merge node to shear_modulus
edge_merge_E_nu_to_shear_modulus = Edge(
    start=merge_elastic_modulus_poissons_ratio,
    end=shear_modulus,
    method_name="from_elastic_modulus_and_poissons_ratio"
)

# ==============================================================================
# STEP 7: Create the complete graph
# ==============================================================================

# Collect all nodes
all_nodes = [
    # Measured parameter nodes
    measured_density,
    measured_hand_hardness,
    measured_grain_form,
    measured_grain_size,
    # Calculated parameter nodes
    density,
    elastic_modulus,
    poissons_ratio,
    shear_modulus,
    # Merge nodes (organized by input parameter combination)
    merge_hand_hardness_grain_form,
    merge_hand_hardness_grain_form_grain_size,
    merge_density_grain_form,
    merge_elastic_modulus_shear_modulus,
    merge_elastic_modulus_poissons_ratio,
]

# Collect all edges
all_edges = [
    # Direct density measurement
    edge_measured_density_to_density,
    
    # Density calculations via hand_hardness + grain_form
    edge_hand_hardness_to_merge_hh_gf,
    edge_grain_form_to_merge_hh_gf,
    edge_merge_hh_gf_to_density_geldsetzer,
    edge_merge_hh_gf_to_density_kim_table2,
    
    # Density calculation via hand_hardness + grain_form + grain_size
    edge_hand_hardness_to_merge_hh_gf_gs,
    edge_grain_form_to_merge_hh_gf_gs,
    edge_grain_size_to_merge_hh_gf_gs,
    edge_merge_hh_gf_gs_to_density_kim_table5,
    
    # Elastic modulus calculations via density + grain_form
    edge_density_to_merge_d_gf,
    edge_grain_form_to_merge_d_gf,
    edge_merge_d_gf_to_elastic_modulus_bergfeld,
    edge_merge_d_gf_to_elastic_modulus_kochle,
    edge_merge_d_gf_to_elastic_modulus_wautier,
    
    # Poisson's ratio calculations
    edge_grain_form_to_poissons_ratio_kochle,
    edge_merge_d_gf_to_poissons_ratio_srivastava,  # Reuses merge_density_grain_form
    edge_elastic_modulus_to_merge_E_G,
    edge_shear_modulus_to_merge_E_G,
    edge_merge_E_G_to_poissons_ratio,
    
    # Shear modulus calculations
    edge_merge_d_gf_to_shear_modulus_wautier,  # Reuses merge_density_grain_form
    edge_elastic_modulus_to_merge_E_nu,
    edge_poissons_ratio_to_merge_E_nu,
    edge_merge_E_nu_to_shear_modulus,
]

# Create the final graph
graph = Graph(nodes=all_nodes, edges=all_edges)
