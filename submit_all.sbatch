#!/bin/bash
#SBATCH --nodes=1                        # Single node
#SBATCH --ntasks-per-node=32             # 32 cores
#SBATCH --exclusive                      # Exclusive node access
#SBATCH --job-name=life_prod             # Job name
#SBATCH --time=02:00:00                  # 2 hours
#SBATCH --partition=prod                 # Partition
#SBATCH --account=teach0026              # Project account
#SBATCH --output=life_prod.%j.out        # Standard output
#SBATCH --error=life_prod.%j.err         # Error output

# Conway's Game of Life - Production Run
# Runs the main simulation and saves snapshots
# Usage: sbatch submit_all.sbatch

echo "════════════════════════════════════════════════════════"
echo "  Conway's Game of Life - Production Run"
echo "════════════════════════════════════════════════════════"
echo "Job ID: $SLURM_JOB_ID"
echo "Nodes: $SLURM_JOB_NUM_NODES"
echo "Total tasks: $SLURM_NTASKS"
echo "Start time: $(date)"
echo ""

# Create directories
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
echo "Activating conda environment..."
conda deactivate
conda activate ./env
echo "✓ Environment ready"
echo ""

# ═══════════════════════════════════════════════════════════
# PRODUCTION RUN - Generate Snapshots for Visualization
# ═══════════════════════════════════════════════════════════

echo "Starting production simulation..."
echo ""

PROD_NX=16384
PROD_NY=16384
PROD_STEPS=2000
PROD_PATTERN="glider_gun"
PROD_SEED=42
PROD_INTERVAL=100

echo "Production configuration:"
echo "  Grid: ${PROD_NX}x${PROD_NY}"
echo "  Steps: ${PROD_STEPS}"
echo "  Pattern: ${PROD_PATTERN}"
echo "  Save interval: ${PROD_INTERVAL}"
echo "  MPI processes: $SLURM_NTASKS"
echo ""

which mpirun
mpirun -np $SLURM_NTASKS python life_mpi.py \
    --nx ${PROD_NX} \
    --ny ${PROD_NY} \
    --steps ${PROD_STEPS} \
    --decomp rows \
    --pattern ${PROD_PATTERN} \
    --seed ${PROD_SEED} \
    --output-dir snapshots \
    --save-interval ${PROD_INTERVAL} \
    --benchmark

echo ""
echo "✓ Production simulation complete!"
echo ""

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════"
echo "  Job Complete - Summary"
echo "════════════════════════════════════════════════════════"
echo ""
echo "End time: $(date)"
echo ""
echo "Generated files:"
echo "  💾 Snapshots: snapshots/step_*.npz"
echo "  📝 Logs:      life_prod.$SLURM_JOB_ID.out/err"
echo ""
echo "Snapshot count:"
ls -1 snapshots/*.npz | wc -l
echo ""
echo "Next steps (run locally after downloading snapshots):"
echo ""
echo "1. Download snapshots:"
echo "   scp -r user@almesbar:~/dist_sys/snapshots ."
echo ""
echo "2. Create animation:"
echo "   python visualize.py --input-dir snapshots --output animation.gif"
echo ""
echo "3. Create heatmap visualization:"
echo "   python visualize.py --input-dir snapshots --output heatmap.gif \\"
echo "       --show-ranks --ranks $SLURM_NTASKS --fps 5"
echo ""
echo "════════════════════════════════════════════════════════"

