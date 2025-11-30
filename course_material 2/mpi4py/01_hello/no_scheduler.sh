module purge
module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

conda deactivate
conda activate ../env

/apps/ku/gcc-9_3/openmpi/4.0/bin/mpirun -x LD_LIBRARY_PATH -x PATH -n 4 -N 2 -hostfile ./hosts.txt python hello.py

conda deactivate
