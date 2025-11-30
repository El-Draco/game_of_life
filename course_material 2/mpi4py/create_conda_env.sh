module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

conda env create -f environment.yml --prefix ./env
