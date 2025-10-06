# SnowPyt-MechParams

[![PyPI version](https://badge.fury.io/py/snowpyt-mechparams.svg)](https://badge.fury.io/py/snowpyt-mechparams)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/your-username/snowpyt-mechparams/workflows/Tests/badge.svg)](https://github.com/your-username/snowpyt-mechparams/actions)

A collaborative Python library for estimating mechanical parameters from snow pit measurements, developed by multiple academic researchers in the snow science community. This package provides scientifically-validated methods to calculate mechanical parameters and avalanche stability metrics from standard snowpit observations.

## Features

## Installation

### Virtual Environment Setup (Recommended)

We strongly recommend using a virtual environment to manage dependencies and avoid conflicts with other Python projects.

#### Create and Activate Virtual Environment
```bash
# Clone the repository
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams

# Create virtual environment
python3 -m venv MechParams

# Activate virtual environment
# On macOS/Linux:
source MechParams/bin/activate
# On Windows:
# MechParams\Scripts\activate

# Install the package in editable mode
pip install -e .
```

#### Deactivate Virtual Environment
```bash
deactivate
```

### From PyPI (recommended for production)
```bash
pip install snowpyt-mechparams
```

### From Source (without virtual environment)
```bash
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams
python3 -m venv MechParams
source MechParams/bin/activate  # On Windows: MechParams\Scripts\activate
pip install -e .[dev]
```

## Quick Start


## Core Modules

## Examples

Comprehensive examples are available in the `examples/` directory:


## Documentation

Full API documentation is available at: [https://snowpyt-mechparams.readthedocs.io/](https://snowpyt-mechparams.readthedocs.io/)

For local documentation:
```bash
cd docs
make html
```

## Testing

Run the test suite:
```bash
pytest
```

With coverage report:
```bash
pytest --cov=snowpyt_mechparams --cov-report=html
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams

# Create and activate virtual environment
python3 -m venv MechParams
source MechParams/bin/activate  # On Windows: MechParams\Scripts\activate

# Install development dependencies
pip install -e .[dev]
pre-commit install
```

### Running Tests
```bash
pytest                           # Run all tests
pytest tests/test_density.py     # Run specific module tests
pytest -m "not slow"            # Skip slow tests
```

## Citation

If you use SnowPyt-MechParams in your research, please cite:

```bibtex
@software{snowpyt_mechparams,
  author = {Connelly, Mary and {SnowPyt-MechParams Contributors}},
  title = {SnowPyt-MechParams: A collaborative Python library for snow mechanical parameter estimation},
  url = {https://github.com/your-username/snowpyt-mechparams},
  version = {0.1.0},
  year = {2025}
}
```

For specific methods or contributions from individual researchers, please also cite the relevant scientific publications listed in the method documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

This collaborative project is made possible by contributions from multiple academic researchers and institutions in the snow science community:

- **Lead Developer**: Mary Connelly
- **Academic Contributors**: [Contributors will be listed here as they join the project]
- **Institutional Affiliations**: [Research institutions will be listed here]

We welcome new academic collaborators! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on joining this collaborative effort.

## Acknowledgments


## Related Projects

- [SnowPylot](https://github.com/connellymk/snowpylot) 

## Contact

- **Project Lead**: Mary Connelly and Samual Verplanck, Montana State University
- **Email**: connellymarykate@gmail.com, samuelverplanck@montana.edu
- **Academic Collaboration Inquiries**: Please reach out to the project leads directly
- **Issues**: [GitHub Issues](https://github.com/your-username/snowpyt-mechparams/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/snowpyt-mechparams/discussions)

For academic researchers interested in collaborating, please see our [collaboration guidelines](CONTRIBUTING.md#scientific-contributions) and feel free to reach out through GitHub Discussions.
