# Execution Engine Implementation

This document describes the execution engine implementation that enables applying calculation pathways to snow pit data, computing mechanical parameters for each layer and slab.

## Overview

The execution engine bridges the gap between:
1. **The parameterization graph** - which defines all possible calculation pathways
2. **Snow pit data** - Layer and Slab objects with measured properties
3. **Calculation methods** - Functions that estimate mechanical parameters

Instead of just returning pathway descriptions as strings, the engine now **executes** each pathway, applying the appropriate methods to compute parameter values.

### Module Structure

The implementation consists of:
- **Graph Module**: `src/snowpyt_mechparams/graph/` - Defines the parameter dependency graph
- **Algorithm Module**: `src/snowpyt_mechparams/algorithm.py` - Finds all calculation pathways
- **Execution Module**: `src/snowpyt_mechparams/execution/` - Executes pathways on data
- **Data Structures**: `src/snowpyt_mechparams/data_structures/` - Layer, Slab, UncertainValue

**Note**: There is also a legacy `algorithm/` directory in the project root that contains the original prototypes. The actual package uses the implementations in `src/snowpyt_mechparams/`.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ExecutionEngine                             │
│  - High-level API for executing pathways                        │
│  - Discovers all parameterizations from graph                   │
│  - Manages cache lifecycle across pathways                      │
│  - Provides cache statistics for performance analysis           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PathwayExecutor                             │
│  - Executes a single parameterization on a slab                 │
│  - Handles layer-level and slab-level calculations              │
│  - Implements dynamic programming via persistent cache          │
│  - Tracks cache hits/misses for statistics                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MethodDispatcher                            │
│  - Maps graph edge names to function implementations            │
│  - Extracts inputs from Layer/Slab objects                      │
│  - Handles method-specific grain form resolution                │
│  - Uses resolve_grain_form_for_method() from constants          │
└─────────────────────────────────────────────────────────────────┘
```

## Dynamic Programming & Caching

A key feature of the execution engine is **dynamic programming** via persistent caching across pathway executions for the same slab:

### Cache Strategy

The `PathwayExecutor` maintains three types of caches:

1. **Layer-level cache**: `(layer_index, parameter, method) -> value`
   - Caches computed layer parameters across pathways
   - Cleared between different slabs

2. **Slab-level cache**: `(parameter, method) -> value`
   - Caches computed slab parameters (A11, B11, D11, A55)
   - Cleared between different slabs

3. **Provenance tracking**: `(layer_index, parameter) -> method_name`
   - Records which method was used for each parameter
   - Useful for understanding calculation paths

### Cache Lifecycle

- **Persists** across pathway executions for the same slab (enabling dynamic programming)
- **Cleared** when `ExecutionEngine.execute_all()` is called for a new slab
- **Statistics** tracked and reported in `ExecutionResults.cache_stats`

### Benefits

When multiple pathways share common subpaths (e.g., all elastic modulus methods need density), the cache significantly reduces redundant calculations:

```python
# Example: 16 pathways for elastic_modulus
# (4 density methods × 4 elastic modulus methods)
# Without caching: 16 density calculations
# With caching: 4 density calculations (one per method)
# Cache hit rate: ~75%
```

## New Files Created

### 1. `src/snowpyt_mechparams/execution/results.py`

Defines dataclasses for storing execution results with full traceability.

```python
@dataclass
class MethodCall:
    """Records a single method invocation."""
    method_name: str
    parameter: str
    inputs: Dict[str, Any]
    output: Optional[UncertainValue]
    success: bool
    error_message: Optional[str]

@dataclass
class LayerResult:
    """Results for a single layer within a pathway."""
    layer_index: int
    layer: Layer  # The layer with computed values
    method_calls: List[MethodCall]
    success: bool

@dataclass
class SlabResult:
    """Results for slab-level calculations."""
    slab: Slab  # Deep copy with layers containing computed values
    layer_results: List[LayerResult]  # Per-layer computation details
    slab_method_calls: List[MethodCall]  # Slab-level calculations
    A11: Optional[UncertainValue]  # Extensional stiffness
    B11: Optional[UncertainValue]  # Bending-extension coupling stiffness
    D11: Optional[UncertainValue]  # Bending stiffness
    A55: Optional[UncertainValue]  # Shear stiffness

@dataclass
class PathwayResult:
    """Complete results for one calculation pathway."""
    pathway_id: str  # Unique identifier (e.g., "density:geldsetzer->elastic_modulus:bergfeld")
    pathway_description: str  # Human-readable description
    methods_used: Dict[str, str]  # Mapping of parameter -> method_name
    layer_results: List[LayerResult]
    slab_result: Optional[SlabResult]
    success: bool
    warnings: List[str]  # Non-fatal issues encountered

@dataclass
class ExecutionResults:
    """Aggregated results from executing all pathways."""
    target_parameter: str
    source_slab: Slab
    results: Dict[str, PathwayResult]  # Keyed by pathway description
    total_pathways: int
    successful_pathways: int
    failed_pathways: int
    cache_stats: Dict[str, float]  # Cache performance metrics (hits, misses, hit_rate)
```

### 2. `src/snowpyt_mechparams/execution/dispatcher.py`

Central registry mapping graph method names to implementations.

**Key Features:**
- `MethodSpec` dataclass defining method metadata (parameter, level, function, required inputs)
- `ParameterLevel` enum distinguishing layer-level vs slab-level calculations
- Method-specific grain form resolution using `resolve_grain_form_for_method()`
- Automatic input extraction from Layer objects via `_get_layer_input()`
- Smart density resolution: prefers `density_calculated` over `density_measured`
- NaN detection and handling in method results

**Registered Methods:**

| Parameter | Method | Level | Required Inputs | Notes |
|-----------|--------|-------|-----------------|-------|
| density | data_flow | layer | density_measured | Direct measurement |
| density | geldsetzer | layer | hand_hardness, grain_form | Geldsetzer lookup table |
| density | kim_jamieson_table2 | layer | hand_hardness, grain_form | Kim-Jamieson Table 2 |
| density | kim_jamieson_table5 | layer | hand_hardness, grain_form, grain_size | Kim-Jamieson Table 5 |
| elastic_modulus | bergfeld | layer | density, grain_form | Bergfeld (2023) |
| elastic_modulus | kochle | layer | density, grain_form | Köchle & Schneebeli (2014) |
| elastic_modulus | wautier | layer | density, grain_form | Wautier et al. (2015) |
| elastic_modulus | schottner | layer | density, grain_form | Scapozza (2004) via Schottner |
| poissons_ratio | kochle | layer | grain_form | Köchle (grain-form dependent) |
| poissons_ratio | srivastava | layer | density, grain_form | Srivastava et al. (2016) |
| shear_modulus | wautier | layer | density, grain_form | Wautier et al. (2015) |
| A11 | weissgraeber_rosendahl | slab | slab | Requires E, ν on all layers |
| B11 | weissgraeber_rosendahl | slab | slab | Requires E, ν on all layers |
| D11 | weissgraeber_rosendahl | slab | slab | Requires E, ν on all layers |
| A55 | weissgraeber_rosendahl | slab | slab | Requires G on all layers |

**Grain Form Resolution:**

The grain form resolution logic is centralized in `snowpilot_constants.py` to maximize compatibility:

```python
# In snowpilot_constants.py
GRAIN_FORM_METHODS = {
    "geldsetzer": {
        "sub_grain_class": {"PPgp", "RGmx", "FCmx"},
        "basic_grain_class": {"PP", "DF", "RG", "FC", "DH"},
    },
    "kim_jamieson_table2": {
        "sub_grain_class": {"PPgp", "RGxf", "FCxr", "MFcr"},
        "basic_grain_class": {"PP", "DF", "FC", "DH", "RG"},
    },
    "kim_jamieson_table5": {
        "sub_grain_class": {"FCxr", "PPgp"},
        "basic_grain_class": {"FC", "PP", "DF", "MF"},
    },
}

def resolve_grain_form_for_method(grain_form, method):
    """Resolve which grain form code to use for a given density method."""
    # Try full grain_form first (could be a sub-grain code)
    # Fall back to basic grain class (first 2 characters)
    # Return None if no valid mapping found
```

When resolving grain form for a method:
1. Try the full `grain_form` first (could be a sub-grain code like `FCxr`)
2. If not valid, try the basic grain class (first 2 characters, e.g., `FC`)
3. Return `None` if no valid mapping found (method will return `None`)

### 3. `src/snowpyt_mechparams/execution/executor.py`

Executes a single parameterization pathway on a slab.

**Key Features:**
- Deep copies the slab to avoid modifying the original
- Processes methods in dependency order (from parameterization branches)
- Implements persistent caching across pathways for dynamic programming
- Tracks all method calls for traceability
- Provides cache statistics (hits, misses, hit rate)

**Execution Flow:**
```
1. Deep copy slab (don't modify original)
2. Extract methods from parameterization:
   - Walk through branches and merge points
   - Build mapping: parameter -> method_name
   - Generate pathway_id and pathway_description
3. For each layer:
   a. Determine execution order (density first, then E, ν, G)
   b. For each parameter in order:
      - Check cache: (layer_index, parameter, method)
      - If cached: retrieve and update layer (cache hit)
      - If not cached: execute via dispatcher, cache result (cache miss)
      - Record method call for traceability
4. If include_plate_theory:
   a. Check prerequisites for each slab parameter
   b. Compute A11, B11, D11 (if E and ν available on all layers)
   c. Compute A55 (if G available on all layers)
   d. Use slab-level cache: (parameter, method)
5. Return PathwayResult with layers, slab, and traces
```

**Helper Methods:**

- `_extract_methods_from_parameterization()`: Extracts parameter->method mapping
- `_build_pathway_description()`: Creates human-readable description
- `_build_pathway_id()`: Creates unique identifier
- `_determine_execution_order()`: Orders parameters by dependencies
- `_get_or_compute_layer_param()`: Implements caching for layer parameters
- `_get_or_compute_slab_param()`: Implements caching for slab parameters

**Special Handling:**

- **Layer thickness**: Direct data flow from `layer.thickness`, no calculation needed
- **Slab parameters**: Require all layers to have necessary properties before attempting calculation
- **Cache persistence**: Cache is NOT cleared between pathways (enables dynamic programming)

### 4. `src/snowpyt_mechparams/execution/engine.py`

High-level API for executing pathways.

**Key Methods:**

```python
class ExecutionEngine:
    def __init__(
        self,
        graph: Graph,
        dispatcher: Optional[MethodDispatcher] = None
    ):
        """Initialize with the parameterization graph."""

    def execute_all(
        self,
        slab: Slab,
        target_parameter: str,
        include_plate_theory: bool = True
    ) -> ExecutionResults:
        """
        Execute all pathways for a target parameter.
        
        Clears the cache at the start, then cache persists across
        pathway executions for dynamic programming.
        """

    def execute_single(
        self,
        slab: Slab,
        target_parameter: str,
        methods: Dict[str, str],
        include_plate_theory: bool = True
    ) -> Optional[PathwayResult]:
        """
        Execute a single specific parameterization pathway.
        
        Parameters
        ----------
        methods : dict
            Mapping of parameter -> method to use
            (e.g., {"density": "geldsetzer", "elastic_modulus": "bergfeld"})
        """

    def list_available_pathways(
        self,
        target_parameter: str
    ) -> List[Dict[str, Any]]:
        """
        List all available pathways for a parameter.
        
        Returns list of dicts with keys: 'id', 'description', 'methods'
        """
```

### 5. `src/snowpyt_mechparams/execution/__init__.py`

Package exports:
```python
from .engine import ExecutionEngine
from .results import (
    ExecutionResults, 
    PathwayResult, 
    LayerResult, 
    SlabResult, 
    MethodCall
)
from .executor import PathwayExecutor
from .dispatcher import MethodDispatcher, MethodSpec, ParameterLevel
```

### 6. `src/snowpyt_mechparams/snowpilot_utils/snowpilot_constants.py`

Centralized constants and grain form resolution:
```python
# Grain form codes organized by method
GRAIN_FORM_METHODS = {
    "geldsetzer": {
        "sub_grain_class": {"PPgp", "RGmx", "FCmx"},
        "basic_grain_class": {"PP", "DF", "RG", "FC", "DH"},
    },
    # ... other methods ...
}

def resolve_grain_form_for_method(grain_form, method):
    """
    Resolve which grain form code to use for a given density method.
    This is the single source of truth for grain form validation logic.
    """
```

## Modified Files

### 1. `src/snowpyt_mechparams/__init__.py`

Added exports for the execution module and graph:
```python
# Execution engine
from snowpyt_mechparams.execution import (
    ExecutionEngine,
    ExecutionResults,
    PathwayResult,
    PathwayExecutor,
    MethodDispatcher,
)

# Graph and algorithm modules (imported as modules)
from snowpyt_mechparams import graph
from snowpyt_mechparams import algorithm
```

**Recommended imports for users:**
```python
# Main execution engine
from snowpyt_mechparams import ExecutionEngine, Slab, Layer

# Graph for parameterization
from snowpyt_mechparams.graph import graph

# Algorithm for finding pathways
from snowpyt_mechparams.algorithm import find_parameterizations
```

### 2. `src/snowpyt_mechparams/data_structures/data_structures.py`

The `grain_form` field in Layer dataclass can now store either basic or sub-grain codes:
```python
@dataclass
class Layer:
    # ... existing fields ...
    grain_form: Optional[str] = None  
    # Grain form code: sub-grain class (e.g., 'FCxr', 'PPgp', 'RGmx') if available,
    # otherwise basic class (e.g., 'FC', 'PP', 'RG')
```

The `main_grain_form` property extracts the 2-character basic code:
```python
@property
def main_grain_form(self) -> Optional[str]:
    """Return first 2 characters of grain_form (basic grain class code)."""
    if self.grain_form and len(self.grain_form) >= 2:
        return self.grain_form[:2]
    return self.grain_form
```

### 3. `src/snowpyt_mechparams/snowpilot_utils/snowpilot_convert.py`

The grain form conversion logic extracts grain forms from SnowPilot/CAAML data:
```python
# Extract grain form - prefer sub-grain class code if available
grain_form = None
if hasattr(layer, 'grain_form_primary') and layer.grain_form_primary:
    # Try sub-grain class code first (more specific)
    grain_form = getattr(layer.grain_form_primary, 'sub_grain_class_code', None)
    # Fall back to basic grain class code
    if not grain_form:
        grain_form = getattr(layer.grain_form_primary, 'basic_grain_class_code', None)
```

## Example Notebooks

### 1. `examples/execution_engine_demo.ipynb`

Comprehensive demonstration of execution engine features:
- Basic usage with manually created slabs
- Executing all pathways for a parameter
- Examining results with full traceability
- Handling missing data scenarios
- Plate theory parameter calculations

### 2. `examples/density_calculation_demo.ipynb`

Calculates density for the entire SnowPilot dataset:
- Loads ~50,000 snow pit XML files
- Executes all 4 density pathways on each slab
- Analyzes success rates by pathway
- Compares estimated vs measured density
- Visualizes density distributions
- Exports results to DataFrame

### 3. `examples/elastic_modulus_calculation_demo.ipynb`

Calculates elastic modulus using chained pathways:
- Demonstrates 16 pathways (4 density × 4 elastic modulus methods)
- Compares elastic modulus methods (Bergfeld, Kochle, Wautier, Schottner)
- Analyzes impact of density estimation choice on final E values
- Visualizes E vs density relationships
- Exports comprehensive results

## Usage Example

```python
from snowpyt_mechparams import ExecutionEngine, Slab, Layer
from snowpyt_mechparams.graph import graph

# Create a slab with layers
# Note: grain_form can contain either basic codes (e.g., 'PP', 'RG')
# or sub-grain codes (e.g., 'PPgp', 'RGmx')
slab = Slab(
    layers=[
        Layer(
            depth_top=0,
            thickness=20,
            hand_hardness="F",
            grain_form="PPgp"  # Sub-grain class code
        ),
        Layer(
            depth_top=20,
            thickness=30,
            hand_hardness="4F",
            grain_form="RG"  # Basic grain class code
        )
    ],
    angle=38.0
)

# Initialize engine
engine = ExecutionEngine(graph)

# Execute all density pathways
results = engine.execute_all(slab, "density")

# Examine results
print(f"Successful: {results.successful_pathways}/{results.total_pathways}")
print(f"Cache hit rate: {results.cache_stats['hit_rate']:.1%}")

for pathway_desc, pathway_result in results.results.items():
    if pathway_result.success:
        print(f"\n{pathway_desc}")
        for lr in pathway_result.layer_results:
            density = lr.layer.density_calculated
            print(f"  Layer {lr.layer_index}: {density.nominal_value:.1f} kg/m³")
```

## Known Limitations

### Grain Form Coverage

Not all grain forms in SnowPilot data are supported by the density estimation methods:

| Grain Form | Occurrence | Support |
|------------|------------|---------|
| FC (Faceted crystals) | Common | ✅ All methods |
| RG (Rounded grains) | Common | ✅ Geldsetzer, Kim T2 |
| MF (Melt forms) | Common | ⚠️ Only MFcr sub-code in Kim T2; MF in Kim T5 |
| DF (Decomposing forms) | Common | ✅ All methods |
| IF (Ice formations) | Moderate | ❌ No support |
| PP (Precipitation particles) | Moderate | ✅ All methods |
| DH (Depth hoar) | Moderate | ✅ Geldsetzer, Kim T2 |
| SH (Surface hoar) | Low | ❌ No support |

### Data Availability

Pathway success depends on data availability in the snow pit:

| Data Field | Typical Availability | Impact |
|------------|---------------------|--------|
| density_measured | ~3% | data_flow pathway rarely succeeds |
| hand_hardness | ~92% | Required for all estimation methods |
| grain_form | ~88% | Required for all methods |
| grain_size_avg | ~52% | Required only for Kim T5 |

## Design Decisions

1. **Deep Copy Strategy**: Each pathway execution works on a deep copy of the slab to ensure the original slab is never modified. However, the cache persists across pathway executions for the same slab.

2. **Persistent Cache for Dynamic Programming**: The cache is NOT cleared between pathway executions for the same slab. This enables dynamic programming where common subpaths are computed once and reused. The cache is only cleared when switching to a new slab via `ExecutionEngine.execute_all()`.

3. **Silent Failure**: Missing data causes methods to return `None` rather than raising exceptions, allowing partial results. Failures are recorded in `MethodCall.failure_reason` for traceability.

4. **Full Traceability**: Every method call is recorded with inputs, outputs, and failure reasons. The `PathwayResult` includes complete provenance information.

5. **Method-Specific Grain Forms**: Grain form resolution is centralized in `snowpilot_constants.resolve_grain_form_for_method()` to maximize compatibility with method-specific lookup tables.

6. **Layer Properties vs Parameters**: Layer properties like `thickness` are direct data flow (no calculation), while parameters like `density` require calculation methods.

7. **Slab Parameter Prerequisites**: Slab-level calculations (A11, B11, D11, A55) check prerequisites before attempting computation. Missing prerequisites result in `None` with a descriptive failure reason.
