# Graph Visualization

This document describes the graph visualization functionality added to the `graph/` module.

## Overview

The visualization module provides utilities to generate mermaid diagrams from the parameter dependency graph. This enables:
- Documentation of the complete graph structure
- Visual understanding of calculation pathways
- Automatic diagram generation that stays in sync with code

## Files Added

### 1. `visualize.py`
Core visualization module with functions:

- **`generate_mermaid_diagram(graph, title)`**: Generate mermaid syntax from a Graph object
- **`save_mermaid_diagram(graph, filepath, title)`**: Generate and save diagram to a file
- **`print_mermaid_diagram(graph, title)`**: Print diagram to stdout

Helper functions:
- `_classify_node(node)`: Classify nodes into visualization categories
- `_sanitize_node_id(parameter)`: Convert parameter names to valid mermaid IDs
- `_get_node_label(node)`: Generate display labels for nodes
- `_get_node_shape(node)`: Determine node shapes (rectangle vs diamond)

### 2. `generate_diagram.py`
Standalone script for diagram generation:
```bash
python generate_diagram.py [output_file.md]
```

### 3. `examples/generate_graph_diagram.py`
Example script demonstrating all three methods of diagram generation:
1. Print to stdout
2. Generate as string
3. Save to file

### 4. `docs/parameter_graph.md`
Complete visualization of the parameter graph with:
- Full mermaid diagram
- Node type descriptions
- Calculation method documentation
- Key pathways examples
- Usage instructions

### 5. `tests/test_graph_visualization.py`
Comprehensive tests for visualization functions:
- Node classification tests
- Node shape and label tests
- Diagram generation tests
- Tests for simple and complex graphs

## Usage

### From Python Code

```python
from snowpyt_mechparams.graph import graph, generate_mermaid_diagram

# Generate diagram as string
diagram = generate_mermaid_diagram(graph)
print(diagram)

# Save to file
from snowpyt_mechparams.graph import save_mermaid_diagram
save_mermaid_diagram(graph, "docs/parameter_graph.md")

# Print to stdout
from snowpyt_mechparams.graph import print_mermaid_diagram
print_mermaid_diagram(graph)
```

### From Command Line

```bash
# Print to stdout
python -m snowpyt_mechparams.graph.visualize

# Save to file
python -m snowpyt_mechparams.graph.visualize docs/parameter_graph.md

# Using standalone script
cd src/snowpyt_mechparams/graph
./generate_diagram.py ../../../docs/parameter_graph.md

# Using example script
cd examples
./generate_graph_diagram.py ../docs/parameter_graph.md
```

## Diagram Features

### Node Types and Colors

1. **Root Node** (Blue) - `snow_pit`
2. **Measured Parameters** (Yellow) - Direct measurements
3. **Merge Nodes** (Purple Diamonds) - Combine multiple inputs
4. **Layer Calculated** (Green) - Layer-level parameters
5. **Slab Calculated** (Orange) - Slab-level parameters

### Edge Labels

- **Unlabeled edges**: Data flow (no transformation)
- **Labeled edges**: Calculation methods (e.g., `|bergfeld|`)

### Styling

Automatic styling applied via mermaid classDefs:
- Border colors and widths
- Fill colors
- Node shapes (rectangles for parameters, diamonds for merges)

## Implementation Details

### Node Classification Algorithm

Nodes are classified based on:
1. Parameter name patterns (`measured_*`, `snow_pit`)
2. Node type (`parameter` vs `merge`)
3. Known parameter categories (density, elastic_modulus, D11, etc.)

### Edge Organization

Edges are grouped in the output for readability:
1. Snow pit to measured parameters
2. Density pathways
3. Elastic modulus pathways
4. Poisson's ratio pathways
5. Shear modulus pathways
6. Slab-level calculations

### ID Sanitization

Parameter names are sanitized for mermaid compatibility:
- Spaces → underscores
- Hyphens → underscores
- Special characters removed

## Extending the Visualization

To modify the visualization:

1. **Change node labels**: Edit `_get_node_label()` function
2. **Change node shapes**: Edit `_get_node_shape()` function
3. **Change colors/styling**: Edit the `classDef` lines in `generate_mermaid_diagram()`
4. **Add new node categories**: Update `_classify_node()` function

## Testing

Run visualization tests:
```bash
pytest tests/test_graph_visualization.py -v
```

Tests cover:
- Node classification for all types
- Label and shape generation
- Diagram generation for simple graphs
- Diagram generation for the complete graph
- Method edge labeling
- Styling application

## Integration with Documentation

The generated diagram can be embedded in:
- GitHub markdown files (renders automatically)
- Documentation sites (MkDocs, Sphinx with mermaid plugin)
- Jupyter notebooks (with mermaid extension)

## Future Enhancements

Potential additions:
1. Interactive HTML version with tooltips
2. Subgraph views (e.g., only layer-level or only slab-level)
3. Pathway highlighting (show specific calculation pathway)
4. Export to other formats (DOT, GraphML)
5. Node filtering by parameter type or method

## References

- Mermaid documentation: https://mermaid.js.org/
- Graph structures: `structures.py`
- Graph definition: `definitions.py`
- Algorithm documentation: `../algorithm/README.md`
