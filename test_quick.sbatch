#!/bin/bash
#SBATCH --nodes=1                        # Number of compute nodes
#SBATCH --ntasks=4                       # Total MPI processes
#SBATCH --ntasks-per-node=4              # Tasks per node
#SBATCH --job-name=life_test             # Job name
#SBATCH --time=00:10:00                  # Time limit (10 minutes for quick test)
#SBATCH --partition=devel                # Use devel queue for quick tests
#SBATCH --account=teach0026              # Project account
#SBATCH --output=life_test.%j.out        # Standard output
#SBATCH --error=life_test.%j.err         # Error output

# Quick test job for Game of Life
# Tests that everything works before running full simulation

# Create output directories
mkdir -p logs test_output

# Load modules (Almesbar standard modules)
module purge
module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

# Create conda environment if it doesn't exist
if [ ! -d "./env" ]; then
    echo "Creating conda environment..."
    conda env create -f environment.yml --prefix ./env
fi

# Activate conda environment
conda deactivate
conda activate ./env

# Verify packages are installed
echo "Python version:"
python --version
echo ""
echo "Checking packages:"
python -c "import numpy; print('numpy:', numpy.__version__)"
python -c "import mpi4py; print('mpi4py:', mpi4py.__version__)"

# Run quick test
which mpirun
mpirun python life_mpi.py \
    --nx 128 \
    --ny 128 \
    --steps 10 \
    --decomp rows \
    --pattern glider \
    --seed 42 \
    --output-dir test_output \
    --save-interval 0 \
    --benchmark

echo ""
echo "✓ Test successful!"
rm -rf test_output
