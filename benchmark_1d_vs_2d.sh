#!/bin/bash
# Compare 1D vs 2D decomposition performance
# 256x256 grid, 1000 steps

set -e

GRID_SIZE=256
STEPS=1000
PATTERN="glider_gun"
SEED=42

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "============================================================"
echo "  1-D vs 2-D Decomposition Benchmark"
echo "============================================================"
echo "Grid: ${GRID_SIZE}×${GRID_SIZE}"
echo "Steps: ${STEPS}"
echo "Pattern: ${PATTERN}"
echo ""

OUTPUT_DIR="benchmark_1d_vs_2d"
rm -rf ${OUTPUT_DIR}
mkdir -p ${OUTPUT_DIR}

echo "# decomp,ranks,time_seconds,speedup,efficiency,checksum" > ${OUTPUT_DIR}/results.txt

# Baseline (1D, np=1)
echo "Running baseline (1D, np=1)..."
mpirun -np 1 python life_mpi.py \
    --nx ${GRID_SIZE} --ny ${GRID_SIZE} \
    --steps ${STEPS} --pattern ${PATTERN} --seed ${SEED} \
    --save-interval 0 --benchmark > ${OUTPUT_DIR}/1d_np1.log 2>&1

BASELINE=$(grep "^BENCHMARK: ranks=" ${OUTPUT_DIR}/1d_np1.log | sed 's/.*time=\([0-9.]*\).*/\1/')
CHECKSUM_1D=$(grep "^BENCHMARK: checksum=" ${OUTPUT_DIR}/1d_np1.log | sed 's/.*checksum=\([0-9]*\).*/\1/')

echo "  Baseline: ${BASELINE}s, checksum=${CHECKSUM_1D}"
echo "1d,1,${BASELINE},1.00,100.0,${CHECKSUM_1D}" >> ${OUTPUT_DIR}/results.txt
echo ""

# Test 1D
for NP in 2 4 8; do
    echo "Testing 1D with np=${NP}..."
    mpirun -np ${NP} python life_mpi.py \
        --nx ${GRID_SIZE} --ny ${GRID_SIZE} \
        --steps ${STEPS} --pattern ${PATTERN} --seed ${SEED} \
        --save-interval 0 --benchmark > ${OUTPUT_DIR}/1d_np${NP}.log 2>&1
    
    TIME=$(grep "^BENCHMARK: ranks=" ${OUTPUT_DIR}/1d_np${NP}.log | sed 's/.*time=\([0-9.]*\).*/\1/')
    CHECKSUM=$(grep "^BENCHMARK: checksum=" ${OUTPUT_DIR}/1d_np${NP}.log | sed 's/.*checksum=\([0-9]*\).*/\1/')
    SPEEDUP=$(echo "scale=2; ${BASELINE} / ${TIME}" | bc)
    EFFICIENCY=$(echo "scale=1; (${SPEEDUP} / ${NP}) * 100" | bc)
    
    echo "  Time: ${TIME}s, Speedup: ${SPEEDUP}×, Efficiency: ${EFFICIENCY}%, checksum=${CHECKSUM}"
    echo "1d,${NP},${TIME},${SPEEDUP},${EFFICIENCY},${CHECKSUM}" >> ${OUTPUT_DIR}/results.txt
    echo ""
done

# Test 2D (perfect square process counts)
for NP in 4 9; do
    echo "Testing 2D with np=${NP}..."
    mpirun -np ${NP} python life_mpi_2d.py \
        --nx ${GRID_SIZE} --ny ${GRID_SIZE} \
        --steps ${STEPS} --pattern ${PATTERN} --seed ${SEED} \
        --save-interval 0 --benchmark > ${OUTPUT_DIR}/2d_np${NP}.log 2>&1
    
    TIME=$(grep "^BENCHMARK: ranks=" ${OUTPUT_DIR}/2d_np${NP}.log | sed 's/.*time=\([0-9.]*\).*/\1/')
    CHECKSUM=$(grep "^BENCHMARK: checksum=" ${OUTPUT_DIR}/2d_np${NP}.log | sed 's/.*checksum=\([0-9]*\).*/\1/')
    SPEEDUP=$(echo "scale=2; ${BASELINE} / ${TIME}" | bc)
    EFFICIENCY=$(echo "scale=1; (${SPEEDUP} / ${NP}) * 100" | bc)
    
    echo "  Time: ${TIME}s, Speedup: ${SPEEDUP}×, Efficiency: ${EFFICIENCY}%, checksum=${CHECKSUM}"
    echo "2d,${NP},${TIME},${SPEEDUP},${EFFICIENCY},${CHECKSUM}" >> ${OUTPUT_DIR}/results.txt
    echo ""
done

echo "============================================================"
echo "  Results Summary"
echo "============================================================"
cat ${OUTPUT_DIR}/results.txt

# Create comparison plot
cat > ${OUTPUT_DIR}/plot_comparison.py << 'PLOT_EOF'
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

data_1d = {'ranks': [], 'time': [], 'speedup': [], 'efficiency': []}
data_2d = {'ranks': [], 'time': [], 'speedup': [], 'efficiency': []}

with open('results.txt', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        decomp = row['# decomp']
        ranks = int(row['ranks'])
        time = float(row['time_seconds'])
        speedup = float(row['speedup'])
        efficiency = float(row['efficiency'])
        
        if decomp == '1d':
            data_1d['ranks'].append(ranks)
            data_1d['time'].append(time)
            data_1d['speedup'].append(speedup)
            data_1d['efficiency'].append(efficiency)
        else:
            data_2d['ranks'].append(ranks)
            data_2d['time'].append(time)
            data_2d['speedup'].append(speedup)
            data_2d['efficiency'].append(efficiency)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Plot 1: Execution Time
axes[0].plot(data_1d['ranks'], data_1d['time'], 'o-', linewidth=2, markersize=8, 
             label='1-D Row', color='blue')
axes[0].plot(data_2d['ranks'], data_2d['time'], 's-', linewidth=2, markersize=8, 
             label='2-D Grid', color='red')
axes[0].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[0].set_ylabel('Time (seconds)', fontweight='bold', fontsize=11)
axes[0].set_title('Execution Time Comparison', fontweight='bold', fontsize=13)
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)

# Plot 2: Speedup
axes[1].plot(data_1d['ranks'], data_1d['speedup'], 'o-', linewidth=2, markersize=8, 
             label='1-D Row', color='blue')
axes[1].plot(data_2d['ranks'], data_2d['speedup'], 's-', linewidth=2, markersize=8, 
             label='2-D Grid', color='red')
ideal_ranks = np.array(sorted(set(data_1d['ranks'] + data_2d['ranks'])))
axes[1].plot(ideal_ranks, ideal_ranks, '--', linewidth=2, alpha=0.5, 
             label='Ideal', color='gray')
axes[1].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[1].set_ylabel('Speedup', fontweight='bold', fontsize=11)
axes[1].set_title('Speedup Comparison', fontweight='bold', fontsize=13)
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

# Plot 3: Efficiency
axes[2].plot(data_1d['ranks'], data_1d['efficiency'], 'o-', linewidth=2, markersize=8, 
             label='1-D Row', color='blue')
axes[2].plot(data_2d['ranks'], data_2d['efficiency'], 's-', linewidth=2, markersize=8, 
             label='2-D Grid', color='red')
axes[2].axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='100%')
axes[2].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[2].set_ylabel('Parallel Efficiency (%)', fontweight='bold', fontsize=11)
axes[2].set_title('Efficiency Comparison', fontweight='bold', fontsize=13)
axes[2].legend(fontsize=11)
axes[2].grid(True, alpha=0.3)
axes[2].set_ylim([70, 105])

plt.tight_layout()
plt.savefig('1d_vs_2d_comparison.png', dpi=150, bbox_inches='tight')
print("\n✓ Saved: 1d_vs_2d_comparison.png")
PLOT_EOF

cd ${OUTPUT_DIR}
python plot_comparison.py
cd ..

echo ""
echo "============================================================"
echo "  ✓ Benchmark Complete!"
echo "============================================================"
echo "Results: ${OUTPUT_DIR}/results.txt"
echo "Plot: ${OUTPUT_DIR}/1d_vs_2d_comparison.png"
echo ""

