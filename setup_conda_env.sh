#!/bin/bash
# Setup conda environment for Game of Life on Almesbar
# Run this ONCE on Almesbar after uploading files

module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

# Create conda environment in local directory
conda env create -f environment.yml --prefix ./env

echo ""
echo "✓ Conda environment created in ./env/"
echo ""
echo "To activate: conda activate ./env"
echo "To deactivate: conda deactivate"

