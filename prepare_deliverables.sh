#!/bin/bash
# Prepare final deliverables for submission

set -e

echo "═══════════════════════════════════════════════════════"
echo "  Preparing Deliverables for Submission"
echo "═══════════════════════════════════════════════════════"

# Create deliverables directory
DELIV_DIR="deliverables"
rm -rf ${DELIV_DIR}
mkdir -p ${DELIV_DIR}

echo ""
echo "📦 Copying core files..."

# Copy main code
cp life_mpi.py ${DELIV_DIR}/

# Copy SLURM scripts
cp backup.sbatch ${DELIV_DIR}/submit.sbatch  # Use backup as main submission script

# Copy visualization scripts
cp visualize.py ${DELIV_DIR}/
cp visualize_local.py ${DELIV_DIR}/

# Copy environment
cp environment.yml ${DELIV_DIR}/

# Copy README
cp README.md ${DELIV_DIR}/

# Copy report
if [ -f report.ipynb ]; then
    cp report.ipynb ${DELIV_DIR}/
    echo "  ✓ report.ipynb"
fi

echo "  ✓ life_mpi.py"
echo "  ✓ submit.sbatch"
echo "  ✓ visualize.py"
echo "  ✓ visualize_local.py"
echo "  ✓ environment.yml"
echo "  ✓ README.md"

echo ""
echo "📊 Copying HPC results..."

# Copy HPC benchmark output
if [ -f life_full.3925211.out ]; then
    cp life_full.3925211.out ${DELIV_DIR}/hpc_benchmark.out
    echo "  ✓ hpc_benchmark.out (from life_full.3925211.out)"
fi

echo ""
echo "📈 Copying local benchmark results..."

# Copy local benchmarks if they exist
if [ -d benchmark_local ]; then
    mkdir -p ${DELIV_DIR}/local_benchmarks
    cp benchmark_local/summary.txt ${DELIV_DIR}/local_benchmarks/ 2>/dev/null || true
    cp benchmark_local/pattern_comparison.png ${DELIV_DIR}/local_benchmarks/ 2>/dev/null || true
    
    for pattern in glider_gun r_pentomino glider random; do
        if [ -d benchmark_local/${pattern} ]; then
            mkdir -p ${DELIV_DIR}/local_benchmarks/${pattern}
            cp benchmark_local/${pattern}/results.txt ${DELIV_DIR}/local_benchmarks/${pattern}/ 2>/dev/null || true
            cp benchmark_local/${pattern}/${pattern}_animation.gif ${DELIV_DIR}/local_benchmarks/${pattern}/ 2>/dev/null || true
        fi
    done
    
    echo "  ✓ local_benchmarks/"
fi

echo ""
echo "🎬 Generating HPC visualizations..."

# Create HPC visualization if snapshots exist
if [ -d snapshots ] && [ "$(ls -A snapshots)" ]; then
    echo "  Generating animation from snapshots/..."
    python visualize.py --input-dir snapshots --output ${DELIV_DIR}/hpc_animation.gif --fps 10
    echo "  ✓ hpc_animation.gif"
else
    echo "  ⚠ No snapshots/ directory found (need to download from HPC)"
    echo "  Run: python visualize.py --input-dir snapshots --output hpc_animation.gif"
fi

echo ""
echo "📋 Creating submission checklist..."

cat > ${DELIV_DIR}/CHECKLIST.txt << 'EOF'
═════════════════════════════════════════════════════════════
  DELIVERABLES CHECKLIST - Conway's Game of Life (MPI)
═════════════════════════════════════════════════════════════

Required Files:
  [✓] life_mpi.py              - Main simulation code
  [✓] submit.sbatch            - SLURM submission script
  [✓] README.md                - Usage instructions
  [✓] environment.yml          - Dependencies
  [✓] report.ipynb             - Project report (1-3 pages)

HPC Results:
  [✓] hpc_benchmark.out        - Benchmark results (correctness + timing)
  [~] hpc_animation.gif        - 16K×16K simulation visualization
                                 (generate after downloading snapshots/)

Local Benchmarks:
  [✓] local_benchmarks/        - All pattern benchmarks (256×256)
      ├── summary.txt          - Results summary
      ├── pattern_comparison.png - Speedup plots
      └── [pattern]/           - Per-pattern results
          ├── results.txt
          └── [pattern]_animation.gif

Visualizations:
  [✓] visualize.py             - Expanding view (for HPC)
  [✓] visualize_local.py       - Full features (for local)

═════════════════════════════════════════════════════════════

Report Contents (report.ipynb):
  ✓ Implementation overview (1-D row decomposition)
  ✓ Correctness evidence (checksums from HPC)
  ✓ Timing for multiple process counts (1, 2, 4, 8, 16)
  ✓ Decomposition choice explanation
  ✓ Performance plots (speedup, efficiency)
  ✓ Pattern visualizations
  ✓ Future work section (2-D decomposition)

═════════════════════════════════════════════════════════════

Submission Instructions:
  1. Upload to HPC: /dpc/teach0026/<StudentID>/
  2. Ensure life_mpi.py is named gol.py or keep as life_mpi.py
  3. Include this deliverables folder
  4. Submit report.ipynb (can be HTML/PDF if required)

═════════════════════════════════════════════════════════════

Optional Extras (Completed):
  ✓ Non-blocking communication (Isend/Irecv)
  ✓ PNG/GIF snapshots and animations
  ✓ Multiple patterns tested
  ✓ Comprehensive benchmarking

Future Extensions:
  [ ] 2-D decomposition (prepared, not yet implemented)

═════════════════════════════════════════════════════════════
EOF

echo "  ✓ CHECKLIST.txt"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✓ Deliverables Ready!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "All files in: ${DELIV_DIR}/"
echo ""
echo "Next steps:"
echo "  1. Review report.ipynb (add local benchmark results)"
echo "  2. Download snapshots/ from HPC (if not done)"
echo "  3. Generate hpc_animation.gif from snapshots/"
echo "  4. Final review of all files"
echo "  5. Submit to HPC: /dpc/teach0026/<StudentID>/"
echo ""

