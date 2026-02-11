# Implementation Plan: Graph Integration and D11 Analysis (REVISED)

**Project:** SnowPyt-MechParams
**Date:** February 9, 2026
**Author:** Implementation Plan for Option 3 Architecture
**Status:** REVISED based on user feedback

---

## Revision History

**Revision 1 (Feb 9, 2026):**
- Corrected Phase 1 graph structure based on user feedback
- Added layer property nodes (layer_location, layer_thickness)
- Corrected merge node structure to match diagram
- Clarified that layer properties are already available on Layer objects
- Updated algorithm considerations for layer-then-slab execution order

---

## Executive Summary

This plan describes the implementation to:
1. Move the parameterization algorithm from `/algorithm` to production code structure
2. Extend the parameter graph to include slab-level parameters (A11, B11, D11, A55)
3. Enhance execution engine with dynamic programming for efficient computation
4. Create comprehensive D11 analysis notebook comparing values across all calculation pathways for ECTP slabs

**Architecture Choice:** Option 3 - Top-level graph module + algorithm utility

**Key Insight:** Slab parameter calculations (A11, B11, D11, A55) require ALL layers to have necessary properties computed first. The execution must complete all layer-level calculations before proceeding to slab-level calculations.

---

## Table of Contents

1. [Phase 1: Extend Graph to Include Slab Parameters](#phase-1-extend-graph-to-include-slab-parameters)
2. [Phase 2: Create Production Module Structure](#phase-2-create-production-module-structure)
3. [Phase 3: Enhance Execution Engine with Dynamic Programming](#phase-3-enhance-execution-engine-with-dynamic-programming)
4. [Phase 4: Update Existing Code](#phase-4-update-existing-code)
5. [Phase 5: Testing](#phase-5-testing)
6. [Phase 6: Create D11 Comparison Notebook](#phase-6-create-d11-comparison-notebook)
7. [Phase 7: Documentation and Cleanup](#phase-7-documentation-and-cleanup)
8. [Implementation Checklist](#implementation-checklist)

---

## Phase 1: Extend Graph to Include Slab Parameters

### 1.1 Add Slab Parameter Nodes to Graph Definition

**Objective:** Extend the graph to represent slab-level calculations based on the provided diagram and existing slab_parameters implementations.

#### New Parameter Nodes

**Slab Parameters:**
- `A11` - Extensional stiffness (N/mm)
- `B11` - Extensional-bending coupling stiffness (N)
- `D11` - Bending stiffness (N·mm)
- `A55` - Shear stiffness with correction factor κ (N/mm)

**Layer Property Nodes:**
- `layer_location` - Depth from top surface (zi, from `depth_top`)
- `layer_thickness` - Layer thickness (hi, from `thickness`)

**Important:** `layer_location` and `layer_thickness` are **already available** as properties on Layer objects (`layer.depth_top` and `layer.thickness`). These nodes represent them in the graph to show the dependency structure, but no calculation is needed - they are direct data flow from measured values.

#### New Merge Nodes

Based on user feedback and the diagram:

**1. `zi` - Merge layer location and layer thickness**
- **Inputs**:
  - `layer_location` (depth_top)
  - `layer_thickness` (thickness)
- **Purpose**: Combines spatial information about layer position
- **Used by**: `merge_zi_E_nu` (for D11 calculation which needs layer positions)

**2. `merge_E_nu` - Merge elastic modulus and Poisson's ratio for all layers**
- **Inputs**:
  - `elastic_modulus` (from all layers)
  - `poissons_ratio` (from all layers)
- **Purpose**: Collects E and ν from all layers (required together for plane-strain modulus)
- **Used by**: `merge_zi_E_nu`, `merge_hi_E_nu`

**3. `merge_zi_E_nu` - Merge spatial info with E and ν**
- **Inputs**:
  - `zi` (layer position information)
  - `merge_E_nu` (E and ν from all layers)
- **Purpose**: Combines layer positions with mechanical properties for bending calculations
- **Used by**: `D11` (via `weissgraeber_rosendahl`)
- **Note**: D11 needs to know where layers are located (zi) because bending stiffness depends on distance from neutral axis (z² weighting)

**4. `merge_hi_G` - Merge layer thickness with shear modulus**
- **Inputs**:
  - `layer_thickness` (hi)
  - `shear_modulus` (G from all layers)
- **Purpose**: Combines layer thicknesses with shear properties
- **Used by**: `A55` (via `weissgraeber_rosendahl`)
- **Note**: A55 = Σ G_i * h_i (sum of shear modulus × thickness for each layer)

**5. `merge_hi_E_nu` - Merge layer thickness with E and ν**
- **Inputs**:
  - `layer_thickness` (hi)
  - `merge_E_nu` (E and ν from all layers)
- **Purpose**: Combines layer thicknesses with elastic properties
- **Used by**: `A11` (via `weissgraeber_rosendahl`)
- **Note**: A11 involves integrating plane-strain modulus over thickness

#### Graph Structure Extensions

```python
# ============================================================================
# NEW NODES for slab parameters
# ============================================================================

# Layer property nodes (data flow from measured values)
layer_location = build_graph.param("layer_location")  # zi (depth_top)
layer_thickness = build_graph.param("layer_thickness")  # hi (thickness)

# Slab parameter nodes (calculated)
A11 = build_graph.param("A11")  # Extensional stiffness
B11 = build_graph.param("B11")  # Bending-extension coupling
D11 = build_graph.param("D11")  # Bending stiffness
A55 = build_graph.param("A55")  # Shear stiffness

# ============================================================================
# NEW MERGE NODES for combining layer properties
# ============================================================================

# Merge 1: Combine layer location and thickness (spatial info)
zi = build_graph.merge("zi")

# Merge 2: Combine E and nu from all layers
merge_E_nu = build_graph.merge("merge_E_nu")

# Merge 3: Combine spatial info with E and nu (for D11)
merge_zi_E_nu = build_graph.merge("merge_zi_E_nu")

# Merge 4: Combine thickness with shear modulus (for A55)
merge_hi_G = build_graph.merge("merge_hi_G")

# Merge 5: Combine thickness with E and nu (for A11)
merge_hi_E_nu = build_graph.merge("merge_hi_E_nu")

# ============================================================================
# DATA FLOW: Snow pit -> layer properties
# ============================================================================

# Layer properties are direct measurements (data flow from snow_pit)
build_graph.flow(snow_pit, layer_location)
build_graph.flow(snow_pit, layer_thickness)

# ============================================================================
# MERGE 1: zi (spatial information)
# ============================================================================

build_graph.flow(layer_location, zi)
build_graph.flow(layer_thickness, zi)

# ============================================================================
# MERGE 2: merge_E_nu (elastic properties from all layers)
# ============================================================================

build_graph.flow(elastic_modulus, merge_E_nu)
build_graph.flow(poissons_ratio, merge_E_nu)

# ============================================================================
# MERGE 3: merge_zi_E_nu (spatial + elastic properties for D11)
# ============================================================================

build_graph.flow(zi, merge_zi_E_nu)
build_graph.flow(merge_E_nu, merge_zi_E_nu)

# ============================================================================
# MERGE 4: merge_hi_G (thickness + shear for A55)
# ============================================================================

build_graph.flow(layer_thickness, merge_hi_G)
build_graph.flow(shear_modulus, merge_hi_G)

# ============================================================================
# MERGE 5: merge_hi_E_nu (thickness + elastic properties for A11)
# ============================================================================

build_graph.flow(layer_thickness, merge_hi_E_nu)
build_graph.flow(merge_E_nu, merge_hi_E_nu)

# ============================================================================
# SLAB PARAMETER CALCULATIONS
# ============================================================================

# D11: Requires spatial position + E + nu for all layers
build_graph.method_edge(merge_zi_E_nu, D11, "weissgraeber_rosendahl")

# A55: Requires thickness + G for all layers
build_graph.method_edge(merge_hi_G, A55, "weissgraeber_rosendahl")

# A11: Requires thickness + E + nu for all layers
build_graph.method_edge(merge_hi_E_nu, A11, "weissgraeber_rosendahl")

# B11: Similar to A11 (uses same merge, different calculation)
build_graph.method_edge(merge_hi_E_nu, B11, "weissgraeber_rosendahl")
```

#### Key Insights

1. **Layer properties are already available**: `depth_top` and `thickness` exist on Layer objects. The nodes `layer_location` and `layer_thickness` represent them in the graph structure but require no calculation - they are direct data flow.

2. **Slab calculations require all layers**: Unlike layer-level parameters where each layer is computed independently, slab parameters (A11, B11, D11, A55) require **all layers** to have their properties computed first.

3. **Spatial information matters for D11**: The `zi` merge captures layer position information because bending stiffness depends on distance from the neutral axis (z² weighting in the integral).

4. **Merge nodes enable different combinations**:
   - `merge_E_nu`: Used by both D11 and A11/B11
   - `zi`: Only needed for D11 (spatial weighting)
   - `merge_hi_G`: Only needed for A55 (shear)

5. **Execution order**: Layer-level calculations must complete **before** slab-level calculations begin. The algorithm/executor must respect this dependency.

### 1.2 Update Data Structures

**Note:** The Slab class **already has** fields for A11, B11, D11, A55 (lines 729-758 in data_structures.py). No changes needed:

```python
@dataclass
class Slab:
    # ... existing fields ...

    # Calculated Parameters - From Method Implementations
    A11: Optional[UncertainValue] = None  # N/mm - Extensional stiffness
    A55: Optional[UncertainValue] = None  # N/mm - Shear stiffness (with shear correction factor κ)
    B11: Optional[UncertainValue] = None  # N - Bending-extension coupling stiffness
    D11: Optional[UncertainValue] = None  # N·mm - Bending stiffness
```

**Design Decision:** Slab parameters are stored directly on Slab objects, consistent with how layer parameters are stored on Layer objects. This is already implemented - no changes needed.

### 1.3 Algorithm Considerations for Layer-then-Slab Execution

**Challenge:** The current algorithm (`find_parameterizations`) works backwards from a target parameter to the root. For slab parameters, this means:

1. Algorithm finds paths from D11 → merge_zi_E_nu → merge_E_nu → elastic_modulus + poissons_ratio
2. This correctly identifies that E and ν must be calculated on all layers
3. **However**, the executor must ensure all layers complete E/ν calculations before attempting D11

**Current Executor Behavior:**
- Processes layers sequentially (layer 0, then layer 1, etc.)
- Computes layer-level parameters on each layer
- Then computes slab parameters

**This is correct!** The current execution order already handles this properly:
```python
# From PathwayExecutor.execute_parameterization (lines 89-108)
for layer_idx, layer in enumerate(working_slab.layers):
    layer_result = self._execute_layer_pathway(...)
    layer_results.append(layer_result)
    working_slab.layers[layer_idx] = layer_result.layer

# Execute slab-level calculations AFTER all layers done
if include_plate_theory:
    slab_result = self._execute_slab_calculations(working_slab, layer_results)
```

**No algorithm changes needed** - the executor already processes all layers before slab calculations.

**What we need to update:**
- `_execute_slab_calculations` to handle the new graph structure
- Dispatcher to recognize when a parameter is slab-level vs layer-level
- Proper handling of "all layers must have property X" checks

---

## Phase 2: Create Production Module Structure

### 2.1 Create `src/snowpyt_mechparams/graph/` Module

**Directory structure:**
```
src/snowpyt_mechparams/graph/
├── __init__.py
├── structures.py      # Graph, Node, Edge, GraphBuilder classes
├── definitions.py     # Parameter graph definition with slab params
└── README.md         # Documentation
```

#### 2.1.1 Create `graph/structures.py`

**Source:** Copy from `algorithm/data_structures.py`

**Changes:**
- Add comprehensive module docstring with usage examples
- Add type hints to all methods
- Improve docstrings to be user-facing (not class-project specific)
- Ensure `NodeType` enum exists (if not present, add it):
  ```python
  from enum import Enum

  class NodeType(Enum):
      PARAMETER = "parameter"
      MERGE = "merge"
  ```

#### 2.1.2 Create `graph/definitions.py`

**Source:** Copy from `algorithm/definitions.py` and extend with Phase 1.1 additions

**Changes:**
1. Add layer property nodes (layer_location, layer_thickness)
2. Add slab parameter nodes (A11, B11, D11, A55)
3. Add merge nodes (zi, merge_E_nu, merge_zi_E_nu, merge_hi_G, merge_hi_E_nu)
4. Add comprehensive documentation at top of file
5. Export all nodes

**Module docstring template:**

```python
"""
Parameter graph definition for SnowPyt-MechParams.

This module defines the complete parameter dependency graph, including:
- Layer-level parameters (density, elastic modulus, Poisson's ratio, shear modulus)
- Slab-level parameters (A11, B11, D11, A55 plate theory stiffnesses)

Graph Structure:
---------------

Layer-Level:
snow_pit → measured_* → density → elastic_modulus
                                → poissons_ratio
                                → shear_modulus

snow_pit → layer_location (depth_top)
         → layer_thickness (thickness)

Slab-Level:
layer_location + layer_thickness → zi
elastic_modulus + poissons_ratio → merge_E_nu

zi + merge_E_nu → merge_zi_E_nu → D11
layer_thickness + shear_modulus → merge_hi_G → A55
layer_thickness + merge_E_nu → merge_hi_E_nu → A11, B11

Methods Available:
-----------------

[Full documentation of all methods with citations]

Slab Parameters (Plate Theory):
- weissgraeber_rosendahl: Classical laminate theory [Weißgraeber & Rosendahl 2023]
  * A11: Extensional stiffness = Σ (E_i/(1-ν_i²)) * h_i
  * B11: Bending-extension coupling = Σ (E_i/(1-ν_i²)) * h_i * z_i
  * D11: Bending stiffness = Σ (E_i/(1-ν_i²)) * (z_{i+1}³ - z_i³) / 3
  * A55: Shear stiffness = κ * Σ G_i * h_i  (κ = 5/6)

Adding New Methods:
------------------
[Instructions for extending the graph]

References:
----------
Weißgraeber, P., & Rosendahl, P. L. (2023). A closed-form model for
layered snow slabs. The Cryosphere, 17(4), 1475-1496.
https://doi.org/10.5194/tc-17-1475-2023

See also:
--------
- /algorithm/README.md: Algorithm explanation
- /algorithm/algorithm_flowchart.md: Visual flowchart
"""
```

**Export all nodes:**
```python
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
    'layer_location',
    'layer_thickness',
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
]
```

#### 2.1.3 Create `graph/__init__.py`

```python
"""
Parameter graph module for SnowPyt-MechParams.

This module defines the directed graph of all available calculation methods
for snow mechanical parameters at both layer and slab levels.

The graph represents:
- **Parameter nodes**: Measured or calculated parameters
- **Merge nodes**: Combinations of inputs required for methods
- **Edges**: Calculation methods or data flow connections

The graph is used by the execution engine to find all possible calculation
pathways from measured inputs to target parameters.

Quick Start
-----------
>>> from snowpyt_mechparams.graph import graph
>>> from snowpyt_mechparams.algorithm import find_parameterizations
>>>
>>> # Find all ways to calculate D11
>>> D11_node = graph.get_node("D11")
>>> pathways = find_parameterizations(graph, D11_node)
>>> print(f"Found {len(pathways)} pathways to calculate D11")

Key Concepts
------------
**Layer Properties**: depth_top and thickness are already available on Layer objects.
The nodes layer_location and layer_thickness represent them in the graph but
require no calculation - they are direct data flow from measurements.

**Slab Parameters**: A11, B11, D11, A55 require ALL layers to have necessary
properties computed. The execution engine handles this by completing all
layer-level calculations before attempting slab-level calculations.

**Merge Nodes**: Special nodes that combine multiple inputs:
- zi: Combines layer position and thickness (for spatial weighting)
- merge_E_nu: Combines E and ν from all layers (for plane-strain modulus)
- merge_zi_E_nu: Combines spatial info with E/ν (for D11 bending calculation)
- merge_hi_G: Combines thickness with shear modulus (for A55)
- merge_hi_E_nu: Combines thickness with E/ν (for A11, B11)

See Also
--------
- graph.definitions : The complete graph definition
- graph.structures : Graph data structures (Node, Edge, Graph)
- algorithm : Functions to find calculation pathways
"""

from snowpyt_mechparams.graph.structures import (
    Node,
    Edge,
    Graph,
    GraphBuilder,
)

from snowpyt_mechparams.graph.definitions import (
    graph,
    # Root
    snow_pit,
    # Measured parameters
    measured_density,
    measured_hand_hardness,
    measured_grain_form,
    measured_grain_size,
    # Layer properties (measured)
    layer_location,
    layer_thickness,
    # Layer parameters (calculated)
    density,
    elastic_modulus,
    poissons_ratio,
    shear_modulus,
    # Slab parameters (calculated)
    A11,
    B11,
    D11,
    A55,
)

__all__ = [
    # Classes
    "Node",
    "Edge",
    "Graph",
    "GraphBuilder",
    # Graph instance
    "graph",
    # Root
    "snow_pit",
    # Measured parameters
    "measured_density",
    "measured_hand_hardness",
    "measured_grain_form",
    "measured_grain_size",
    # Layer properties (measured)
    "layer_location",
    "layer_thickness",
    # Layer parameters (calculated)
    "density",
    "elastic_modulus",
    "poissons_ratio",
    "shear_modulus",
    # Slab parameters (calculated)
    "A11",
    "B11",
    "D11",
    "A55",
]
```

#### 2.1.4 Create `graph/README.md`

Content:
- Overview of the graph structure
- Explanation of node types (parameter vs merge)
- Explanation of layer properties vs calculated parameters
- Explanation of slab parameter dependencies
- How to explore the graph programmatically
- How to add new methods
- Link to algorithm documentation

### 2.2 Create `src/snowpyt_mechparams/algorithm.py`

**Source:** Copy from `algorithm/parameterization_algorithm.py`

**Changes:**

1. **Update imports:**
   ```python
   from typing import List, Dict, Optional
   from dataclasses import dataclass
   from snowpyt_mechparams.graph.structures import Node, Graph
   ```

2. **Add comprehensive module docstring** (similar to previous plan version)

3. **No functional changes to algorithm logic** - it already handles the graph structure correctly

---

## Phase 3: Enhance Execution Engine with Dynamic Programming

### 3.1 Objectives

1. **Avoid redundant calculations**: When multiple pathways share common subpaths, compute each parameter once
2. **Track calculation provenance**: Record which method was used for each parameter
3. **Support slab-level parameters**: Handle calculations that require all layers to have properties
4. **Handle layer properties**: Recognize layer_location and layer_thickness as direct data flow (no calculation)

### 3.2 Current State Analysis

**Existing cache in `executor.py`:**
```python
self._cache: Dict[Tuple[int, str, str], UncertainValue] = {}
# Key: (layer_index, parameter, method)
# Value: Calculated parameter value
```

**Current behavior:** Cache is cleared for each pathway execution (`self._cache.clear()` in line 77)

**Limitation:** No dynamic programming across pathways for the same slab

### 3.3 Enhanced Caching Strategy

**New approach:**
1. **Persistent cache across pathways** for the same slab
2. **Three-level caching**:
   - Layer-level: `(layer_index, parameter, method) -> value`
   - Slab-level: `(parameter, method) -> value`
   - Provenance: `(layer_index, parameter) -> method_name`

**Implementation:**

```python
class PathwayExecutor:
    """
    Executes parameterization pathways on Layer/Slab objects.

    Implements dynamic programming by caching computed values across
    pathway executions for the same slab.
    """

    def __init__(self, dispatcher: Optional[MethodDispatcher] = None):
        self.dispatcher = dispatcher or MethodDispatcher()

        # Layer-level cache: (layer_index, parameter, method) -> value
        self._layer_cache: Dict[Tuple[int, str, str], UncertainValue] = {}

        # Slab-level cache: (parameter, method) -> value
        self._slab_cache: Dict[Tuple[str, str], UncertainValue] = {}

        # Provenance tracking: (layer_index, parameter) -> method_name
        self._layer_provenance: Dict[Tuple[int, str], str] = {}

        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0

    def clear_cache(self):
        """Clear all caches (call between different slabs)."""
        self._layer_cache.clear()
        self._slab_cache.clear()
        self._layer_provenance.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache performance statistics."""
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': self._cache_hits / (self._cache_hits + self._cache_misses)
                        if (self._cache_hits + self._cache_misses) > 0 else 0.0
        }

    def _get_or_compute_layer_param(
        self,
        layer: Layer,
        layer_index: int,
        parameter: str,
        method: str,
        **kwargs
    ) -> Tuple[Optional[UncertainValue], bool]:
        """
        Get parameter from cache or compute it.

        Returns
        -------
        Tuple[Optional[UncertainValue], bool]
            (value, was_cached)
        """
        # Special handling for layer properties (direct data flow)
        if parameter == "layer_location":
            # Direct from layer.depth_top
            return layer.depth_top, False
        elif parameter == "layer_thickness":
            # Direct from layer.thickness
            return layer.thickness, False

        cache_key = (layer_index, parameter, method)

        # Check cache first
        if cache_key in self._layer_cache:
            self._cache_hits += 1
            return self._layer_cache[cache_key], True

        # Compute and store
        self._cache_misses += 1
        value = self.dispatcher.execute_method(
            parameter=parameter,
            method=method,
            level=ParameterLevel.LAYER,
            layer=layer,
            **kwargs
        )

        if value is not None:
            self._layer_cache[cache_key] = value
            self._layer_provenance[(layer_index, parameter)] = method

        return value, False

    def execute_parameterization(
        self,
        parameterization: Parameterization,
        slab: Slab,
        target_parameter: str,
        include_plate_theory: bool = True
    ) -> PathwayResult:
        """
        Execute a single parameterization pathway on a slab.

        NOTE: Cache is NOT cleared, allowing dynamic programming across
        pathway executions for the same slab. Call clear_cache() when
        switching to a new slab.
        """
        # DO NOT clear cache - enables dynamic programming
        # self._cache.clear()  # REMOVED

        # ... rest of implementation uses _get_or_compute_layer_param
```

### 3.4 Execution Engine Updates

**Update `ExecutionEngine.execute_all()` to manage cache lifecycle:**

```python
class ExecutionEngine:
    def execute_all(
        self,
        slab: Slab,
        target_parameter: str,
        include_plate_theory: bool = True
    ) -> ExecutionResults:
        """Execute all pathways for a slab with dynamic programming."""

        # Create executor with persistent cache for this slab
        executor = PathwayExecutor()

        # Find all parameterizations
        target_node = self.graph.get_node(target_parameter)
        parameterizations = find_parameterizations(self.graph, target_node)

        results = {}
        for param in parameterizations:
            # Cache persists across pathway executions
            result = executor.execute_parameterization(
                parameterization=param,
                slab=slab,  # Work on same slab
                target_parameter=target_parameter,
                include_plate_theory=include_plate_theory
            )
            results[result.pathway_description] = result

        # Get cache statistics
        cache_stats = executor.get_cache_stats()

        return ExecutionResults(
            target_parameter=target_parameter,
            results=results,
            cache_stats=cache_stats  # NEW: Track cache efficiency
        )
```

### 3.5 Slab Parameter Execution

**Update `_execute_slab_calculations` to handle new graph structure:**

```python
def _execute_slab_calculations(
    self,
    slab: Slab,
    layer_results: List[LayerResult]
) -> SlabResult:
    """
    Execute slab-level parameter calculations.

    Slab parameters require all layers to have certain properties.
    Checks prerequisites before attempting each calculation.
    """
    slab_result = SlabResult()

    # Check layer properties availability (these are always available if layer exists)
    all_layers_have_location = all(
        lr.layer.depth_top is not None
        for lr in layer_results
    )
    all_layers_have_thickness = all(
        lr.layer.thickness is not None
        for lr in layer_results
    )

    # Check if we can compute each slab parameter

    # A11, B11: Require E and ν on all layers, plus thickness
    can_compute_A11_B11 = (
        all_layers_have_thickness and
        all(lr.layer.elastic_modulus is not None for lr in layer_results) and
        all(lr.layer.poissons_ratio is not None for lr in layer_results)
    )

    # D11: Requires E, ν on all layers, plus location and thickness (for zi)
    can_compute_D11 = (
        all_layers_have_location and
        all_layers_have_thickness and
        all(lr.layer.elastic_modulus is not None for lr in layer_results) and
        all(lr.layer.poissons_ratio is not None for lr in layer_results)
    )

    # A55: Requires G on all layers, plus thickness
    can_compute_A55 = (
        all_layers_have_thickness and
        all(lr.layer.shear_modulus is not None for lr in layer_results)
    )

    # Compute A11 if possible
    if can_compute_A11_B11:
        A11_value = self._get_or_compute_slab_param(
            slab=slab,
            parameter="A11",
            method="weissgraeber_rosendahl"
        )
        slab_result.A11 = A11_value
        slab.A11 = A11_value

    # Compute B11 if possible
    if can_compute_A11_B11:
        B11_value = self._get_or_compute_slab_param(
            slab=slab,
            parameter="B11",
            method="weissgraeber_rosendahl"
        )
        slab_result.B11 = B11_value
        slab.B11 = B11_value

    # Compute D11 if possible
    if can_compute_D11:
        D11_value = self._get_or_compute_slab_param(
            slab=slab,
            parameter="D11",
            method="weissgraeber_rosendahl"
        )
        slab_result.D11 = D11_value
        slab.D11 = D11_value

    # Compute A55 if possible
    if can_compute_A55:
        A55_value = self._get_or_compute_slab_param(
            slab=slab,
            parameter="A55",
            method="weissgraeber_rosendahl"
        )
        slab_result.A55 = A55_value
        slab.A55 = A55_value

    return slab_result

def _get_or_compute_slab_param(
    self,
    slab: Slab,
    parameter: str,
    method: str
) -> Optional[UncertainValue]:
    """
    Get slab parameter from cache or compute it.

    Returns
    -------
    Optional[UncertainValue]
        Computed value or None if computation failed
    """
    cache_key = (parameter, method)

    # Check cache
    if cache_key in self._slab_cache:
        self._cache_hits += 1
        return self._slab_cache[cache_key]

    # Compute
    self._cache_misses += 1
    value = self.dispatcher.execute_method(
        parameter=parameter,
        method=method,
        level=ParameterLevel.SLAB,
        slab=slab
    )

    if value is not None:
        self._slab_cache[cache_key] = value

    return value
```

### 3.6 Dispatcher Updates

**Update `MethodDispatcher` to handle slab-level parameters:**

```python
class ParameterLevel(Enum):
    """Level at which parameter is calculated."""
    LAYER = "layer"
    SLAB = "slab"

class MethodDispatcher:
    """
    Dispatches method calls to appropriate implementation functions.

    Handles both layer-level and slab-level parameter calculations.
    """

    def execute_method(
        self,
        parameter: str,
        method: str,
        level: ParameterLevel,
        layer: Optional[Layer] = None,
        slab: Optional[Slab] = None,
        **kwargs
    ) -> Optional[UncertainValue]:
        """
        Execute a calculation method.

        Parameters
        ----------
        parameter : str
            Parameter to calculate (e.g., "density", "D11")
        method : str
            Method name (e.g., "geldsetzer", "weissgraeber_rosendahl")
        level : ParameterLevel
            Whether this is a layer or slab parameter
        layer : Optional[Layer]
            Layer object (required for layer-level)
        slab : Optional[Slab]
            Slab object (required for slab-level)

        Returns
        -------
        Optional[UncertainValue]
            Calculated value or None if calculation failed
        """
        try:
            if level == ParameterLevel.LAYER:
                return self._execute_layer_method(parameter, method, layer, **kwargs)
            elif level == ParameterLevel.SLAB:
                return self._execute_slab_method(parameter, method, slab, **kwargs)
        except Exception as e:
            # Log but don't crash - return None for failed calculations
            return None

    def _execute_slab_method(
        self,
        parameter: str,
        method: str,
        slab: Slab,
        **kwargs
    ) -> Optional[UncertainValue]:
        """Execute slab-level parameter calculation."""

        # Import slab parameter modules
        if parameter == "A11":
            from snowpyt_mechparams.slab_parameters.A11 import calculate_A11
            return calculate_A11(method=method, slab=slab, **kwargs)

        elif parameter == "B11":
            from snowpyt_mechparams.slab_parameters.B11 import calculate_B11
            return calculate_B11(method=method, slab=slab, **kwargs)

        elif parameter == "D11":
            from snowpyt_mechparams.slab_parameters.D11 import calculate_D11
            return calculate_D11(method=method, slab=slab, **kwargs)

        elif parameter == "A55":
            from snowpyt_mechparams.slab_parameters.A55 import calculate_A55
            return calculate_A55(method=method, slab=slab, **kwargs)

        else:
            raise ValueError(f"Unknown slab parameter: {parameter}")
```

---

## Phase 4: Update Existing Code

### 4.1 Update Execution Module Imports

**Files to update:**
- `src/snowpyt_mechparams/execution/engine.py`
- `src/snowpyt_mechparams/execution/executor.py`
- `src/snowpyt_mechparams/execution/dispatcher.py`

**Changes:**
```python
# OLD (line 12-14 in executor.py)
sys.path.insert(0, '/Users/marykate/Desktop/Snow/SnowPyt-MechParams/algorithm')
from parameterization_algorithm import Parameterization, PathSegment, Branch

# NEW
from snowpyt_mechparams.algorithm import Parameterization, PathSegment, Branch
from snowpyt_mechparams.graph import graph
```

### 4.2 Update Package `__init__.py`

**File:** `src/snowpyt_mechparams/__init__.py`

**Add:**
```python
"""
SnowPyt-MechParams: Collaborative Python library for snow mechanical parameters.

Main Components
---------------
Data Structures
    Layer, Slab, Pit - Core data structures for snow profiles

Parameter Calculation
    layer_parameters - Methods for layer-level properties (density, E, ν, G)
    slab_parameters - Methods for slab-level plate theory parameters (A11, B11, D11, A55)

Parameterization Graph
    graph - Directed graph of all available calculation methods
    algorithm - Functions to find all calculation pathways

Execution Engine
    ExecutionEngine - Execute calculations across all pathways with dynamic programming
    ExecutionResults - Results from pathway execution with cache statistics

Quick Start
-----------
>>> from snowpyt_mechparams import ExecutionEngine
>>> from snowpyt_mechparams.graph import graph
>>> from snowpyt_mechparams.data_structures import Slab, Layer
>>>
>>> # Create slab with measured data
>>> layers = [Layer(thickness=30, density_measured=250, grain_form='RG')]
>>> slab = Slab(layers=layers, angle=35)
>>>
>>> # Execute all pathways to calculate D11
>>> engine = ExecutionEngine(graph)
>>> results = engine.execute_all(slab, target_parameter='D11')
>>> print(f"Computed D11 via {results.successful_pathways} pathways")
"""

# Existing exports
from snowpyt_mechparams.data_structures import Layer, Slab, Pit
from snowpyt_mechparams.execution import ExecutionEngine, ExecutionResults

# NEW exports
from snowpyt_mechparams import graph
from snowpyt_mechparams import algorithm

__all__ = [
    # Data structures
    "Layer",
    "Slab",
    "Pit",
    # Execution
    "ExecutionEngine",
    "ExecutionResults",
    # Graph and algorithm (as modules)
    "graph",
    "algorithm",
]

__version__ = "0.3.0"  # Bump version for new features
```

### 4.3 Update Examples

**Files to update:**
- `examples/execution_engine_demo.ipynb`
- Any other notebooks importing from `algorithm/`

**Pattern:**
```python
# OLD
sys.path.insert(0, '../algorithm')
from definitions import graph
from parameterization_algorithm import find_parameterizations

# NEW
from snowpyt_mechparams.graph import graph
from snowpyt_mechparams.algorithm import find_parameterizations
```

---

## Phase 5: Testing

[Testing section remains similar to original plan - see original document for full details]

Key tests to add:
- Test graph has slab parameter nodes
- Test D11 pathway enumeration
- Test execution with dynamic programming
- Test slab parameter calculation
- Test cache statistics

---

## Phase 6: Create D11 Comparison Notebook

[Notebook structure remains the same as original plan - see original document for full 10-section structure]

Key sections:
1. Introduction and Setup
2. Load ECTP Slabs
3. Execute All Pathways (with D11)
4. Data Loss Analysis
5. D11 Statistics by Pathway
6. D11 Statistics Across Pathways (Per Slab)
7. Variability vs Slab Properties
8. Pairwise Pathway Comparison
9. Heatmap Visualization
10. Summary and Export

---

## Phase 7: Documentation and Cleanup

[Documentation section remains the same as original plan]

Key updates:
- Add deprecation warnings to old algorithm files
- Update main README
- Create CHANGELOG entry
- Update pyproject.toml to v0.3.0

---

## Implementation Checklist

### Phase 1: Extend Graph ✅ REVISED
- [ ] 1.1 Add nodes to graph definition
  - [ ] Add layer property nodes (layer_location, layer_thickness)
  - [ ] Add slab parameter nodes (A11, B11, D11, A55)
  - [ ] Add merge nodes (zi, merge_E_nu, merge_zi_E_nu, merge_hi_G, merge_hi_E_nu)
  - [ ] Connect layer properties via data flow
  - [ ] Connect merge nodes correctly per diagram
  - [ ] Test graph structure
- [ ] 1.2 Verify Slab data structure (already has A11, B11, D11, A55)
- [ ] 1.3 Confirm execution order (already correct: layers then slab)

### Phase 2: Create Module Structure
- [ ] 2.1 Create `graph/` module
  - [ ] Create directory
  - [ ] Create `structures.py`
  - [ ] Create `definitions.py` with corrected merge structure
  - [ ] Create `__init__.py`
  - [ ] Create `README.md`
- [ ] 2.2 Create `algorithm.py`
  - [ ] Copy from algorithm/
  - [ ] Update imports
  - [ ] Add comprehensive docstrings

### Phase 3: Dynamic Programming
- [ ] 3.1 Enhance PathwayExecutor
  - [ ] Add persistent cache across pathways
  - [ ] Add cache statistics tracking
  - [ ] Implement `_get_or_compute_layer_param` with layer property handling
  - [ ] Remove cache clearing in `execute_parameterization`
- [ ] 3.2 Update ExecutionEngine
  - [ ] Manage cache lifecycle
  - [ ] Add cache stats to results
- [ ] 3.3 Slab parameter execution
  - [ ] Implement `_execute_slab_calculations` with prerequisite checks
  - [ ] Add slab-level caching via `_get_or_compute_slab_param`
  - [ ] Handle missing layer properties gracefully
- [ ] 3.4 Update dispatcher
  - [ ] Add ParameterLevel enum
  - [ ] Add `_execute_slab_method`
  - [ ] Handle A11, B11, D11, A55

### Phase 4: Update Existing Code
- [ ] 4.1 Update execution module
  - [ ] Update `engine.py` imports
  - [ ] Update `executor.py` imports
  - [ ] Update `dispatcher.py` imports
- [ ] 4.2 Update package `__init__.py`
  - [ ] Add graph and algorithm exports
  - [ ] Update docstrings
  - [ ] Bump version to 0.3.0
- [ ] 4.3 Update examples
  - [ ] Update `execution_engine_demo.ipynb`
  - [ ] Update other notebooks

### Phase 5: Testing
- [ ] 5.1 Create graph tests
  - [ ] Test graph structure with slab params
  - [ ] Test layer property nodes
  - [ ] Test merge node structure
- [ ] 5.2 Create algorithm tests
  - [ ] Test find_parameterizations for D11
  - [ ] Test pathway count
- [ ] 5.3 Create integration tests
  - [ ] Test D11 execution
  - [ ] Test dynamic programming cache
- [ ] 5.4 Run all tests

### Phase 6: D11 Comparison Notebook
- [ ] 6.1-6.12 Create and run notebook (see original plan for details)

### Phase 7: Documentation
- [ ] 7.1-7.4 Update documentation (see original plan for details)

---

## Success Criteria

1. ✅ Graph extends to include slab parameters with correct merge structure
2. ✅ Layer properties (depth_top, thickness) represented as data flow nodes
3. ✅ Algorithm and graph in production module structure
4. ✅ Dynamic programming reduces redundant calculations
5. ✅ All tests pass
6. ✅ D11 comparison notebook runs successfully on all ECTP slabs
7. ✅ Statistical analysis complete with pathway and cross-pathway comparisons
8. ✅ Documentation complete and accessible

---

## Estimated Timeline

- **Phase 1**: 2-3 hours (graph extension with corrected structure)
- **Phase 2**: 2-3 hours (module structure)
- **Phase 3**: 4-5 hours (dynamic programming + slab execution)
- **Phase 4**: 1-2 hours (updates)
- **Phase 5**: 3-4 hours (testing)
- **Phase 6**: 4-6 hours (notebook development and execution)
- **Phase 7**: 1-2 hours (documentation)

**Total**: 17-26 hours

---

## Notes and Considerations

### Layer Properties vs Calculated Parameters

**Key Distinction:**
- `layer_location` (depth_top) and `layer_thickness` (thickness) are **measured values** already on Layer objects
- The graph nodes represent them to show dependency structure
- No calculation is performed - they are direct data flow
- Executor must recognize these as special cases

### Merge Node Structure

The corrected merge structure reflects how slab calculations actually work:
- **zi**: Spatial information (where layers are located)
- **merge_E_nu**: Mechanical properties (E and ν together)
- **merge_zi_E_nu**: Combines spatial + mechanical for D11 (needs both)
- **merge_hi_G**: Thickness + shear for A55
- **merge_hi_E_nu**: Thickness + mechanical for A11/B11

### Dynamic Programming Benefits

With ~14,776 slabs and multiple pathways sharing common subpaths:
- **Without DP**: Each pathway recomputes all parameters (~236k layer calculations)
- **With DP**: Shared calculations cached (estimated 60-80% reduction)
- D11 pathways = (# density methods) × (# E methods) × (# ν methods) = 4 × 4 × 2 = 32 pathways

### Slab Parameter Dependencies

**A11, B11**: Need thickness + E + ν on all layers
**D11**: Need location + thickness + E + ν on all layers (most restrictive)
**A55**: Need thickness + G on all layers

Expect lower success rate for D11 due to additional location requirement and need for both E and ν.

---

## End of Revised Implementation Plan

This revised plan incorporates user feedback on the graph structure, correctly representing:
1. Layer properties as measured values (data flow nodes)
2. Corrected merge node structure matching the diagram
3. Proper handling of spatial information (zi) for D11
4. Clear distinction between layer-level and slab-level calculations
