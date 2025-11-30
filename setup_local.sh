#!/bin/bash
# Setup script for local development on macOS using uv

echo "Setting up local environment for Parallel Game of Life..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew is not installed. Please install it from https://brew.sh"
    exit 1
fi

# Install OpenMPI
echo "Installing OpenMPI..."
brew install openmpi

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Sync dependencies using uv
echo "Installing Python dependencies with uv..."
uv sync

echo ""
echo "Setup complete!"
echo ""
echo "To test locally, run:"
echo "  uv run mpirun -np 2 python -m mpi4py life_mpi.py --nx 256 --ny 256 --steps 50 --pattern glider_gun"
echo ""
echo "Or activate the virtual environment:"
echo "  source .venv/bin/activate"
echo "  mpirun -np 2 python -m mpi4py life_mpi.py --nx 256 --ny 256 --steps 50 --pattern glider_gun"

