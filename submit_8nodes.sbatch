#!/bin/bash
#SBATCH --nodes=8                        # 8 nodes
#SBATCH --ntasks-per-node=52             # 52 cores per node = 416 total
#SBATCH --exclusive                      # Exclusive node access
#SBATCH --job-name=life_8nodes           # Job name
#SBATCH --time=02:00:00                  # 2 hours
#SBATCH --partition=prod                 # Partition
#SBATCH --account=teach0026              # Project account
#SBATCH --output=life_8nodes.%j.out      # Standard output
#SBATCH --error=life_8nodes.%j.err       # Error output

# Conway's Game of Life - Production Run (8 nodes, 416 cores)
# For 16384×16384 grid, 2000 steps
# Expected runtime: ~1.5 hours
# Usage: sbatch submit_8nodes.sbatch

echo "════════════════════════════════════════════════════════"
echo "  Conway's Game of Life - 8 Node Production Run"
echo "════════════════════════════════════════════════════════"
echo "Job ID: $SLURM_JOB_ID"
echo "Nodes: $SLURM_JOB_NUM_NODES"
echo "Total tasks: $SLURM_NTASKS"
echo "Cores per node: 52"
echo "Start time: $(date)"
echo ""

# Create directories
mkdir -p logs snapshots_8nodes

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
# PRODUCTION RUN - 16K×16K Grid, 2000 Steps
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
echo "  Grid: ${PROD_NX}×${PROD_NY} (268M cells)"
echo "  Steps: ${PROD_STEPS}"
echo "  Pattern: ${PROD_PATTERN}"
echo "  Save interval: ${PROD_INTERVAL}"
echo "  MPI processes: $SLURM_NTASKS (8 nodes × 52 cores)"
echo "  Expected time: ~1.5 hours"
echo ""

which mpirun
mpirun -np $SLURM_NTASKS python life_mpi.py \
    --nx ${PROD_NX} \
    --ny ${PROD_NY} \
    --steps ${PROD_STEPS} \
    --decomp rows \
    --pattern ${PROD_PATTERN} \
    --seed ${PROD_SEED} \
    --output-dir snapshots_8nodes \
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
echo "  💾 Snapshots: snapshots_8nodes/step_*.npz"
echo "  📝 Logs:      life_8nodes.$SLURM_JOB_ID.out/err"
echo ""
echo "Snapshot count:"
ls -1 snapshots_8nodes/*.npz 2>/dev/null | wc -l
echo ""
echo "Total snapshots created: $(ls -1 snapshots/*.npz 2>/dev/null | wc -l)"
echo "Grid size: ${PROD_NX}×${PROD_NY}"
echo "Total steps: ${PROD_STEPS}"
echo "MPI processes: $SLURM_NTASKS"
echo ""
echo "Next steps (run locally after downloading snapshots):"
echo ""
echo "1. Download snapshots:"
echo "   scp -r username@almesbar:~/dist_sys/snapshots_8nodes ."
echo ""
echo "2. Create animation:"
echo "   python visualize.py --input-dir snapshots_8nodes --output 8node_animation.gif"
echo ""
echo "3. Create heatmap visualization:"
echo "   python visualize.py --input-dir snapshots_8nodes --output 8node_heatmap.gif \\"
echo "       --show-ranks --ranks $SLURM_NTASKS --fps 5"
echo ""
echo "════════════════════════════════════════════════════════"

