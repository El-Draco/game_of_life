#!/bin/bash
#SBATCH --job-name=life_test
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --time=00:10:00
#SBATCH --partition=devel
#SBATCH --account=teach0026

mkdir -p logs test_output

module purge
module load python/3.10.5
module load openmpi/4.1.4

source .venv/bin/activate

mpirun -np 4 python life_mpi.py \
    --nx 128 --ny 128 \
    --steps 10 \
    --decomp rows \
    --pattern glider \
    --output-dir test_output \
    --save-interval 0 \
    --benchmark

echo ""
echo "✓ Test successful!"
rm -rf test_output
