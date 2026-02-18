# Parameterization Algorithm

This directory contains an algorithm for finding all possible parameterizations for calculating snow mechanical parameters from snow pit measurements.

## Overview

The algorithm uses **recursion with dynamic programming (memoization)** to traverse a directed graph representing parameter dependencies and calculation methods. It finds all possible paths from a target parameter back to the root `snow_pit` node.

## Key Concepts

### Graph Structure

- **Parameter nodes**: Represent measured or calculated parameters (e.g., `density`, `elastic_modulus`)
- **Merge nodes**: Combine multiple parameters that serve as inputs to a method
- **Edges**: Represent either:
  - **Method edges**: Transformations/calculations with a method name (e.g., `geldsetzer`, `bergfeld`)
  - **Data flow edges**: Simple data flow connections (displayed as `data_flow`)

### Algorithm Logic

The algorithm traverses **backwards** from the target parameter to the `snow_pit` node:

1. **Parameter nodes** (OR logic): Try each incoming edge independently. Each edge represents a different way to calculate the parameter.

2. **Merge nodes** (AND logic): All incoming edges must be included. All inputs are required for the merge.

3. **Memoization**: Results for each node are cached to avoid redundant computation.

4. **Deduplication**: After all structural traversals are generated, any two traversals that produce the same `(parameter → method)` mapping are considered identical. Only the first occurrence of each unique fingerprint is returned.

   This matters when a parameter node is reachable via more than one branch of a merge node. For example, `density` is used by both `elastic_modulus` and `srivastava` (Poisson's ratio). The Cartesian-product merge logic internally generates all cross-combinations of density sub-paths, but since only one density method can be in use at a time, all but one combination per unique density choice are duplicates. Deduplication removes them before the caller sees the result.

## Files

- `data_structures.py`: Defines `Node`, `Edge`, `Graph`, and `GraphBuilder` classes
- `definitions.py`: Creates the graph of all available methods and parameters
- `parameterization_algorithm.py`: Implements the `find_parameterizations()` function

## Usage

```python
from algorithm import find_parameterizations, graph, density

# Find all parameterizations for a target parameter
parameterizations = find_parameterizations(graph, density)

# Print results
for i, param in enumerate(parameterizations, 1):
    print(f"Parameterization {i}:")
    print(param)
    print()
```

## Output Format

Each parameterization shows:

- **Branches**: Individual paths from `snow_pit` to various nodes
- **Merge points**: Where multiple branches combine

Example output:
```
Parameterization 2:
branch 1: snow_pit -> data_flow -> measured_hand_hardness -> data_flow -> merge_hand_hardness_grain_form -> geldsetzer -> density
branch 2: snow_pit -> data_flow -> measured_grain_form -> data_flow -> merge_hand_hardness_grain_form -> geldsetzer -> density
merge branch 1, branch 2: merge_hand_hardness_grain_form
```

This shows that to calculate `density` using the `geldsetzer` method:
1. Branch 1 gets `measured_hand_hardness` from `snow_pit`
2. Branch 2 gets `measured_grain_form` from `snow_pit`
3. These merge at `merge_hand_hardness_grain_form`
4. The `geldsetzer` method uses the merged inputs to calculate `density`

## Algorithm Complexity

- **Time complexity**: O(n × m) where n is the number of nodes and m is the average number of incoming edges per node
- **Space complexity**: O(n × p) where p is the number of parameterizations per node (due to memoization)

The dynamic programming approach ensures each node is processed only once, with results cached for reuse.

