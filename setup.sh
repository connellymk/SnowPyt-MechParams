#!/bin/bash

# SnowPyt-MechParams Setup Script
# This script helps set up the virtual environment and install dependencies

set -e  # Exit on error

echo "=========================================="
echo "SnowPyt-MechParams Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"
echo ""

# Check if virtual environment already exists
if [ -d "venv" ]; then
    echo "Virtual environment 'venv' already exists."
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Using existing virtual environment."
        SKIP_VENV_CREATE=true
    fi
fi

# Create virtual environment if needed
if [ "$SKIP_VENV_CREATE" != "true" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel --quiet || {
    echo "Warning: Could not upgrade pip. This might be due to SSL certificate issues."
    echo "You may need to install certificates or use --trusted-host flags."
}

# Install the package
echo ""
echo "Installing SnowPyt-MechParams..."
if pip install -e .; then
    echo "✓ Package installed successfully"
else
    echo ""
    echo "⚠ Installation failed. This might be due to:"
    echo "  1. SSL certificate issues (see README.md troubleshooting section)"
    echo "  2. Missing dependencies"
    echo ""
    echo "Try running manually with:"
    echo "  source venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Verify installation
echo ""
echo "Verifying installation..."
if python -c "import snowpyt_mechparams; print('✓ Import successful')" 2>/dev/null; then
    echo ""
    echo "=========================================="
    echo "Setup Complete! ✓"
    echo "=========================================="
    echo ""
    echo "To activate the virtual environment in the future:"
    echo "  source venv/bin/activate"
    echo ""
    echo "To deactivate:"
    echo "  deactivate"
    echo ""
else
    echo "⚠ Warning: Could not verify installation. Please check manually."
fi
