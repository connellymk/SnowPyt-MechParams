# Execution Engine Implementation

This document describes the execution engine implementation that enables applying calculation pathways to snow pit data, computing mechanical parameters for each layer and slab.

## Overview

The execution engine bridges the gap between:
1. **The parameterization graph** - which defines all possible calculation pathways
2. **Snow pit data** - Layer and Slab objects with measured properties
3. **Calculation methods** - Functions that estimate mechanical parameters

Instead of just returning pathway descriptions as strings, the engine now **executes** each pathway, applying the appropriate methods to compute parameter values.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ExecutionEngine                             │
│  - High-level API for executing pathways                        │
│  - Discovers all parameterizations from graph                   │
│  - Coordinates execution across slabs                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PathwayExecutor                             │
│  - Executes a single parameterization on a slab                 │
│  - Handles layer-level and slab-level calculations              │
│  - Implements caching/dynamic programming                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MethodDispatcher                            │
│  - Maps graph edge names to function implementations            │
│  - Extracts inputs from Layer/Slab objects                      │
│  - Handles method-specific grain form resolution                │
└─────────────────────────────────────────────────────────────────┘
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
    slab: Slab
    method_calls: List[MethodCall]
    success: bool

@dataclass
class PathwayResult:
    """Complete results for one calculation pathway."""
    pathway_description: str
    methods_used: List[str]
    layer_results: List[LayerResult]
    slab_result: Optional[SlabResult]
    success: bool

@dataclass
class ExecutionResults:
    """Aggregated results from executing all pathways."""
    target_parameter: str
    source_slab: Slab
    results: Dict[str, PathwayResult]  # Keyed by pathway description
    total_pathways: int
    successful_pathways: int
```

### 2. `src/snowpyt_mechparams/execution/dispatcher.py`

Central registry mapping graph method names to implementations.

**Key Features:**
- `MethodSpec` dataclass defining method metadata (parameter, level, function, required inputs)
- `ParameterLevel` enum distinguishing layer-level vs slab-level calculations
- Method-specific grain form resolution for density methods
- Automatic input extraction from Layer objects

**Registered Methods:**

| Parameter | Method | Level | Required Inputs |
|-----------|--------|-------|-----------------|
| density | data_flow | layer | density_measured |
| density | geldsetzer | layer | hand_hardness, grain_form |
| density | kim_jamieson_table2 | layer | hand_hardness, grain_form |
| density | kim_jamieson_table5 | layer | hand_hardness, grain_form, grain_size |
| elastic_modulus | bergfeld | layer | density, grain_form |
| elastic_modulus | kochle | layer | density, grain_form |
| elastic_modulus | wautier | layer | density, grain_form |
| elastic_modulus | schottner | layer | density, grain_form |
| poissons_ratio | kochle | layer | grain_form |
| poissons_ratio | srivastava | layer | density, grain_form |
| shear_modulus | wautier | layer | density, grain_form |
| A11 | weissgraeber_rosendahl | slab | slab |
| B11 | weissgraeber_rosendahl | slab | slab |
| D11 | weissgraeber_rosendahl | slab | slab |
| A55 | weissgraeber_rosendahl | slab | slab |

**Grain Form Resolution:**

The dispatcher implements method-specific grain form resolution to maximize compatibility:

```python
DENSITY_METHOD_GRAIN_CODES = {
    "geldsetzer": {"PP", "PPgp", "DF", "RG", "RGmx", "FC", "FCmx", "DH"},
    "kim_jamieson_table2": {"PP", "PPgp", "DF", "RGxf", "FC", "FCxr", "DH", "MFcr", "RG"},
    "kim_jamieson_table5": {"FC", "FCxr", "PP", "PPgp", "DF", "MF"},
}
```

When resolving grain form for a method:
1. Try sub-grain class code first (e.g., `FCxr`) if it's in the method's valid set
2. Fall back to basic grain class code (e.g., `FC`)
3. Return the code even if invalid (method will return NaN)

### 3. `src/snowpyt_mechparams/execution/executor.py`

Executes a single parameterization pathway on a slab.

**Key Features:**
- Deep copies the slab to avoid modifying the original
- Processes methods in dependency order (from parameterization branches)
- Caches computed values on Layer objects for reuse
- Tracks all method calls for traceability

**Execution Flow:**
```
1. Deep copy slab
2. For each branch in parameterization:
   a. Extract method name from edge
   b. For each layer:
      - Gather inputs from layer
      - Execute method via dispatcher
      - Store result on layer (e.g., layer.density_calculated)
      - Record method call
3. Return PathwayResult with all layer results
```

### 4. `src/snowpyt_mechparams/execution/engine.py`

High-level API for executing pathways.

**Key Methods:**

```python
class ExecutionEngine:
    def __init__(self, graph: nx.DiGraph):
        """Initialize with the parameterization graph."""

    def execute_all(
        self,
        slab: Slab,
        target_parameter: str,
        include_plate_theory: bool = True
    ) -> ExecutionResults:
        """Execute all pathways for a target parameter."""

    def execute_single(
        self,
        slab: Slab,
        parameterization: Parameterization
    ) -> PathwayResult:
        """Execute a specific parameterization."""

    def list_available_pathways(
        self,
        target_parameter: str
    ) -> List[Dict[str, Any]]:
        """List all available pathways for a parameter."""
```

### 5. `src/snowpyt_mechparams/execution/__init__.py`

Package exports:
```python
from .engine import ExecutionEngine
from .results import ExecutionResults, PathwayResult, LayerResult, SlabResult, MethodCall
from .executor import PathwayExecutor
from .dispatcher import MethodDispatcher, MethodSpec, ParameterLevel
```

## Modified Files

### 1. `src/snowpyt_mechparams/__init__.py`

Added exports for the execution module:
```python
from .execution import (
    ExecutionEngine,
    ExecutionResults,
    PathwayResult,
    PathwayExecutor,
    MethodDispatcher,
)
```

### 2. `src/snowpyt_mechparams/data_structures/data_structures.py`

Added `grain_form_sub` field to Layer dataclass:
```python
@dataclass
class Layer:
    # ... existing fields ...
    grain_form: Optional[str] = None  # Basic grain class code (e.g., 'PP', 'RG', 'FC')
    grain_form_sub: Optional[str] = None  # Sub-grain class code (e.g., 'PPgp', 'RGmx', 'FCxr')
```

### 3. `examples/snowpilot_utils.py`

Updated `pit_to_layers()` to extract both grain form codes:
```python
# Extract grain form from grain_form_primary (both basic and sub codes)
grain_form = None
grain_form_sub = None
if hasattr(layer, 'grain_form_primary') and layer.grain_form_primary:
    grain_form = getattr(layer.grain_form_primary, 'basic_grain_class_code', None)
    grain_form_sub = getattr(layer.grain_form_primary, 'sub_grain_class_code', None)
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
from algorithm.definitions import graph

# Create a slab with layers
slab = Slab(
    layers=[
        Layer(
            depth_top=0,
            thickness=20,
            hand_hardness="F",
            grain_form="PP",
            grain_form_sub="PPgp"
        ),
        Layer(
            depth_top=20,
            thickness=30,
            hand_hardness="4F",
            grain_form="RG"
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

1. **Deep Copy Strategy**: Each pathway execution works on a deep copy of the slab to ensure pathways don't interfere with each other.

2. **Silent Failure**: Missing data causes methods to return None rather than raising exceptions, allowing partial results.

3. **Full Traceability**: Every method call is recorded with inputs, outputs, and any error messages.

4. **Dynamic Programming**: Computed values are stored on Layer objects and reused within a pathway (e.g., density computed once, used by multiple downstream methods).

5. **Method-Specific Grain Forms**: The dispatcher handles grain form resolution per-method to maximize compatibility with the lookup tables.
