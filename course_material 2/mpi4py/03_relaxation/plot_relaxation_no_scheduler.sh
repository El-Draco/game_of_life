
module purge
module load miniconda/3

conda deactivate
conda activate ../env

python plot_relaxation.py

conda deactivate

