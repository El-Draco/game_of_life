#!/bin/bash
#SBATCH --nodes=2                        # 2 nodes
#SBATCH --ntasks-per-node=52             # 52 cores per node = 104 total
#SBATCH --exclusive                      # Exclusive node access
#SBATCH --job-name=life_backup           # Job name
#SBATCH --time=01:00:00                  # 1 hour (finishes in ~30 min)
#SBATCH --partition=prod                 # Partition
#SBATCH --account=teach0026              # Project account
#SBATCH --output=life_backup.%j.out      # Standard output
#SBATCH --error=life_backup.%j.err       # Error output

# Conway's Game of Life - BACKUP Run (Fast & Safe)
# 2 nodes, 104 cores, 4096×4096 grid, 2000 steps
# Expected runtime: ~30 minutes
# Usage: sbatch backup.sbatch

echo "════════════════════════════════════════════════════════"
echo "  Conway's Game of Life - BACKUP Run (Fast & Safe)"
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
# PRODUCTION RUN - 4K×4K Grid, 2000 Steps (BACKUP)
# ═══════════════════════════════════════════════════════════

echo "Starting backup simulation..."
echo ""

PROD_NX=4096
PROD_NY=4096
PROD_STEPS=2000
PROD_PATTERN="glider_gun"
PROD_SEED=42
PROD_INTERVAL=100

echo "Backup configuration:"
echo "  Grid: ${PROD_NX}×${PROD_NY} (16.7M cells)"
echo "  Steps: ${PROD_STEPS}"
echo "  Pattern: ${PROD_PATTERN}"
echo "  Save interval: ${PROD_INTERVAL}"
echo "  MPI processes: $SLURM_NTASKS (2 nodes × 52 cores)"
echo "  Expected time: ~30 minutes"
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
echo "✓ Backup simulation complete!"
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
echo "  📝 Logs:      life_backup.$SLURM_JOB_ID.out/err"
echo ""
echo "Snapshot count: $(ls -1 snapshots/*.npz 2>/dev/null | wc -l)"
echo "Grid size: ${PROD_NX}×${PROD_NY}"
echo "Total steps: ${PROD_STEPS}"
echo "MPI processes: $SLURM_NTASKS"
echo ""
echo "Next steps (run locally after downloading snapshots):"
echo ""
echo "1. Download snapshots:"
echo "   scp -r username@almesbar:~/dist_sys/snapshots ."
echo ""
echo "2. Create animation:"
echo "   python visualize.py --input-dir snapshots --output backup_animation.gif"
echo ""
echo "3. Create heatmap visualization:"
echo "   python visualize.py --input-dir snapshots --output backup_heatmap.gif \\"
echo "       --show-ranks --ranks $SLURM_NTASKS --fps 5"
echo ""
echo "════════════════════════════════════════════════════════"

