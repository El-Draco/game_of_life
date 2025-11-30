#!/bin/bash
# Local performance benchmarking (macOS with uv)
# Measures speedup across different process counts

set -e

SCRIPT="life_mpi.py"
PATTERN="glider_gun"
STEPS=200
GRID_SIZE=512
SEED=42

echo "======================================"
echo "Conway's Game of Life - Performance Benchmark"
echo "======================================"
echo "Grid: ${GRID_SIZE}x${GRID_SIZE}"
echo "Steps: ${STEPS}"
echo "Pattern: ${PATTERN}"
echo ""

# Create output directory
OUTPUT_DIR="benchmark_local"
rm -rf ${OUTPUT_DIR}
mkdir -p ${OUTPUT_DIR}

echo "# ranks,time_seconds,speedup,efficiency" > ${OUTPUT_DIR}/results.txt

BASELINE_TIME=0

for NP in 1 2 4 8; do
    SNAP_DIR="${OUTPUT_DIR}/snapshots_np${NP}"
    
    echo "Benchmarking with np=${NP}..."
    
    # Run 3 times and take median
    TIMES=()
    for RUN in 1 2 3; do
        echo "  Run ${RUN}/3..."
        uv run mpirun -np ${NP} python ${SCRIPT} \
            --nx ${GRID_SIZE} --ny ${GRID_SIZE} \
            --steps ${STEPS} \
            --pattern ${PATTERN} \
            --seed ${SEED} \
            --output-dir ${SNAP_DIR} \
            --save-interval 0 \
            --benchmark > ${OUTPUT_DIR}/bench_np${NP}_run${RUN}.log 2>&1
        
        TIME=$(grep "^BENCHMARK: ranks=" ${OUTPUT_DIR}/bench_np${NP}_run${RUN}.log | sed 's/.*time=\([0-9.]*\).*/\1/')
        TIMES+=($TIME)
    done
    
    # Get median time (middle value)
    MEDIAN_TIME=$(printf '%s\n' "${TIMES[@]}" | sort -n | sed -n '2p')
    
    if [ ${NP} -eq 1 ]; then
        BASELINE_TIME=${MEDIAN_TIME}
        SPEEDUP=1.00
        EFFICIENCY=100.0
    else
        SPEEDUP=$(echo "scale=2; ${BASELINE_TIME} / ${MEDIAN_TIME}" | bc)
        EFFICIENCY=$(echo "scale=1; (${SPEEDUP} / ${NP}) * 100" | bc)
    fi
    
    echo "  Median time: ${MEDIAN_TIME}s"
    echo "  Speedup: ${SPEEDUP}x"
    echo "  Efficiency: ${EFFICIENCY}%"
    echo ""
    
    echo "${NP},${MEDIAN_TIME},${SPEEDUP},${EFFICIENCY}" >> ${OUTPUT_DIR}/results.txt
    
    # Clean up snapshot directories (keep logs)
    rm -rf ${SNAP_DIR}
done

echo "======================================"
echo "Benchmark Results:"
echo "======================================"
cat ${OUTPUT_DIR}/results.txt

# Create plot if matplotlib is available
cat > ${OUTPUT_DIR}/plot_results.py << 'EOF'
import sys
import csv

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    print("Warning: matplotlib not available, skipping plot")
    sys.exit(0)

data = {'ranks': [], 'time': [], 'speedup': [], 'efficiency': []}

with open('results.txt', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data['ranks'].append(int(row['# ranks']))
        data['time'].append(float(row['time_seconds']))
        data['speedup'].append(float(row['speedup']))
        data['efficiency'].append(float(row['efficiency']))

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Plot 1: Execution Time
axes[0].plot(data['ranks'], data['time'], 'o-', linewidth=2, markersize=8)
axes[0].set_xlabel('Number of Processes', fontweight='bold')
axes[0].set_ylabel('Time (seconds)', fontweight='bold')
axes[0].set_title('Execution Time', fontweight='bold')
axes[0].grid(True, alpha=0.3)

# Plot 2: Speedup
axes[1].plot(data['ranks'], data['speedup'], 'o-', linewidth=2, markersize=8, label='Actual')
axes[1].plot(data['ranks'], data['ranks'], '--', linewidth=2, alpha=0.5, label='Ideal')
axes[1].set_xlabel('Number of Processes', fontweight='bold')
axes[1].set_ylabel('Speedup', fontweight='bold')
axes[1].set_title('Speedup vs Processes', fontweight='bold')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# Plot 3: Efficiency
axes[2].plot(data['ranks'], data['efficiency'], 'o-', linewidth=2, markersize=8)
axes[2].axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
axes[2].set_xlabel('Number of Processes', fontweight='bold')
axes[2].set_ylabel('Parallel Efficiency (%)', fontweight='bold')
axes[2].set_title('Parallel Efficiency', fontweight='bold')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results_plot.png', dpi=150, bbox_inches='tight')
print("\n✓ Saved plot: results_plot.png")
EOF

cd ${OUTPUT_DIR}
uv run python plot_results.py
cd ..

echo ""
echo "✓ Benchmark complete!"
echo "  📁 All results in: ${OUTPUT_DIR}/"
echo "     - results.txt         (timing data)"
echo "     - results_plot.png    (speedup graphs)"
echo "     - bench_np*.log       (detailed logs)"

