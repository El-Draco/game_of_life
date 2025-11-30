#!/bin/bash
#SBATCH --job-name=life_mpi
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=8
#SBATCH --time=01:00:00
#SBATCH --partition=prod
#SBATCH --account=hpc_project_code

# Conway's Game of Life - MPI Parallel Simulation
# Usage: sbatch submit.sbatch

# Create directories
mkdir -p logs snapshots

# Load modules (adjust for your HPC)
module purge
module load python/3.10.5
module load openmpi/4.1.4

# Setup Python environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install numpy mpi4py matplotlib scipy pillow
else
    source .venv/bin/activate
fi

# Run simulation
# Adjust parameters as needed for your grid size
mpirun -np $SLURM_NTASKS python life_mpi.py \
    --nx 16384 \
    --ny 16384 \
    --steps 2000 \
    --pattern glider_gun \
    --seed 42 \
    --output-dir snapshots \
    --save-interval 100 \
    --benchmark

echo ""
echo "Job completed! Output saved to: snapshots/"
echo "Create visualizations with:"
echo "  python visualize.py --input-dir snapshots --output animation.gif"
