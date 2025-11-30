#!/bin/bash
# Comprehensive benchmark: All patterns, 256x256 grid, 200 steps
# For report generation

set -e

SCRIPT="life_mpi.py"
STEPS=1000
GRID_SIZE=256
SEED=42

PATTERNS=("glider_gun" "r_pentomino" "glider" "random")
PROCESS_COUNTS=(1 2 4 8)

# Adjust for Mac (12 cores max, but we'll be conservative)
if [[ "$OSTYPE" == "darwin"* ]]; then
    MAX_NP=8
else
    MAX_NP=12
fi

echo "═══════════════════════════════════════════════════════"
echo "  Conway's Game of Life - Multi-Pattern Benchmark"
echo "═══════════════════════════════════════════════════════"
echo "Grid: ${GRID_SIZE}×${GRID_SIZE}"
echo "Steps: ${STEPS}"
echo "Patterns: ${PATTERNS[@]}"
echo "Process counts: ${PROCESS_COUNTS[@]}"
echo ""

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✓ Activated .venv"
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Activated venv"
else
    echo "⚠ Warning: No virtual environment found, using system Python"
fi
echo ""

# Create output directory
OUTPUT_DIR="benchmark_local"
rm -rf ${OUTPUT_DIR}
mkdir -p ${OUTPUT_DIR}

# Main results summary
echo "# Benchmark Results Summary" > ${OUTPUT_DIR}/summary.txt
echo "Grid: ${GRID_SIZE}×${GRID_SIZE}, Steps: ${STEPS}" >> ${OUTPUT_DIR}/summary.txt
echo "" >> ${OUTPUT_DIR}/summary.txt

# Run benchmarks for each pattern
for PATTERN in "${PATTERNS[@]}"; do
    echo "───────────────────────────────────────────────────────"
    echo "Testing pattern: ${PATTERN}"
    echo "───────────────────────────────────────────────────────"
    
    # Create pattern-specific directory
    PATTERN_DIR="${OUTPUT_DIR}/${PATTERN}"
    mkdir -p ${PATTERN_DIR}
    
    # Create results file for this pattern
    echo "# ranks,time_seconds,speedup,efficiency" > ${PATTERN_DIR}/results.txt
    
    BASELINE_TIME=0
    
    for NP in "${PROCESS_COUNTS[@]}"; do
        if [ ${NP} -gt ${MAX_NP} ]; then
            continue
        fi
        
        SNAP_DIR="${PATTERN_DIR}/snapshots_np${NP}"
        
        echo "  np=${NP}..."
        
        # Run simulation
        mpirun -np ${NP} python ${SCRIPT} \
            --nx ${GRID_SIZE} --ny ${GRID_SIZE} \
            --steps ${STEPS} \
            --pattern ${PATTERN} \
            --seed ${SEED} \
            --output-dir ${SNAP_DIR} \
            --save-interval $(( ${STEPS} / 10 )) \
            --benchmark > ${PATTERN_DIR}/bench_np${NP}.log 2>&1
        
        # Extract timing
        TIME=$(grep "^BENCHMARK: ranks=" ${PATTERN_DIR}/bench_np${NP}.log | sed 's/.*time=\([0-9.]*\).*/\1/')
        
        if [ ${NP} -eq 1 ]; then
            BASELINE_TIME=${TIME}
            SPEEDUP=1.00
            EFFICIENCY=100.0
        else
            SPEEDUP=$(echo "scale=2; ${BASELINE_TIME} / ${TIME}" | bc)
            EFFICIENCY=$(echo "scale=1; (${SPEEDUP} / ${NP}) * 100" | bc)
        fi
        
        echo "    Time: ${TIME}s, Speedup: ${SPEEDUP}×, Efficiency: ${EFFICIENCY}%"
        
        echo "${NP},${TIME},${SPEEDUP},${EFFICIENCY}" >> ${PATTERN_DIR}/results.txt
    done
    
    echo ""
    
    # Add pattern summary to main summary
    echo "## ${PATTERN}" >> ${OUTPUT_DIR}/summary.txt
    cat ${PATTERN_DIR}/results.txt >> ${OUTPUT_DIR}/summary.txt
    echo "" >> ${OUTPUT_DIR}/summary.txt
    
    # Create visualizations for each pattern
    echo "  Creating visualizations..."
    python visualize_local.py \
        --input-dir ${SNAP_DIR} \
        --output ${PATTERN_DIR}/${PATTERN}_animation.gif \
        --fps 10 > /dev/null 2>&1 || echo "    (animation skipped)"
done

echo "═══════════════════════════════════════════════════════"
echo "  Generating Comparison Plots"
echo "═══════════════════════════════════════════════════════"

# Create comprehensive comparison plot
cat > ${OUTPUT_DIR}/plot_comparison.py << 'PLOT_EOF'
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

patterns = ["glider_gun", "r_pentomino", "glider", "random"]
pattern_labels = ["Glider Gun", "R-Pentomino", "Glider", "Random"]
colors = ['blue', 'green', 'red', 'orange']

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

for idx, pattern in enumerate(patterns):
    results_file = f"{pattern}/results.txt"
    if not os.path.exists(results_file):
        continue
    
    data = {'ranks': [], 'time': [], 'speedup': [], 'efficiency': []}
    
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data['ranks'].append(int(row['# ranks']))
            data['time'].append(float(row['time_seconds']))
            data['speedup'].append(float(row['speedup']))
            data['efficiency'].append(float(row['efficiency']))
    
    color = colors[idx]
    label = pattern_labels[idx]
    
    # Plot 1: Execution Time
    axes[0, 0].plot(data['ranks'], data['time'], 'o-', linewidth=2, 
                    markersize=8, label=label, color=color)
    
    # Plot 2: Speedup
    axes[0, 1].plot(data['ranks'], data['speedup'], 'o-', linewidth=2, 
                    markersize=8, label=label, color=color)
    
    # Plot 3: Efficiency
    axes[1, 0].plot(data['ranks'], data['efficiency'], 'o-', linewidth=2, 
                    markersize=8, label=label, color=color)
    
    # Plot 4: Speedup vs Ideal (for first pattern only, to avoid clutter)
    if idx == 0:
        axes[1, 1].plot(data['ranks'], data['speedup'], 'o-', linewidth=2, 
                        markersize=8, label='Actual (Glider Gun)', color='blue')
        axes[1, 1].plot(data['ranks'], data['ranks'], '--', linewidth=2, 
                        alpha=0.5, label='Ideal', color='gray')

# Configure Plot 1: Execution Time
axes[0, 0].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[0, 0].set_ylabel('Time (seconds)', fontweight='bold', fontsize=11)
axes[0, 0].set_title('Execution Time Comparison', fontweight='bold', fontsize=13)
axes[0, 0].legend(fontsize=10)
axes[0, 0].grid(True, alpha=0.3)

# Configure Plot 2: Speedup
axes[0, 1].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[0, 1].set_ylabel('Speedup', fontweight='bold', fontsize=11)
axes[0, 1].set_title('Speedup Comparison', fontweight='bold', fontsize=13)
axes[0, 1].legend(fontsize=10)
axes[0, 1].grid(True, alpha=0.3)

# Configure Plot 3: Efficiency
axes[1, 0].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[1, 0].set_ylabel('Parallel Efficiency (%)', fontweight='bold', fontsize=11)
axes[1, 0].set_title('Parallel Efficiency Comparison', fontweight='bold', fontsize=13)
axes[1, 0].axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
axes[1, 0].legend(fontsize=10)
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].set_ylim([70, 110])

# Configure Plot 4: Speedup vs Ideal
axes[1, 1].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[1, 1].set_ylabel('Speedup', fontweight='bold', fontsize=11)
axes[1, 1].set_title('Speedup vs Ideal (Glider Gun)', fontweight='bold', fontsize=13)
axes[1, 1].legend(fontsize=10)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('pattern_comparison.png', dpi=150, bbox_inches='tight')
print("✓ Saved: pattern_comparison.png")
PLOT_EOF

cd ${OUTPUT_DIR}
python plot_comparison.py
cd ..

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✓ Benchmark Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Results saved in: ${OUTPUT_DIR}/"
echo ""
echo "Files generated:"
echo "  📊 summary.txt                  - All results summary"
echo "  📈 pattern_comparison.png       - Comparison plots"
echo ""
for PATTERN in "${PATTERNS[@]}"; do
    echo "  📁 ${PATTERN}/"
    echo "     - results.txt"
    echo "     - ${PATTERN}_animation.gif"
    echo "     - bench_np*.log"
done
echo ""

