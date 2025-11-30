#!/bin/bash
#SBATCH --job-name=life_full
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=8
#SBATCH --time=04:00:00
#SBATCH --partition=prod
#SBATCH --account=teach0026

# Conway's Game of Life - Complete Run
# Runs BOTH benchmark and production simulation in one job
# Usage: sbatch submit_all.sbatch

echo "════════════════════════════════════════════════════════"
echo "  Conway's Game of Life - Complete HPC Run"
echo "════════════════════════════════════════════════════════"
echo "Job ID: $SLURM_JOB_ID"
echo "Nodes: $SLURM_JOB_NUM_NODES"
echo "Total tasks: $SLURM_NTASKS"
echo "Start time: $(date)"
echo ""

# Create directories
mkdir -p logs snapshots benchmark_data

# Load modules (Almesbar standard modules)
module purge
module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

# Activate conda environment
echo "Activating conda environment..."
conda deactivate
conda activate ./env
echo "✓ Environment ready"
echo ""

# ═══════════════════════════════════════════════════════════
# PART 1: BENCHMARK - Performance Testing
# ═══════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════"
echo "  PART 1/2: Running Performance Benchmark"
echo "════════════════════════════════════════════════════════"
echo ""

BENCH_GRID=4096
BENCH_STEPS=500
BENCH_PATTERN="glider_gun"
BENCH_SEED=42

echo "Benchmark configuration:"
echo "  Grid: ${BENCH_GRID}x${BENCH_GRID}"
echo "  Steps: ${BENCH_STEPS}"
echo "  Pattern: ${BENCH_PATTERN}"
echo ""

# Create results file
echo "# ranks,time_seconds,speedup,efficiency" > benchmark_data/results.txt

BASELINE_TIME=0

# Test different process counts
for NP in 1 2 4 8 16 32; do
    if [ ${NP} -gt $SLURM_NTASKS ]; then
        echo "Skipping np=${NP} (exceeds allocated tasks: $SLURM_NTASKS)"
        continue
    fi
    
    echo "─────────────────────────────────────────"
    echo "Testing with np=${NP}..."
    
    OUTPUT_DIR="benchmark_data/np${NP}"
    
    mpirun -np ${NP} python life_mpi.py \
        --decomp rows \
        --nx ${BENCH_GRID} --ny ${BENCH_GRID} \
        --steps ${BENCH_STEPS} \
        --pattern ${BENCH_PATTERN} \
        --seed ${BENCH_SEED} \
        --output-dir ${OUTPUT_DIR} \
        --save-interval 0 \
        --benchmark > benchmark_data/bench_np${NP}.log 2>&1
    
    TIME=$(grep "^BENCHMARK: ranks=" benchmark_data/bench_np${NP}.log | sed 's/.*time=\([0-9.]*\).*/\1/')
    CHECKSUM=$(grep "^BENCHMARK: checksum=" benchmark_data/bench_np${NP}.log | sed 's/.*checksum=\([0-9]*\).*/\1/')
    
    if [ ${NP} -eq 1 ]; then
        BASELINE_TIME=${TIME}
        SPEEDUP=1.00
        EFFICIENCY=100.0
    else
        SPEEDUP=$(echo "scale=2; ${BASELINE_TIME} / ${TIME}" | bc)
        EFFICIENCY=$(echo "scale=1; (${SPEEDUP} / ${NP}) * 100" | bc)
    fi
    
    echo "  Time: ${TIME}s"
    echo "  Speedup: ${SPEEDUP}x"
    echo "  Efficiency: ${EFFICIENCY}%"
    echo "  Checksum: ${CHECKSUM}"
    
    echo "${NP},${TIME},${SPEEDUP},${EFFICIENCY}" >> benchmark_data/results.txt
    
    # Clean up benchmark output (keep logs, remove snapshots)
    rm -rf ${OUTPUT_DIR}
done

echo ""
echo "✓ Benchmark complete!"
echo ""
echo "Benchmark Results Summary:"
echo "─────────────────────────────────────────"
cat benchmark_data/results.txt
echo "─────────────────────────────────────────"
echo ""

# ═══════════════════════════════════════════════════════════
# PART 2: PRODUCTION RUN - Generate Snapshots for Visualization
# ═══════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════"
echo "  PART 2/2: Production Simulation with Snapshots"
echo "════════════════════════════════════════════════════════"
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
mpirun python life_mpi.py \
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
echo "  📊 Benchmark results: benchmark_data/results.txt"
echo "  📊 Benchmark logs:    benchmark_data/bench_np*.log"
echo "  💾 Snapshots:         snapshots/step_*.npz"
echo ""
echo "Next steps (run on login node or locally):"
echo ""
echo "1. Download benchmark results:"
echo "   scp user@hpc:~/dist_sys/benchmark_data/results.txt ."
echo ""
echo "2. Create simple animation:"
echo "   python visualize.py --input-dir snapshots --output animation.gif"
echo ""
echo "3. Create heatmap visualization:"
echo "   python visualize.py --input-dir snapshots --output heatmap.gif \\"
echo "       --show-ranks --ranks $SLURM_NTASKS --fps 5"
echo ""
echo "4. Plot benchmark results (optional):"
echo "   python plot_speedup.py benchmark_data/results.txt"
echo ""
echo "════════════════════════════════════════════════════════"

