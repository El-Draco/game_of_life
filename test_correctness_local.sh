#!/bin/bash
# Local correctness testing (macOS with uv)
# Tests if different process counts produce identical results

set -e

SCRIPT="life_mpi.py"
PATTERN="glider_gun"
STEPS=50
GRID_SIZE=128
SEED=12345

echo "======================================"
echo "Conway's Game of Life - Correctness Test"
echo "======================================"
echo "Grid: ${GRID_SIZE}x${GRID_SIZE}"
echo "Steps: ${STEPS}"
echo "Pattern: ${PATTERN}"
echo ""

# Create output directory
OUTPUT_DIR="test_correctness"
rm -rf ${OUTPUT_DIR}
mkdir -p ${OUTPUT_DIR}

# Test with different process counts
for NP in 1 2 4 8; do
    SNAP_DIR="${OUTPUT_DIR}/snapshots_np${NP}"
    echo "Running with np=${NP}..."
    
    uv run mpirun -np ${NP} python ${SCRIPT} \
        --nx ${GRID_SIZE} --ny ${GRID_SIZE} \
        --steps ${STEPS} \
        --pattern ${PATTERN} \
        --seed ${SEED} \
        --output-dir ${SNAP_DIR} \
        --save-interval 0 \
        --benchmark > ${OUTPUT_DIR}/test_np${NP}.log 2>&1
    
    # Extract checksum
    CHECKSUM=$(grep "checksum=" ${OUTPUT_DIR}/test_np${NP}.log | sed 's/.*checksum=\([0-9]*\).*/\1/')
    echo "  Checksum: ${CHECKSUM}"
    echo "np=${NP} checksum=${CHECKSUM}" >> ${OUTPUT_DIR}/checksums.txt
    
    # Clean up snapshots (keep logs)
    rm -rf ${SNAP_DIR}
done

echo ""
echo "======================================"
echo "Verifying correctness..."
echo "======================================"

# Check if all checksums are identical
UNIQUE_CHECKSUMS=$(cut -d' ' -f2 ${OUTPUT_DIR}/checksums.txt | sort -u | wc -l)

if [ ${UNIQUE_CHECKSUMS} -eq 1 ]; then
    echo "✓ SUCCESS: All process counts produced identical results!"
    cat ${OUTPUT_DIR}/checksums.txt
else
    echo "✗ FAILURE: Different process counts produced different results!"
    cat ${OUTPUT_DIR}/checksums.txt
    exit 1
fi

echo ""
echo "✓ Correctness test passed!"
echo "  📁 Test logs saved in: ${OUTPUT_DIR}/"

