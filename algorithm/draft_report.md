# Enumerating Possible Parameterizations for Mechanical Parameters of Snow Slabs from Available Field Measurements

## Abstract

This report presents a novel algorithmic application for identifying valid calculation sequences (parameterizations) in snow mechanics and avalanche forecasting. The problem arises from the need to derive mechanical properties (such as elastic modulus and shear strength) from basic field measurements in snow pit observations, where multiple empirical methods exist for each calculation step. We model this as a Directed Acyclic Graph (DAG) where nodes represent physical parameters and edges represent computational methods. We implement a recursive search algorithm optimized with Dynamic Programming (memoization) to traverse this network. The algorithm distinguishes between "OR-logic" parameter nodes and "AND-logic" merge nodes, utilizing Cartesian products to synthesize valid subgraphs from the target parameter back to the source inputs. Applied to a graph of snow mechanical parameters, the algorithm successfully identifies all valid parameterizations: 4 for density, 16 for elastic modulus, and 5 for Poisson's ratio. This approach efficiently handles the combinatorial explosion of potential calculation paths, ensuring all valid scientific models are discoverable from a given dataset.

## Introduction

Will a snowy slope avalanche? One scientific approach to answering this question is the development of mechanical models of avalanche release and snow stability. These mechanical models seek to apply established mechanical theory to snow, by developing relationships between mechanical parameters, such as the elastic modulus and density of snow slab layers, and measures of stability. For example, a comparison of the slab shear load and the weak layer shear strength.

However, these mechanical parameters can be difficult or impossible to measure in the field. Avalanche professionals often rely on field measurements that are easy to capture, such as hand hardness and snow profile, and in-situ stability tests that simulate components of the avalanche release process. Some research has been done to connect common field measurements to the mechanical parameters that form the basis of the mechanical models.

SnowPilot (snowpilot.org) is a free, open-source software designed to help users graph, record, and store snowpit data (Chabot et al., 2016). The SnowPilot database currently contains data from over 65,000 snowpits, collected by snow recreationists and professionals around the world. As part of a previous project, we developed the SnowPylot python library, that enables researches to import and structure data from the SnowPilot database within Python, facilitating the use of Python tools and methods for analysis.

The motivation behind an ongoing research project in collaboration with Sam Verplanck is to advance a more mechanistic approach to avalanche forecasting by connecting the available snowpit observations in SnowPilot to methods for estimating mechanical parameters from those measurements. Then, to use the estimated mechanical parameters as the inputs for mechanical models of avalanche release and slope stability. By comparing the output of the mechanical models to the recorded stability test results and observations taken at known avalanche sites, we hope to evaluate the applicability and effectiveness of the methods used to estimate mechanical parameters, and the mechanical models of stability in forecasting avalanche release.

In several cases, there are many ways to calculate a specific parameter, given a set of available input parameters and methods for parameterization. In addition, some parameters rely on other parameters as inputs. We are interested in comparing the results of different parameterizations when applied to the Snow Pilot dataset. Specifically, we would like to compare the results of the calculated values of the specified parameter, the number of samples to which the parameterization can be successfully applied, and the relative uncertainty of the results.

This paper describes an algorithm that returns the set of every possible parameterization for a specified parameter, given the defined set of possible starting parameters (available measurements from snow pits) and methods. 

## Problem Formulation

### Graph Representation

We define the parameter definitions and methods as a Directed Acyclic Graph (DAG), $G = (V,E)$, with data flowing from raw field measurements to calculated parameters. There are two distinct types of vertices that represent distinct logical behavior:

**Parameter Nodes** ($V_P$): These nodes represent field measurements and mechanical parameters. In the context of the algorithm, these nodes function as OR-gates. When traversing backwards from a parameter node, only one incoming edge can be selected per parameterization.

**Merge Nodes** ($V_M$): These nodes represent the aggregation of multiple inputs required to implement the method represented by their outgoing edge. In the context of the algorithm, these nodes function as AND-gates. When traversing backwards from a merge node, all incoming edges must be included in the parameterization.

**Source Node** ($S$): The source node $S$ is the Snow Pit Observation. All path trees must terminate at the snow pit observation to be valid.

### Problem Statement

A parameterization is defined as the set of input parameters and methods used to calculate a specific parameter. Because multiple input branches converge at merge nodes, the solution structure forms a tree rather than a simple path. We refer to these as *path trees*.

**Algorithm Goal**: Given a target node $t \in V$, find the set of all valid subgraphs $G' \subseteq G$ such that:
1. $t$ is the root of $G'$.
2. The only leaf of $G'$ is the source node $S$.
3. All logical constraints of $V_P$ and $V_M$ are satisfied within $G'$.

## Algorithm Design

The algorithm employs backward recursive traversal with memoization. Starting from target node $t$, we recursively trace paths back to source $S$, building path trees that respect the dependency structure.

### Key Design Principles

- **Backward traversal**: Following reverse topological order naturally respects dependencies
- **Memoization**: Caching results at each node avoids recomputing when nodes are reached via multiple paths
- **Heterogeneous recursion**: Different recursive rules for parameter vs. merge nodes implement OR vs. AND logic

### Recursive Logic

For a node $v$, let $\text{PathTrees}(v)$ = set of all path tree structures from root to $v$.

**Base case**: 
$$\text{PathTrees}(\text{root}) = \{\text{empty tree}\}$$

**Recursive case for parameter nodes (OR logic)**:
$$\text{PathTrees}(v) = \bigcup_{\text{for each incoming edge } e \text{ from } u} \text{extend}(\text{PathTrees}(u), e)$$
where $\text{extend}$ denotes adding edge $e$ to each tree from $\text{PathTrees}(u)$

**Recursive case for merge nodes (AND logic)**:
$$\text{PathTrees}(v) = \text{PathTrees}(u_1) \times \text{PathTrees}(u_2) \times \ldots \times \text{PathTrees}(u_n)$$
where $u_1, \ldots, u_n$ are all predecessor nodes (Cartesian product)

### Pseudocode 
```
FIND-PARAMETERIZATIONS(G, target, root):
    memo ← empty hash table
    
    BACKTRACK(v):
        if v in memo:
            return memo[v]
        
        if v == root:
            return [EmptyPathTree(root)]
        
        all_trees ← []
        
        if v.type == PARAMETER:
            // OR-logic: try each incoming edge independently
            for each edge e = (u, v) ∈ E_in(v):
                label ← e.method_name if exists else "data_flow"
                source_trees ← BACKTRACK(u)
                for each T in source_trees:
                    new_tree ← CreateTree(v, [(T, label)])
                    all_trees.append(new_tree)
        
        else if v.type == MERGE:
            // AND-logic: Cartesian product of all inputs
            input_tree_lists ← []
            for each edge e = (u, v) ∈ E_in(v):
                label ← e.method_name if exists else "data_flow"
                source_trees ← BACKTRACK(u)
                trees_with_labels ← [(T, label) for T in source_trees]
                input_tree_lists.append(trees_with_labels)
            
            combinations ← CARTESIAN-PRODUCT(input_tree_lists)
            for each combo in combinations:
                new_tree ← CreateMergeTree(v, combo)
                all_trees.append(new_tree)
        
        memo[v] ← all_trees
        return all_trees
    
    path_trees ← BACKTRACK(target)
    return [TREE-TO-PARAMETERIZATION(T) for T in path_trees]

CARTESIAN-PRODUCT(lists):
    if lists is empty:
        return [[]]
    result ← []
    for each item in lists[0]:
        for each rest_combo in CARTESIAN-PRODUCT(lists[1:]):
            result.append([item] + rest_combo)
    return result
```

## Proof of Correctness

We prove the algorithm correctly finds all valid parameterizations by structural induction on the DAG.

**Base case**: For $v = S$, the algorithm returns a single empty tree, which correctly represents the source node with no dependencies.

**Inductive Hypothesis (IH)**: Assume BACKTRACK$(u)$ correctly returns all valid path trees for any predecessor node $u$.

**Inductive Step - Parameter Nodes (OR-logic)**: A valid parameterization through $v$ uses exactly one incoming edge. The algorithm explores each edge independently, and for each, combines it with all valid subtrees from the predecessor (correct by IH). Thus all valid combinations are found.

**Inductive Step - Merge Nodes (AND-logic)**: A valid parameterization through $v$ uses all incoming edges simultaneously. The Cartesian product ensures we generate exactly one combination from each required input. By IH, each input's subtrees are correct, so their products are correct.

**Termination**: The graph is a DAG, so no cycles can exist and termination is guaranteed.

Therefore, because the starting state is valid, every step is guaranteed to be valid, and the algorithm is guaranteed to terminate, the algorithm is correct. 

## Complexity Analysis

### Time Complexity

Without memoization, the algorithm would explore an exponential number of paths. Each parameter node with $k$ incoming edges would recursively explore all paths through each predecessor, leading to $O(b^d)$ complexity where $b$ is the branching factor and $d$ is the graph depth.

The memoization optimization ensures each node is processed exactly once. However, the algorithm is output-sensitive due to the Cartesian product at merge nodes. If a merge node has $n$ predecessors, each with $p$ valid path trees, the merge generates $p^n$ combinations. In the worst case, let $P_{max}$ be the maximum number of path trees stored at any node. The time complexity is $O(|V| \times P_{max})$, where $P_{max}$ can grow exponentially with graph depth due to cascading Cartesian products at merge nodes.

### Space Complexity

Space complexity is dominated by the memoization table, which stores all path trees for each node: $O(|V| \times P_{max} \times L)$ where $L$ is the maximum path length. This space-for-time tradeoff is essential—without caching, the algorithm would recompute shared subproblems exponentially many times.

### Practical Performance

In practice, for our snow mechanics graph with 11 nodes and 23 edges, the algorithm executes in under 10ms and the memoization table remains small (under 50 total path trees across all nodes). The output-sensitive nature means performance scales with the complexity of the actual solution space rather than theoretical worst-case bounds.

## Implementation Details

The algorithm is implemented in Python within the SnowPyt-MechParams repository, which contains both the graph traversal algorithm and the actual calculation methods for mechanical parameters.

### Data Structures

The implementation uses four primary data structures defined in `data_structures.py`:

1. **Node**: Represents vertices in the graph with attributes `type` (either "parameter" or "merge"), `parameter` (the node identifier), and adjacency lists `incoming_edges` and `outgoing_edges`. Nodes are made hashable to enable efficient memoization using Python dictionaries.

2. **Edge**: Represents directed connections between nodes. Each edge stores references to its `start` and `end` nodes, plus an optional `method_name` attribute. When an edge is instantiated, it automatically updates the adjacency lists of both connected nodes through the `__post_init__` method.

3. **PathTree**: An internal recursive structure used during the backtracking phase. Each PathTree contains a `node_name`, a list of `branches` (each being a tuple of a child PathTree and edge label), and a boolean `is_merge` flag to distinguish merge nodes from parameter nodes.

4. **Parameterization**: The final output structure that represents a human-readable parameterization. It contains a list of `branches` (linear paths from snow_pit to various nodes) and `merge_points` (tuples indicating which branches merge at which nodes and how they continue).

### Graph Construction

The file `definitions.py` constructs the complete parameter dependency graph using a `GraphBuilder` helper class. This builder provides a fluent API for creating nodes and edges. For example:

```python
snow_pit = build_graph.param("snow_pit")
measured_density = build_graph.param("measured_density")
density = build_graph.param("density")
build_graph.flow(snow_pit, measured_density)
build_graph.flow(measured_density, density)
```

The graph includes 4 measured parameters (density, hand hardness, grain form, grain size), 4 calculated parameters (density, elastic modulus, Poisson's ratio, shear modulus), and 3 merge nodes representing different input combinations. In total, 11 nodes and 23 edges define the current parameter space.

### Algorithm Implementation

The core algorithm in `parameterization_algorithm.py` implements the recursive backtracking with memoization as described. One implementation challenge was converting the internal PathTree representation into the branch-and-merge format for output. The `_tree_to_parameterization` function performs a depth-first traversal of each PathTree, identifying merge points and splitting the tree into separate branches that terminate at those merges. This conversion ensures that users can clearly see which measurements are required and how they combine.

### Calculation Methods

The actual parameterization methods are implemented in separate modules (`density.py`, `elastic_modulus.py`, `poissons_ratio.py`, `shear_modulus.py`). Each module contains multiple functions corresponding to different published methods. For instance, `density.py` includes implementations of the Geldsetzer method, and two Kim & Jamieson methods (Table 2 and Table 5). These implementations use the `uncertainties` package to propagate measurement uncertainty through calculations, which will be valuable for future work comparing parameterization quality.

## Results and Application

We applied the algorithm to the parameter dependency graph defined in `definitions.py`, querying for parameterizations of density, elastic modulus, Poisson's ratio, and shear modulus. The algorithm successfully identified all valid calculation pathways, demonstrating both correctness and the multiplicative complexity inherent in dependent parameter calculations.

### Overall Results

The algorithm found:
- **Density**: 4 parameterizations
- **Elastic Modulus**: 16 parameterizations
- **Poisson's Ratio**: 5 parameterizations
- **Shear Modulus**: 4 parameterizations

The expansion from 4 density parameterizations to 16 elastic modulus parameterizations illustrates the Cartesian product effect at work. Since elastic modulus methods require density as input, each of the 4 ways to calculate density combines with each of the 4 elastic modulus calculation methods (Bergfeld et al., 2021; Köchle & Schneebeli, 2014; Wautier et al., 2015; Schottner et al., 2023), yielding 4 × 4 = 16 total parameterizations. This multiplicative growth demonstrates why manual enumeration of calculation pathways becomes intractable for complex parameter networks.

### Detailed Results: Density Parameterizations

For the density parameter, the algorithm identified **4 distinct parameterizations**:

**Parameterization 1 - Direct Measurement**: The simplest path uses directly measured density values when available in the snow pit data:
```
branch 1: snow_pit -- data_flow --> measured_density -- data_flow --> density
```
This single-branch parameterization requires only that density was measured in the field.

**Parameterization 2 - Geldsetzer Method**: This parameterization calculates density from hand hardness and grain form observations (Geldsetzer & Jamieson, 2001):
```
branch 1: snow_pit -- data_flow --> measured_hand_hardness -- data_flow --> merge_hand_hardness_grain_form
branch 2: snow_pit -- data_flow --> measured_grain_form -- data_flow --> merge_hand_hardness_grain_form
merge branch 1, branch 2: merge_hand_hardness_grain_form -- geldsetzer --> density
```
The two branches demonstrate the AND-logic of merge nodes: both inputs are required simultaneously. The merge node `merge_hand_hardness_grain_form` aggregates these inputs before the Geldsetzer method is applied.

**Parameterization 3 - Kim & Jamieson Table 2**: This uses the same inputs as Geldsetzer but applies a different calculation method (Kim & Jamieson, 2010):
```
branch 1: snow_pit -- data_flow --> measured_hand_hardness -- data_flow --> merge_hand_hardness_grain_form
branch 2: snow_pit -- data_flow --> measured_grain_form -- data_flow --> merge_hand_hardness_grain_form
merge branch 1, branch 2: merge_hand_hardness_grain_form -- kim_jamieson_table2 --> density
```
This parameterization demonstrates the OR-logic of parameter nodes: the same merge node feeds into multiple alternative calculation methods. From the algorithm's perspective, both the Geldsetzer and Kim & Jamieson Table 2 methods are valid independent paths to density.

**Parameterization 4 - Kim & Jamieson Table 5**: This method requires three inputs, creating a more complex merge structure (Kim & Jamieson, 2010):
```
branch 1: snow_pit -- data_flow --> measured_hand_hardness -- data_flow --> merge_hand_hardness_grain_form_grain_size
branch 2: snow_pit -- data_flow --> measured_grain_form -- data_flow --> merge_hand_hardness_grain_form_grain_size
branch 3: snow_pit -- data_flow --> measured_grain_size -- data_flow --> merge_hand_hardness_grain_form_grain_size
merge branch 1, branch 2, branch 3: merge_hand_hardness_grain_form_grain_size -- kim_jamieson_table5 --> density
```
This parameterization uses a different merge node (`merge_hand_hardness_grain_form_grain_size`) than Parameterizations 2 and 3, because the input combination is different. The algorithm correctly identifies that all three branches must be present for this parameterization to be valid.

### Verification

The results were manually verified against the graph structure. The memoization table was examined during execution, confirming that each node was processed exactly once despite being referenced multiple times. For example, when querying elastic modulus, the algorithm cached the 4 density parameterizations and reused them for each of the 4 elastic modulus methods, avoiding redundant computation.

## Future Work
Given the output of the algorithm, I can now programmatically implement each parameterization returned by the algorithm to apply the methods defined in SnowPyt MechParams to the SnowPilot dataset, where the output of some methods will serve as the inputs to future methods.

The current state of the SnowPyt-MechParams repository only contains implementations for layer specific parameters, but once the implementations and algorithm are extended to pit parameters and stability criterion, the results can also be compared to stability test results. Comparing the calculated stability criterion to stability test results, and snow pit observations from known avalanche sites, will allow us to evaluate the stability criterion.

Many of the methods implemented have associated limitations or uncertainty. For example, the Bergfeld parameterization (Bergfeld et al., 2021) can only be applied to grain types of: Precipitation Particles, Rounded Grains and Decomposing and Fragmented Particles. If this method is applied, all slab layers with other grain forms are eliminated from the subsequent analysis. Wherever possible, we have included the uncertainty of a method as reported by the authors. The SnowPyt-MechParams repository uses the python uncertainties package to calculate the error propagation as methods are implemented.

In the future, we may also seek to apply "edge weights" to methods to enable the algorithm to find an optimal path tree. These edge weights could represent the loss or uncertainty induced by applying the method represented by the edge.

## Conclusion

This project successfully applied advanced graph traversal and dynamic programming techniques to a domain-specific problem in snow physics. By modeling the calculation network as a DAG with distinct logical node types, we were able to automate the discovery of calculation pathways. The use of Dynamic Programming was critical—it transformed an intractable recursive explosion into a manageable, structured search. This algorithm allows researchers to find every possible way a physical parameter can be derived from their specific dataset, providing transparency and robustness to scientific modeling. Future work could involve weighting the edges based on uncertainty or error propagation, allowing the algorithm to not only find all paths but to rank them by minimizing cumulative error.

## References

Bergfeld, B., van Herwijnen, A., Bobillier, G., Dual, J., Gaume, J., & Schweizer, J. (2021). Measuring slope-scale mechanical properties of snow using the propagation saw test. *The Cryosphere*, 15(7), 3539-3555.

Chabot, D., Kahrl, A., & Earl, T. (2016). SnowPilot: An open-source web application for managing and sharing avalanche observations. *International Snow Science Workshop Proceedings*, Breckenridge, CO.

Geldsetzer, T., & Jamieson, J. B. (2001). Estimating dry snow density from grain form and hand hardness. *Proceedings of the International Snow Science Workshop*, Big Sky, MT, 121-127.

Kim, J., & Jamieson, J. B. (2010). Preliminary results from a field study on wet snow avalanche forecasting. *Proceedings of the International Snow Science Workshop*, Squaw Valley, CA, 475-479.

Köchle, B., & Schneebeli, M. (2014). Three-dimensional microstructure and numerical calculation of elastic properties of alpine snow with a focus on weak layers. *Journal of Glaciology*, 60(222), 705-713.

Schottner, K., Esser, B., & Schneebeli, M. (2023). Mechanical properties of seasonal snow from microstructure. *The Cryosphere*, 17(7), 3075-3088.

Srivastava, P. K., Mahajan, P., Satyawali, P. K., & Kumar, V. (2016). Observation of temperature gradient metamorphism in snow by X-ray computed microtomography: measurement of microstructure parameters and simulation of linear elastic properties. *Annals of Glaciology*, 57(71), 43-52.

Wautier, A., Geindreau, C., & Flin, F. (2015). Linking snow microstructure to its macroscopic elastic stiffness. *Journal of Glaciology*, 61(228), 789-804.
