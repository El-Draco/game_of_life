#!/bin/bash
#SBATCH --nodes=1                        # Number of compute nodes
#SBATCH --ntasks-per-node=52             # All 52 cores on Almesbar node
#SBATCH --exclusive                      # Exclusive node access (no interference)
#SBATCH --job-name=life_mpi              # Job name
#SBATCH --time=01:00:00                  # Time limit
#SBATCH --partition=prod                 # Partition (queue)
#SBATCH --account=teach0026              # Project account
#SBATCH --output=life_mpi.%j.out         # Standard output
#SBATCH --error=life_mpi.%j.err          # Error output

# Conway's Game of Life - MPI Parallel Simulation
# Usage: sbatch submit.sbatch

# Create output directories
mkdir -p logs snapshots

# Load modules (Almesbar standard modules)
module purge
module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

# Create conda environment if it doesn't exist
if [ ! -d "./env" ]; then
    echo "Creating conda environment (first run)..."
    conda env create -f environment.yml --prefix ./env
fi

# Activate conda environment
conda deactivate
conda activate ./env

# Run simulation (mpirun uses $SLURM_NTASKS automatically)
which mpirun
mpirun python life_mpi.py \
    --nx 16384 \
    --ny 16384 \
    --steps 2000 \
    --decomp rows \
    --pattern glider_gun \
    --seed 42 \
    --output-dir snapshots \
    --save-interval 100 \
    --benchmark

echo ""
echo "Job completed! Output saved to: snapshots/"
