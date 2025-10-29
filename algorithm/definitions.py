"""
Implementation of parameter calculation graph using data structures.

This module creates a directed graph representing all possible calculation paths
for snow mechanical parameters. The graph includes:
- Parameter nodes: represent measured or calculated parameters
- Merge nodes: combine multiple parameters as inputs to a method
- Edges: represent data flow or method transformations
"""

from data_structures import Node, Edge, Graph

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
# STEP 2: Create merge nodes for methods requiring multiple inputs
# ==============================================================================

# Density calculation merge nodes
# Method: geldsetzer (requires hand_hardness, grain_form)
merge_density_geldsetzer = Node(type="merge", parameter="merge_density_geldsetzer")

# Method: kim_jamieson_table2 (requires hand_hardness, grain_form)
merge_density_kim_jamieson_table2 = Node(type="merge", parameter="merge_density_kim_jamieson_table2")

# Method: kim_jamieson_table5 (requires hand_hardness, grain_form, grain_size)
merge_density_kim_jamieson_table5 = Node(type="merge", parameter="merge_density_kim_jamieson_table5")

# Elastic modulus calculation merge nodes
# Method: bergfeld (requires density, grain_form)
merge_elastic_modulus_bergfeld = Node(type="merge", parameter="merge_elastic_modulus_bergfeld")

# Method: kochle (requires density, grain_form)
merge_elastic_modulus_kochle = Node(type="merge", parameter="merge_elastic_modulus_kochle")

# Method: wautier (requires density, grain_form)
merge_elastic_modulus_wautier = Node(type="merge", parameter="merge_elastic_modulus_wautier")

# Poisson's ratio calculation merge nodes
# Method: kochle (requires grain_form only - no merge needed, single input)

# Method: srivastava (requires density, grain_form)
merge_poissons_ratio_srivastava = Node(type="merge", parameter="merge_poissons_ratio_srivastava")

# Method: from_elastic_and_shear_modulus (requires elastic_modulus, shear_modulus)
merge_poissons_ratio_from_E_G = Node(type="merge", parameter="merge_poissons_ratio_from_E_G")

# Shear modulus calculation merge nodes
# Method: wautier (requires density, grain_form)
merge_shear_modulus_wautier = Node(type="merge", parameter="merge_shear_modulus_wautier")

# Method: from_elastic_modulus_and_poissons_ratio (requires elastic_modulus, poissons_ratio)
merge_shear_modulus_from_E_nu = Node(type="merge", parameter="merge_shear_modulus_from_E_nu")

# ==============================================================================
# STEP 3: Create edges for density calculations
# ==============================================================================

# Direct edge from measured_density to density (if density is directly measured)
edge_measured_density_to_density = Edge(
    start=measured_density,
    end=density,
    method_name=None  # Direct data flow, no transformation
)

# Edges for geldsetzer method
edge_hand_hardness_to_merge_geldsetzer = Edge(
    start=measured_hand_hardness,
    end=merge_density_geldsetzer,
    method_name=None  # Data flow to merge node
)
edge_grain_form_to_merge_geldsetzer = Edge(
    start=measured_grain_form,
    end=merge_density_geldsetzer,
    method_name=None  # Data flow to merge node
)
edge_merge_geldsetzer_to_density = Edge(
    start=merge_density_geldsetzer,
    end=density,
    method_name="geldsetzer"  # Method: _calculate_density_geldsetzer
)

# Edges for kim_jamieson_table2 method
edge_hand_hardness_to_merge_kim_table2 = Edge(
    start=measured_hand_hardness,
    end=merge_density_kim_jamieson_table2,
    method_name=None
)
edge_grain_form_to_merge_kim_table2 = Edge(
    start=measured_grain_form,
    end=merge_density_kim_jamieson_table2,
    method_name=None
)
edge_merge_kim_table2_to_density = Edge(
    start=merge_density_kim_jamieson_table2,
    end=density,
    method_name="kim_jamieson_table2"  # Method: _calculate_density_kim_jamieson_table2
)

# Edges for kim_jamieson_table5 method
edge_hand_hardness_to_merge_kim_table5 = Edge(
    start=measured_hand_hardness,
    end=merge_density_kim_jamieson_table5,
    method_name=None
)
edge_grain_form_to_merge_kim_table5 = Edge(
    start=measured_grain_form,
    end=merge_density_kim_jamieson_table5,
    method_name=None
)
edge_grain_size_to_merge_kim_table5 = Edge(
    start=measured_grain_size,
    end=merge_density_kim_jamieson_table5,
    method_name=None
)
edge_merge_kim_table5_to_density = Edge(
    start=merge_density_kim_jamieson_table5,
    end=density,
    method_name="kim_jamieson_table5"  # Method: _calculate_density_kim_jamieson_table5
)

# ==============================================================================
# STEP 4: Create edges for elastic modulus calculations
# ==============================================================================

# Edges for bergfeld method
edge_density_to_merge_bergfeld = Edge(
    start=density,
    end=merge_elastic_modulus_bergfeld,
    method_name=None
)
edge_grain_form_to_merge_bergfeld = Edge(
    start=measured_grain_form,
    end=merge_elastic_modulus_bergfeld,
    method_name=None
)
edge_merge_bergfeld_to_elastic_modulus = Edge(
    start=merge_elastic_modulus_bergfeld,
    end=elastic_modulus,
    method_name="bergfeld"  # Method: _calculate_elastic_modulus_bergfeld
)

# Edges for kochle method
edge_density_to_merge_kochle = Edge(
    start=density,
    end=merge_elastic_modulus_kochle,
    method_name=None
)
edge_grain_form_to_merge_kochle = Edge(
    start=measured_grain_form,
    end=merge_elastic_modulus_kochle,
    method_name=None
)
edge_merge_kochle_to_elastic_modulus = Edge(
    start=merge_elastic_modulus_kochle,
    end=elastic_modulus,
    method_name="kochle"  # Method: _calculate_elastic_modulus_kochle
)

# Edges for wautier method
edge_density_to_merge_wautier_E = Edge(
    start=density,
    end=merge_elastic_modulus_wautier,
    method_name=None
)
edge_grain_form_to_merge_wautier_E = Edge(
    start=measured_grain_form,
    end=merge_elastic_modulus_wautier,
    method_name=None
)
edge_merge_wautier_E_to_elastic_modulus = Edge(
    start=merge_elastic_modulus_wautier,
    end=elastic_modulus,
    method_name="wautier"  # Method: _calculate_elastic_modulus_wautier
)

# ==============================================================================
# STEP 5: Create edges for Poisson's ratio calculations
# ==============================================================================

# Edges for kochle method (single input, no merge node needed)
edge_grain_form_to_poissons_ratio_kochle = Edge(
    start=measured_grain_form,
    end=poissons_ratio,
    method_name="kochle"  # Method: _calculate_poissons_ratio_kochle
)

# Edges for srivastava method
edge_density_to_merge_srivastava = Edge(
    start=density,
    end=merge_poissons_ratio_srivastava,
    method_name=None
)
edge_grain_form_to_merge_srivastava = Edge(
    start=measured_grain_form,
    end=merge_poissons_ratio_srivastava,
    method_name=None
)
edge_merge_srivastava_to_poissons_ratio = Edge(
    start=merge_poissons_ratio_srivastava,
    end=poissons_ratio,
    method_name="srivastava"  # Method: _calculate_poissons_ratio_srivastava
)

# Edges for from_elastic_and_shear_modulus method
edge_elastic_modulus_to_merge_E_G = Edge(
    start=elastic_modulus,
    end=merge_poissons_ratio_from_E_G,
    method_name=None
)
edge_shear_modulus_to_merge_E_G = Edge(
    start=shear_modulus,
    end=merge_poissons_ratio_from_E_G,
    method_name=None
)
edge_merge_E_G_to_poissons_ratio = Edge(
    start=merge_poissons_ratio_from_E_G,
    end=poissons_ratio,
    method_name="from_elastic_and_shear_modulus"  # Method: _calculate_poissons_ratio_from_elastic_and_shear_modulus
)

# ==============================================================================
# STEP 6: Create edges for shear modulus calculations
# ==============================================================================

# Edges for wautier method
edge_density_to_merge_wautier_G = Edge(
    start=density,
    end=merge_shear_modulus_wautier,
    method_name=None
)
edge_grain_form_to_merge_wautier_G = Edge(
    start=measured_grain_form,
    end=merge_shear_modulus_wautier,
    method_name=None
)
edge_merge_wautier_G_to_shear_modulus = Edge(
    start=merge_shear_modulus_wautier,
    end=shear_modulus,
    method_name="wautier"  # Method: _calculate_shear_modulus_wautier
)

# Edges for from_elastic_modulus_and_poissons_ratio method
edge_elastic_modulus_to_merge_E_nu = Edge(
    start=elastic_modulus,
    end=merge_shear_modulus_from_E_nu,
    method_name=None
)
edge_poissons_ratio_to_merge_E_nu = Edge(
    start=poissons_ratio,
    end=merge_shear_modulus_from_E_nu,
    method_name=None
)
edge_merge_E_nu_to_shear_modulus = Edge(
    start=merge_shear_modulus_from_E_nu,
    end=shear_modulus,
    method_name="from_elastic_modulus_and_poissons_ratio"  # Method: _calculate_shear_modulus_wautier_from_elastic_modulus_and_poissons_ratio
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
    # Merge nodes for density
    merge_density_geldsetzer,
    merge_density_kim_jamieson_table2,
    merge_density_kim_jamieson_table5,
    # Merge nodes for elastic modulus
    merge_elastic_modulus_bergfeld,
    merge_elastic_modulus_kochle,
    merge_elastic_modulus_wautier,
    # Merge nodes for Poisson's ratio
    merge_poissons_ratio_srivastava,
    merge_poissons_ratio_from_E_G,
    # Merge nodes for shear modulus
    merge_shear_modulus_wautier,
    merge_shear_modulus_from_E_nu,
]

# Collect all edges
all_edges = [
    # Density edges
    edge_measured_density_to_density,
    edge_hand_hardness_to_merge_geldsetzer,
    edge_grain_form_to_merge_geldsetzer,
    edge_merge_geldsetzer_to_density,
    edge_hand_hardness_to_merge_kim_table2,
    edge_grain_form_to_merge_kim_table2,
    edge_merge_kim_table2_to_density,
    edge_hand_hardness_to_merge_kim_table5,
    edge_grain_form_to_merge_kim_table5,
    edge_grain_size_to_merge_kim_table5,
    edge_merge_kim_table5_to_density,
    # Elastic modulus edges
    edge_density_to_merge_bergfeld,
    edge_grain_form_to_merge_bergfeld,
    edge_merge_bergfeld_to_elastic_modulus,
    edge_density_to_merge_kochle,
    edge_grain_form_to_merge_kochle,
    edge_merge_kochle_to_elastic_modulus,
    edge_density_to_merge_wautier_E,
    edge_grain_form_to_merge_wautier_E,
    edge_merge_wautier_E_to_elastic_modulus,
    # Poisson's ratio edges
    edge_grain_form_to_poissons_ratio_kochle,
    edge_density_to_merge_srivastava,
    edge_grain_form_to_merge_srivastava,
    edge_merge_srivastava_to_poissons_ratio,
    edge_elastic_modulus_to_merge_E_G,
    edge_shear_modulus_to_merge_E_G,
    edge_merge_E_G_to_poissons_ratio,
    # Shear modulus edges
    edge_density_to_merge_wautier_G,
    edge_grain_form_to_merge_wautier_G,
    edge_merge_wautier_G_to_shear_modulus,
    edge_elastic_modulus_to_merge_E_nu,
    edge_poissons_ratio_to_merge_E_nu,
    edge_merge_E_nu_to_shear_modulus,
]

# Create the final graph
graph = Graph(nodes=all_nodes, edges=all_edges)
