# SnowPyt-MechParams

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A collaborative Python library for estimating mechanical parameters of snow layers and snow slabs from snow pit measurements. This package provides scientifically-validated methods to calculate layer-level mechanical properties (density, elastic modulus, Poisson's ratio, shear modulus) and slab-level plate theory parameters (A11, B11, D11, A55) from standard snowpit observations.

**Key Innovation**: SnowPyt-MechParams implements a **parameterization graph** that automatically discovers and executes **all possible calculation pathways** from measured inputs to target parameters, using dynamic programming to efficiently compute results across multiple methods.

## Features

### 🎯 Core Capabilities

- **Multi-Method Parameter Estimation**: Calculate snow mechanical parameters using multiple published methods
- **Parameterization Graph**: Directed graph representing all calculation pathways and method dependencies
- **Automatic Pathway Discovery**: Algorithm finds all valid combinations of methods to reach target parameters
- **Dynamic Programming Execution**: Cache intermediate results to avoid redundant calculations
- **Layer & Slab Parameters**: Support for both individual layer properties and integrated slab-level stiffnesses
- **Uncertainty Propagation**: Built-in support for uncertainty quantification via the `uncertainties` package
- **SnowPilot Integration**: Parse CAAML files directly from the SnowPilot dataset

### 📊 Supported Parameters & Methods

**Layer-Level Parameters:**

- **Density** (ρ, kg/m³)
  - Direct measurement (data_flow)
  - Geldsetzer et al. (2009) - from hand hardness and grain form
  - Kim & Jamieson (2010) Table 2 - from hand hardness and grain form
  - Kim & Jamieson (2010) Table 5 - from hand hardness, grain form, and grain size

- **Elastic Modulus** (E, MPa)
  - Bergfeld et al. (2023) - from density and grain form
  - Köchle & Schneebeli (2014) - from density and grain form
  - Wautier et al. (2015) - from density and grain form
  - Schöttner et al. (2024) - from density and grain form

- **Poisson's Ratio** (ν, dimensionless)
  - Köchle & Schneebeli (2014) - from grain form only
  - Srivastava et al. (2016) - from density and grain form

- **Shear Modulus** (G, MPa)
  - Wautier et al. (2015) - from density and grain form

**Slab-Level Parameters (Plate Theory):**

- **A11** (N/mm): Extensional stiffness
- **B11** (N): Bending-extension coupling stiffness
- **D11** (N·mm): Bending stiffness
- **A55** (N/mm): Shear stiffness (with correction factor κ = 5/6)

All slab parameters calculated using classical laminate theory (Weißgraeber & Rosendahl 2023).

### 🚀 Parameterization Graph System

The graph-based calculation system enables:

- **32 unique pathways to D11**: Automatically discovers all valid method combinations (4 density × 4 elastic modulus × 2 Poisson's ratio)
- **Method independence**: Each method implemented independently, graph handles dependencies
- **Extensibility**: Add new methods by implementing the function and adding a graph edge
- **Provenance tracking**: Know exactly which methods produced each value
- **Failure analysis**: Understand why calculations fail (missing data, unsupported grain forms, etc.)

**Example:** To calculate D11 (bending stiffness), the system needs:
1. Density (4 possible methods: data_flow, geldsetzer, kim_jamieson_table2, kim_jamieson_table5)
2. Elastic modulus (4 possible methods: bergfeld, kochle, wautier, schottner)
3. Poisson's ratio (2 possible methods: kochle, srivastava)
4. Layer positions and thicknesses (from measurements)

The graph automatically finds all valid combinations: 4 × 4 × 2 = **32 pathways**

**Note**: The `data_flow` density method uses measured density directly when available on the layer.

## Installation

### Prerequisites

- **Python 3.8 or higher** (Python 3.9+ recommended)
- **pip** (usually comes with Python)
- **git** (for cloning the repository)

Check your Python version:
```bash
python3 --version
```

### Virtual Environment Setup (Recommended)

We strongly recommend using a virtual environment to manage dependencies and avoid conflicts with other Python projects.

#### Quick Setup (Automated)

For a quick automated setup, run:
```bash
./setup.sh
```

This script will create the virtual environment, upgrade pip, and install the package.

#### Manual Setup

#### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment (named 'venv')
python3 -m venv venv
```

#### Step 3: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` appear in your terminal prompt when activated.

#### Step 4: Upgrade pip (Recommended)

```bash
pip install --upgrade pip setuptools wheel
```

#### Step 5: Install the Package

**Standard Installation (editable mode):**
```bash
pip install -e .
```

**Development Installation (includes testing and development tools):**
```bash
pip install -e .[dev]
```

This installs the package in "editable" mode, meaning changes to the source code will be immediately available without reinstalling.

#### Step 6: Verify Installation

```bash
python -c "import snowpyt_mechparams; print('Installation successful!')"
```

#### Deactivate Virtual Environment

When you're done working:
```bash
deactivate
```

### Using with Jupyter Notebooks

To use this package in Jupyter notebooks with your virtual environment:

1. **Activate your virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install ipykernel:**
   ```bash
   pip install ipykernel
   ```

3. **Register the kernel:**
   ```bash
   python -m ipykernel install --user --name=snowpyt-mechparams --display-name="Python (SnowPyt-MechParams)"
   ```

4. **In Jupyter:** Select "Python (SnowPyt-MechParams)" from the kernel dropdown menu.

## Quick Start

### Basic Usage: Calculate Parameters for a Single Layer

```python
from snowpyt_mechparams.data_structures import Layer
from snowpyt_mechparams.layer_parameters import calculate_density, calculate_elastic_modulus
from uncertainties import ufloat

# Create a layer with measurements
layer = Layer(
    depth_top=10,                          # cm from surface
    thickness=15,                          # cm
    hand_hardness='1F',                    # Hand hardness code
    grain_form='RG',                       # Rounded grains
    grain_size_avg=ufloat(1.0, 0.1)       # mm ± uncertainty
)

# Calculate density using Kim & Jamieson Table 2 method
density = calculate_density(
    method='kim_jamieson_table2',
    hand_hardness=layer.hand_hardness,
    grain_form=layer.grain_form
)
print(f"Density: {density:.1f} kg/m³")

# Calculate elastic modulus using Bergfeld method
E = calculate_elastic_modulus(
    method='bergfeld',
    density=density,
    grain_form=layer.grain_form
)
print(f"Elastic modulus: {E:.2f} MPa")
```

### Advanced Usage: Execute All Pathways for a Slab

```python
from snowpyt_mechparams import ExecutionEngine
from snowpyt_mechparams.graph import graph
from snowpyt_mechparams.data_structures import Slab, Layer
from uncertainties import ufloat

# Create a slab with multiple layers
layers = [
    Layer(depth_top=0, thickness=ufloat(20, 1), hand_hardness='1F', grain_form='RG'),
    Layer(depth_top=20, thickness=ufloat(15, 1), hand_hardness='P', grain_form='FC'),
    Layer(depth_top=35, thickness=ufloat(25, 1), density_measured=ufloat(200, 18), grain_form='DF')
]
slab = Slab(layers=layers, angle=35.0)  # 35° slope

# Initialize execution engine
engine = ExecutionEngine(graph)

# Execute ALL pathways to calculate D11 (bending stiffness)
results = engine.execute_all(
    slab=slab,
    target_parameter='D11'
)

print(f"Total pathways attempted: {results.total_pathways}")
print(f"Successful pathways: {results.successful_pathways}")
print(f"Cache hit rate: {results.cache_stats['hit_rate']:.1%}")

# Examine results from different pathways
for pathway_desc, pathway_result in results.pathways.items():
    if pathway_result.success and pathway_result.slab.D11:
        print(f"\nPathway: {pathway_desc}")
        print(f"  Methods: {pathway_result.methods_used}")
        print(f"  D11 = {pathway_result.slab.D11:.1f} N·mm")
```

### Using with SnowPilot Data

```python
from snowpyt_mechparams import ExecutionEngine
from snowpyt_mechparams.graph import graph
from snowpyt_mechparams.snowpilot_utils import parse_caaml_file
from snowpyt_mechparams.data_structures import Pit

# Parse CAAML file from SnowPilot
snow_pit = parse_caaml_file('path/to/snowpits-12345-caaml.xml')

# Create Pit object
pit = Pit.from_snow_pit(snow_pit)

# Create slabs from ECTP (Extended Column Test with Propagation) failures
slabs = pit.create_slabs(weak_layer_def="ECTP_failure_layer")

# Initialize execution engine
engine = ExecutionEngine(graph)

# Execute all pathways for each slab
for slab in slabs:
    results = engine.execute_all(slab, target_parameter='D11')
    
    print(f"Slab {slab.slab_id}: {results.successful_pathways}/{results.total_pathways} pathways succeeded")
    print(f"Cache hit rate: {results.cache_stats['hit_rate']:.1%}")
    
    # Access successful D11 values
    for desc, pathway_result in results.get_successful_pathways().items():
        if pathway_result.slab.D11:
            print(f"  {desc}: D11 = {pathway_result.slab.D11:.1f} N·mm")
```

## Core Modules

### Data Structures (`snowpyt_mechparams.data_structures`)

- **`Layer`**: Represents a single snow layer with measured and calculated properties
- **`Slab`**: Collection of layers representing a snow slab above a weak layer
- **`Pit`**: Complete snow pit profile with layers and stability test results

### Parameter Calculation

**Layer Parameters** (`snowpyt_mechparams.layer_parameters`):
- `density.py` - Density estimation methods
- `elastic_modulus.py` - Elastic modulus estimation methods
- `poissons_ratio.py` - Poisson's ratio estimation methods
- `shear_modulus.py` - Shear modulus estimation methods

**Slab Parameters** (`snowpyt_mechparams.slab_parameters`):
- `A11.py` - Extensional stiffness (classical laminate theory)
- `B11.py` - Bending-extension coupling
- `D11.py` - Bending stiffness (critical for avalanche modeling)
- `A55.py` - Shear stiffness

### Parameterization Graph (`snowpyt_mechparams.graph`)

- **`structures.py`**: Graph data structures (Node, Edge, Graph, GraphBuilder)
- **`definitions.py`**: Complete parameter dependency graph with all methods
- **`visualize.py`**: Mermaid diagram generation for graph visualization
- **`README.md`**: Documentation on graph structure and extending the graph

The graph represents:
- **Parameter nodes**: Measured or calculated parameters
- **Merge nodes**: Combinations of inputs required for methods
- **Edges**: Calculation methods or data flow connections

**Visualization**: Generate mermaid diagrams to visualize the graph:
```python
from snowpyt_mechparams.graph import graph, save_mermaid_diagram
save_mermaid_diagram(graph, "docs/parameter_graph.md")
```
See [`docs/parameter_graph.md`](docs/parameter_graph.md) for the complete graph visualization.

### Algorithm (`snowpyt_mechparams.algorithm`)

Core algorithm that finds all possible parameterization pathways:

```python
from snowpyt_mechparams.algorithm import find_parameterizations
from snowpyt_mechparams.graph import graph

# Find all pathways to calculate D11
D11_node = graph.get_node("D11")
pathways = find_parameterizations(graph, D11_node)
print(f"Found {len(pathways)} pathways to calculate D11")  # Output: 32 pathways
```

**Algorithm features:**
- Recursive backtracking from target parameter to measured inputs
- Memoization to avoid recomputing shared subgraphs
- OR logic for parameter nodes (alternative methods)
- AND logic for merge nodes (all inputs required)
- Automatic discovery of all valid method combinations

**Example output for D11:**
- 32 unique pathways combining:
  - 4 density methods (including direct measurement via data_flow)
  - 4 elastic modulus methods
  - 2 Poisson's ratio methods

See `docs/execution_engine.md` for detailed architecture and implementation documentation with Mermaid diagrams.

### Execution Engine (`snowpyt_mechparams.execution`)

Executes parameterization pathways with dynamic programming:

- **`ExecutionEngine`**: Orchestrates pathway execution for all pathways
- **`PathwayExecutor`**: Executes individual pathways with layer-level caching
- **`MethodDispatcher`**: Routes method calls to implementations
- **`ComputationCache`**: Layer-level cache with provenance tracking
- **`ExecutionConfig`**: Optional configuration (verbose mode)
- **`ExecutionResults`**: Container for all pathway results with cache statistics
- **`PathwayResult`**: Individual pathway result with slab parameters and computation traces

**Key features:**
- **Dynamic programming**: Caches layer-level parameters within each slab (density, elastic modulus, Poisson's ratio)
- **Copy-on-write optimization**: Efficient layer copying for minimal memory overhead
- **Provenance tracking**: Full computation traces showing which methods computed each value
- **Cache statistics**: Real-time hit rates and performance metrics
- **Graceful failure handling**: Continues when methods fail (unsupported grain forms, missing data)
- **Performance**: 40-50% cache hit rates on typical D11 calculations, significantly reducing redundant computations

## Examples

Comprehensive examples are available in the `examples/` directory:

### Basic Examples

- `execution_engine_demo.ipynb` - Introduction to the execution engine
- `density_kim_jamieson_table5.ipynb` - Density estimation examples
- `emod_bergfeld.ipynb` - Elastic modulus calculations
- `poissons_ratio_comparison.ipynb` - Comparing Poisson's ratio methods

### Advanced Analysis

- **`compare_D11_across_pathways_v3.ipynb`** - Comprehensive D11 analysis across all 32 pathways
  - Processes ~50,000 snow pits from SnowPilot dataset
  - Executes ~473,000 pathway calculations (14,776 slabs × 32 pathways)
  - Analyzes success rates, inter-pathway variability, and method comparisons
  - Explores relationships between variability and slab properties
  - Generates publication-ready figures
  - **Runtime**: 15-30 minutes

- **`compare_D11_across_pathways.ipynb`** - Legacy analysis (archived)
  - Original notebook, superseded by v3

### Visualization Examples

- `dataset_stats.ipynb` - Dataset statistics and visualizations
- Example outputs include pathway success rate charts, D11 distributions, and variability analysis

### Dataset Examples

- `analyze_ectp_slabs.ipynb` - Create slabs from ECTP test results
- `dataset_stats.ipynb` - Dataset summary statistics
- `dataset_temp_info.ipynb` - Temperature data analysis

## Project Structure

```
SnowPyt-MechParams/
├── src/snowpyt_mechparams/       # Main package source
│   ├── data_structures/          # Layer, Slab, Pit classes
│   ├── layer_parameters/         # Layer-level calculation methods
│   │   ├── density.py            # 4 density methods
│   │   ├── elastic_modulus.py    # 4 elastic modulus methods
│   │   ├── poissons_ratio.py     # 2 Poisson's ratio methods
│   │   └── shear_modulus.py      # Shear modulus method
│   ├── slab_parameters/          # Slab-level calculation methods
│   │   ├── A11.py                # Extensional stiffness
│   │   ├── B11.py                # Bending-extension coupling
│   │   ├── D11.py                # Bending stiffness
│   │   └── A55.py                # Shear stiffness
│   ├── graph/                    # Parameterization graph
│   │   ├── structures.py         # Graph data structures
│   │   ├── definitions.py        # Complete parameter dependency graph
│   │   ├── visualize.py          # Mermaid diagram generation
│   │   └── README.md             # Graph documentation
│   ├── algorithm.py              # Pathway discovery algorithm
│   ├── execution/                # Execution engine with dynamic programming
│   │   ├── engine.py             # ExecutionEngine
│   │   ├── executor.py           # PathwayExecutor with caching
│   │   ├── dispatcher.py         # MethodDispatcher
│   │   ├── cache.py              # ComputationCache
│   │   ├── config.py             # ExecutionConfig
│   │   └── results.py            # Result containers
│   └── snowpilot_utils.py        # SnowPilot CAAML parsing
├── examples/                     # Jupyter notebook examples
│   ├── compare_D11_across_pathways_v3.ipynb    # Full D11 analysis (current)
│   ├── compare_D11_across_pathways.ipynb       # Legacy analysis
│   ├── dataset_stats.ipynb       # Dataset statistics
│   └── data/                     # SnowPilot dataset (50,278 CAAML files)
├── tests/                        # Test suite (pytest)
│   ├── test_integration.py       # Integration tests
│   ├── test_executor_dynamic_programming.py  # Cache tests
│   ├── test_computation_cache.py # Cache unit tests
│   └── ...                       # Additional test modules
├── docs/                         # Documentation
│   ├── execution_engine.md       # Complete architecture & implementation
│   ├── parameter_graph.md        # Complete graph visualization
│   └── REFACTORING_COMPLETE.md   # Implementation summary
└── README.md                     # This file
```

## Documentation

### API Documentation

Full API documentation is available at: [https://snowpyt-mechparams.readthedocs.io/](https://snowpyt-mechparams.readthedocs.io/)

For local documentation:
```bash
cd docs
make html
```

### Key Documentation Files

- **`README.md`** (this file): Project overview and quick start
- **`docs/execution_engine.md`**: Complete architecture and implementation with Mermaid diagrams
- **`docs/parameter_graph.md`**: Full graph visualization
- **`src/snowpyt_mechparams/graph/README.md`**: Graph structure and extension guide
- **`src/snowpyt_mechparams/graph/definitions.py`**: Comprehensive inline documentation of all methods

## Testing

Run the test suite:
```bash
pytest
```

With coverage report:
```bash
pytest --cov=snowpyt_mechparams --cov-report=html
```

Run specific test modules:
```bash
pytest tests/test_graph.py              # Graph structure tests
pytest tests/test_algorithm.py          # Algorithm tests
pytest tests/test_executor_dynamic_programming.py  # Dynamic programming tests
pytest tests/test_integration.py        # Integration tests
```

**Current test status**: 
- Integration tests: ✓ Passing
- Dynamic programming/caching tests: ✓ Passing  
- Graph and algorithm tests: ✓ Passing
- Dispatcher tests: ✓ Passing
- Total: 135+ tests

## Current Status (v0.3.0)

### ✅ Completed Features

- [x] Layer parameter calculations (density, E, ν, G) with 4+4+2+1 methods
- [x] Slab parameter calculations (A11, B11, D11, A55) using classical laminate theory
- [x] Parameterization graph with 32 D11 pathways
- [x] Automatic pathway discovery algorithm with memoization
- [x] Dynamic programming execution engine with layer-level caching
- [x] Copy-on-write optimization for efficient memory usage
- [x] Provenance tracking and computation traces
- [x] SnowPilot CAAML parsing and integration
- [x] Uncertainty propagation throughout all calculations
- [x] Comprehensive test suite (135+ tests)
- [x] D11 comparison analysis across all pathways
- [x] Production-ready examples and documentation
- [x] Performance optimization (40-50% cache hit rates)

### 🚧 In Development

- [ ] Additional elastic modulus methods
- [ ] Temperature-dependent properties
- [ ] 3D microstructure integration
- [ ] API documentation (ReadTheDocs)
- [ ] PyPI package publication

### 📊 Dataset Status

- **SnowPilot dataset**: 50,278 CAAML files parsed successfully
- **ECTP slabs**: ~14,776 slabs from ~12,347 pits (24.6% ECTP rate)
- **D11 pathways**: 32 unique pathways (4 density × 4 E × 2 ν)
- **Analysis**: Comprehensive pathway comparison in `compare_D11_across_pathways_v3.ipynb`

## Troubleshooting

### Python Cache Issues

If you experience issues with stale code being loaded, clear Python's bytecode cache:

```bash
# Run the cache clearing script
./clear_cache.sh
# or
python clear_cache.py
```

**Manual clearing:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

After clearing cache, restart your Jupyter kernel.

### SSL Certificate Issues (macOS)

If you encounter SSL certificate errors:

```bash
# Install certificates (Recommended)
/Applications/Python\ 3.*/Install\ Certificates.command
```

### Common Issues

- **"Unknown method" errors**: Clear the cache and restart the kernel
- **Changes not taking effect**: Ensure `%autoreload 2` is enabled in notebooks and clear cache
- **Import errors after updates**: Reinstall in editable mode: `pip install -e .`
- **Package not found**: Make sure virtual environment is activated (`(venv)` in prompt)
- **ModuleNotFoundError**: Verify installation with `python -c "import snowpyt_mechparams"`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

For contributors who want to develop and test the package:

```bash
# Clone the repository
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Adding New Methods

To add a new calculation method:

1. **Implement the method** in the appropriate module (`layer_parameters/` or `slab_parameters/`)
2. **Add to the graph**: Update `src/snowpyt_mechparams/graph/definitions.py`
   ```python
   build_graph.method_edge(merge_node, parameter_node, "your_method_name")
   ```
3. **Register in dispatcher**: Update `execution/dispatcher.py`
4. **Write tests**: Add tests to `tests/`
5. **Document**: Add method citation to graph documentation

The execution engine will automatically discover and use your new method!

See `src/snowpyt_mechparams/graph/README.md` for detailed instructions.

## Citation

If you use SnowPyt-MechParams in your research, please cite:

```bibtex
@software{snowpyt_mechparams,
  author = {Connelly, Mary and Verplanck, Samuel and {SnowPyt-MechParams Contributors}},
  title = {SnowPyt-MechParams: A collaborative Python library for snow mechanical parameter estimation},
  url = {https://github.com/your-username/snowpyt-mechparams},
  version = {0.3.0},
  year = {2025}
}
```

### Method Citations

When using specific methods, please also cite the relevant publications:

**Density Methods:**
- Geldsetzer et al. (2009) - Hand hardness correlations
- Kim & Jamieson (2010) - Tables 2 and 5 methods

**Elastic Modulus Methods:**
- Bergfeld et al. (2023) - Temporal evolution of crack propagation
- Köchle & Schneebeli (2014) - Microstructure-based calculations
- Wautier et al. (2015) - Numerical homogenization
- Schöttner et al. (2024) - Finite element modeling

**Poisson's Ratio Methods:**
- Köchle & Schneebeli (2014) - Grain form correlations
- Srivastava et al. (2016) - Temperature gradient metamorphism

**Shear Modulus:**
- Wautier et al. (2015) - Numerical homogenization

**Slab Parameters:**
- Weißgraeber & Rosendahl (2023) - Classical laminate theory for layered snow slabs

Full citations available in `src/snowpyt_mechparams/graph/definitions.py`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

This collaborative project is made possible by contributions from multiple academic researchers and institutions:

- **Lead Developers**: Mary Connelly, Samuel Verplanck - Montana State University
- **Academic Contributors**: [Contributors will be listed here as they join the project]
- **Institutional Affiliations**: Montana State University

We welcome new academic collaborators! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

- SnowPilot dataset provided by the avalanche forecasting community
- Algorithm development supported by Montana State University
- Built on the `uncertainties` package for uncertainty propagation

## Related Projects

- [SnowPylot](https://github.com/connellymk/snowpylot) - Python library for parsing and analyzing SnowPilot data

## Contact

- **Project Leads**: Mary Connelly and Samuel Verplanck, Montana State University
- **Email**: connellymarykate@gmail.com, samuelverplanck@montana.edu
- **Academic Collaboration Inquiries**: Please reach out to the project leads directly
- **Issues**: [GitHub Issues](https://github.com/your-username/snowpyt-mechparams/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/snowpyt-mechparams/discussions)

For academic researchers interested in collaborating, please see our [collaboration guidelines](CONTRIBUTING.md#scientific-contributions) and feel free to reach out through GitHub Discussions.

---

**Version**: 0.3.0 | **Last Updated**: February 2026 | **Python**: 3.8+ | **License**: MIT
