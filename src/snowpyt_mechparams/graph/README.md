# Parameter Graph Module

This module defines the parameter dependency graph for SnowPyt-MechParams, which represents all available calculation methods for snow mechanical parameters at both layer and slab levels.

## Overview

The parameter graph is a **directed graph** where:
- **Nodes** represent parameters (measured or calculated)
- **Edges** represent either data flow or calculation methods
- **Merge nodes** combine multiple parameters as inputs to a method

The graph enables the execution engine to:
1. Find all possible calculation pathways from measurements to target parameters
2. Determine which input parameters are needed for each pathway
3. Execute calculations in the correct dependency order

## Graph Structure

### Layer-Level Parameters

```
snow_pit → measured_density → density → elastic_modulus
        → measured_hand_hardness ↗         ↓
        → measured_grain_form ↗      poissons_ratio
        → measured_grain_size          ↓
                                  shear_modulus
```

**Available parameters:**
- `density` (kg/m³) - Snow density
- `elastic_modulus` (MPa) - Elastic (Young's) modulus
- `poissons_ratio` (dimensionless) - Poisson's ratio
- `shear_modulus` (MPa) - Shear modulus

### Slab-Level Parameters

```
measured_layer_thickness → zi ↘
                                merge_zi_E_nu → D11
elastic_modulus → merge_E_nu ↗ ↓
poissons_ratio → ↗              merge_hi_E_nu → A11, B11
measured_layer_thickness → ↗

measured_layer_thickness → merge_hi_G → A55
shear_modulus → ↗
```

**Available parameters:**
- `A11` (N/mm) - Extensional stiffness
- `B11` (N) - Bending-extension coupling stiffness
- `D11` (N·mm) - Bending stiffness
- `A55` (N/mm) - Shear stiffness with correction factor

All slab parameters use the `weissgraeber_rosendahl` method from [Weißgraeber & Rosendahl (2023)](https://doi.org/10.5194/tc-17-1475-2023).

## Node Types

### Parameter Nodes

Represent measured or calculated parameters. Examples:
- `snow_pit` - Root node representing measured snow pit data
- `density` - Calculated or measured snow density
- `D11` - Calculated bending stiffness

### Merge Nodes

Combine multiple parameters as inputs to a calculation method. Examples:
- `merge_density_grain_form` - Combines density and grain form for elastic modulus calculation
- `merge_E_nu` - Combines elastic modulus and Poisson's ratio from all layers
- `merge_zi_E_nu` - Combines spatial information with elastic properties for D11

**Key insight:** Merge nodes are shared between methods that use the same input combination, enabling efficient pathway enumeration.

## Usage

### Accessing the Graph

```python
from snowpyt_mechparams.graph import graph, D11

# Get a node by name
d11_node = graph.get_node("D11")

# Or use the exported node directly
print(D11.parameter)  # "D11"
print(D11.type)  # "parameter"
```

### Finding Calculation Pathways

```python
from snowpyt_mechparams.graph import graph, elastic_modulus
from snowpyt_mechparams.algorithm import find_parameterizations

# Find all ways to calculate elastic modulus
E_node = graph.get_node("elastic_modulus")
pathways = find_parameterizations(graph, E_node)

print(f"Found {len(pathways)} pathways")
# Output: Found 4 pathways (bergfeld, kochle, wautier, schottner)
```

### Exploring Graph Structure

```python
from snowpyt_mechparams.graph import graph, density

# Get density node
density_node = graph.get_node("density")

# Check incoming edges (methods that calculate density)
for edge in density_node.incoming_edges:
    if edge.method_name:
        print(f"Method: {edge.method_name}")
    else:
        print(f"Data flow from: {edge.start.parameter}")

# Check outgoing edges (what uses density)
for edge in density_node.outgoing_edges:
    print(f"Feeds into: {edge.end.parameter}")
```

## Layer Properties vs Calculated Parameters

**Important distinction:**

- **Layer properties** like `measured_layer_thickness` are **already available** on Layer objects
- These nodes in the graph represent **data flow**, not calculations
- No method is needed - the values are directly accessed from `layer.thickness`

**Calculated parameters** like `density` or `elastic_modulus`:
- Require calculation methods to derive from other parameters
- May have multiple alternative methods available

## Slab Parameter Dependencies

Slab parameters require **all layers** to have certain properties computed:

| Parameter | Required Layer Properties |
|-----------|---------------------------|
| A11 | thickness, elastic_modulus, poissons_ratio |
| B11 | thickness, elastic_modulus, poissons_ratio |
| D11 | thickness, elastic_modulus, poissons_ratio |
| A55 | thickness, shear_modulus |

The execution engine automatically:
1. Completes all layer-level calculations first
2. Checks that required properties are available on all layers
3. Computes slab parameters only when prerequisites are met

## Adding New Methods

To extend the graph with a new calculation method:

### 1. Implement the Method

Add your method to the appropriate module:

```python
# In layer_parameters/elastic_modulus.py
def _calculate_elastic_modulus_new_method(density, grain_form):
    """Your implementation here."""
    # ... calculation logic ...
    return result
```

### 2. Register in Dispatcher

Add the method to `execution/dispatcher.py`:

```python
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

### 3. Add to Graph

Add the method edge to `graph/definitions.py`:

```python
# If using existing merge node (density + grain_form)
build_graph.method_edge(merge_d_gf, elastic_modulus, "new_method")

# If you need a new merge node
merge_new = build_graph.merge("merge_new_inputs")
build_graph.flow(input1, merge_new)
build_graph.flow(input2, merge_new)
build_graph.method_edge(merge_new, output_param, "new_method")
```

### 4. Write Tests

Add tests in `tests/`:

```python
def test_new_method():
    layer = Layer(density_measured=250, grain_form="RG")
    result = calculate_elastic_modulus("new_method", 
                                       density=layer.density_measured,
                                       grain_form=layer.grain_form)
    assert result is not None
```

## References

### Layer Parameter Methods

- **Bergfeld et al. (2023)**: Elastic modulus from density and grain form
  - DOI: [10.5194/tc-17-1487-2023](https://doi.org/10.5194/tc-17-1487-2023)

- **Köchle & Schneebeli (2014)**: Elastic modulus and Poisson's ratio
  - DOI: [10.3189/2014JoG13J220](https://doi.org/10.3189/2014JoG13J220)

- **Wautier et al. (2015)**: Elastic and shear modulus from microstructure
  - DOI: [10.1002/2015GL065227](https://doi.org/10.1002/2015GL065227)

- **Schöttner et al. (2024)**: Elastic modulus from microstructure evolution
  - DOI: [10.5194/tc-18-1579-2024](https://doi.org/10.5194/tc-18-1579-2024)

### Slab Parameter Methods

- **Weißgraeber & Rosendahl (2023)**: Classical laminate theory for snow slabs
  - DOI: [10.5194/tc-17-1475-2023](https://doi.org/10.5194/tc-17-1475-2023)
  - Calculates: A11, B11, D11, A55 using plane-strain assumptions

## Related Documentation

- **Algorithm README** (`/algorithm/README.md`) - Detailed explanation of pathfinding algorithm
- **Algorithm Flowchart** (`/algorithm/algorithm_flowchart.md`) - Visual representation of algorithm
- **Execution Engine** (`/src/snowpyt_mechparams/execution/`) - How pathways are executed
- **Implementation Plan** (`/docs/implementation_plan_graph_integration_REVISED.md`) - This integration

## Visualization

The graph can be visualized as a mermaid diagram for documentation and understanding:

```python
from snowpyt_mechparams.graph import graph, generate_mermaid_diagram

# Generate mermaid diagram
diagram = generate_mermaid_diagram(graph)
print(diagram)

# Or save to file
from snowpyt_mechparams.graph import save_mermaid_diagram
save_mermaid_diagram(graph, "docs/parameter_graph.md")
```

You can also generate the diagram from the command line:

```bash
# Print to stdout
python -m snowpyt_mechparams.graph.visualize

# Save to file
python -m snowpyt_mechparams.graph.visualize docs/parameter_graph.md
```

Or use the standalone script:

```bash
cd src/snowpyt_mechparams/graph
python generate_diagram.py ../../../docs/parameter_graph.md
```

## Module Structure

```
graph/
├── __init__.py          # Module exports
├── structures.py        # Node, Edge, Graph, GraphBuilder classes
├── definitions.py       # Complete graph definition
├── visualize.py         # Mermaid diagram generation
├── generate_diagram.py  # Standalone diagram generator script
└── README.md           # This file
```

## Example: Complete Workflow

```python
from snowpyt_mechparams import ExecutionEngine
from snowpyt_mechparams.graph import graph
from snowpyt_mechparams.data_structures import Slab, Layer

# Create a slab with measured data
layers = [
    Layer(thickness=10, density_measured=250, grain_form='RG', hand_hardness='4F'),
    Layer(thickness=20, density_measured=300, grain_form='FC', hand_hardness='1F'),
]
slab = Slab(layers=layers, angle=35)

# Execute all pathways to calculate D11
engine = ExecutionEngine(graph)
results = engine.execute_all(slab, target_parameter='D11')

# Examine results
print(f"Successfully computed via {len(results.results)} pathways")
for pathway_desc, result in results.results.items():
    if result.success:
        print(f"{pathway_desc}: D11 = {result.slab.D11}")
```
