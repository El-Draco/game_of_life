#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=52
#SBATCH --exclusive
#SBATCH --job-name=life_backup
#SBATCH --time=01:00:00
#SBATCH --partition=prod
#SBATCH --account=teach0026
#SBATCH --output=life_backup.%j.out
#SBATCH --error=life_backup.%j.err

# Conway's Game of Life - Production Run
# 2 nodes, 104 cores, 4096x4096 grid, 2000 steps

mkdir -p logs snapshots_backup

module purge
module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

if [ ! -d "./env" ]; then
    conda env create -f environment.yml --prefix ./env
fi

conda deactivate
conda activate ./env

# Simulation parameters
PROD_NX=4096
PROD_NY=4096
PROD_STEPS=2000
PROD_PATTERN="glider_gun"
PROD_SEED=42
PROD_INTERVAL=100

mpirun -np $SLURM_NTASKS python life_mpi.py \
    --nx ${PROD_NX} \
    --ny ${PROD_NY} \
    --steps ${PROD_STEPS} \
    --decomp rows \
    --pattern ${PROD_PATTERN} \
    --seed ${PROD_SEED} \
    --output-dir snapshots_backup \
    --save-interval ${PROD_INTERVAL} \
    --benchmark
