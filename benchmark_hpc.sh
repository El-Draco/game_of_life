#!/bin/bash
#SBATCH --job-name=life_bench
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=8
#SBATCH --time=01:00:00
#SBATCH --partition=prod
#SBATCH --account=teach0026

# HPC Performance Benchmarking
# Measures performance on large grids with many processes

module purge
module load python/3.10.5
module load openmpi/4.1.4

# Setup Python environment (adjust if using uv on HPC)
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install numpy mpi4py matplotlib scipy pillow
else
    source .venv/bin/activate
fi

SCRIPT="life_mpi.py"
PATTERN="glider_gun"
STEPS=500
GRID_SIZE=16384  # 16K x 16K
SEED=42

mkdir -p logs

echo "======================================"
echo "HPC Performance Benchmark"
echo "======================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Nodes: $SLURM_JOB_NUM_NODES"
echo "Grid: ${GRID_SIZE}x${GRID_SIZE}"
echo "Steps: ${STEPS}"
echo ""

rm -rf bench_hpc_* benchmark_hpc_results.txt

echo "# ranks,time_seconds,speedup,efficiency" > benchmark_hpc_results.txt

BASELINE_TIME=0

# Test with different process counts
for NP in 1 2 4 8 16 32; do
    if [ ${NP} -gt $((SLURM_JOB_NUM_NODES * SLURM_NTASKS_PER_NODE)) ]; then
        echo "Skipping np=${NP} (exceeds allocated resources)"
        continue
    fi
    
    OUTPUT_DIR="bench_hpc_np${NP}"
    
    echo "Running with np=${NP}..."
    
    mpirun -np ${NP} python ${SCRIPT} \
        --nx ${GRID_SIZE} --ny ${GRID_SIZE} \
        --steps ${STEPS} \
        --pattern ${PATTERN} \
        --seed ${SEED} \
        --output-dir ${OUTPUT_DIR} \
        --save-interval 0 \
        --benchmark > bench_hpc_np${NP}.log 2>&1
    
    TIME=$(grep "^BENCHMARK: ranks=" bench_hpc_np${NP}.log | sed 's/.*time=\([0-9.]*\).*/\1/')
    
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
    echo ""
    
    echo "${NP},${TIME},${SPEEDUP},${EFFICIENCY}" >> benchmark_hpc_results.txt
    
    # Clean up large snapshot directories
    rm -rf ${OUTPUT_DIR}
done

echo "======================================"
echo "Benchmark Results:"
echo "======================================"
cat benchmark_hpc_results.txt

echo ""
echo "✓ HPC Benchmark complete!"
echo "Results saved to: benchmark_hpc_results.txt"

