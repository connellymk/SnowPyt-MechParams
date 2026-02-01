# SnowPyt-MechParams

[![PyPI version](https://badge.fury.io/py/snowpyt-mechparams.svg)](https://badge.fury.io/py/snowpyt-mechparams)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/your-username/snowpyt-mechparams/workflows/Tests/badge.svg)](https://github.com/your-username/snowpyt-mechparams/actions)

A collaborative Python library for estimating mechanical parameters from snow pit measurements, developed by multiple academic researchers in the snow science community. This package provides scientifically-validated methods to calculate mechanical parameters and avalanche stability metrics from standard snowpit observations.

## Features

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

Follow these steps for manual setup:

#### Step 1: Clone the Repository

If you haven't already cloned the repository:
```bash
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment (named 'venv')
python3 -m venv venv

# Alternative: You can name it 'MechParams' if you prefer
# python3 -m venv MechParams
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

### Installation Methods

#### From PyPI (Production Use)

If you just want to use the package without development:
```bash
pip install snowpyt-mechparams
```

#### From Source (Without Virtual Environment)

**Not recommended**, but if you prefer:
```bash
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams
pip install -e .
```

### Using with Jupyter Notebooks

To use this package in Jupyter notebooks with your virtual environment:

1. **Activate your virtual environment:**
   ```bash
   source venv/bin/activate  # or MechParams/bin/activate
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

## Troubleshooting

### Python Cache Issues

If you experience issues with stale code being loaded (e.g., code changes not taking effect), Python's bytecode cache may be the culprit. We provide utilities to clear all cache files:

**Option 1: Run the cache clearing script**
```bash
# From the project root
./clear_cache.sh
# or
python clear_cache.py
```

**Option 2: Manual clearing**
```bash
# Remove all __pycache__ directories and .pyc files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

**Option 3: Prevent cache generation (recommended for development)**

Add this to the first cell of your Jupyter notebooks:
```python
import sys
sys.dont_write_bytecode = True
```

**After clearing cache:**
1. Restart your Jupyter kernel (Kernel → Restart Kernel)
2. Run all cells from the beginning

### SSL Certificate Issues (macOS)

If you encounter SSL certificate errors when installing packages (e.g., `SSLError(SSLCertVerificationError)`):

**Option 1: Install certificates (Recommended)**
```bash
# Run this in your terminal (outside the virtual environment)
/Applications/Python\ 3.*/Install\ Certificates.command
```

**Option 2: Use pip with trusted hosts (Temporary workaround)**
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .
```

**Option 3: Update certificates manually**
```bash
# Install certifi and update certificates
pip install --upgrade certifi
/Applications/Python\ 3.*/Install\ Certificates.command
```

### Common Issues

- **"Unknown method" errors**: Clear the cache and restart the kernel
- **Changes not taking effect**: Ensure `%autoreload 2` is enabled in notebooks and clear the cache
- **Import errors after updates**: Reinstall the package in editable mode: `pip install -e .`
- **SSL certificate errors**: See "SSL Certificate Issues" section above
- **Package not found**: Make sure your virtual environment is activated (you should see `(venv)` in your prompt)
- **Permission errors**: Avoid using `sudo` with pip when in a virtual environment

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

For contributors who want to develop and test the package:

```bash
# Clone the repository (if not already done)
git clone https://github.com/your-username/snowpyt-mechparams.git
cd snowpyt-mechparams

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install development dependencies (includes pytest, black, flake8, etc.)
pip install -e .[dev]

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

**Note:** The `[dev]` extra includes:
- Testing tools: `pytest`, `pytest-cov`
- Code formatting: `black`, `flake8`
- Type checking: `mypy`
- Documentation: `sphinx`, `sphinx-rtd-theme`
- Jupyter: `jupyter`

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
