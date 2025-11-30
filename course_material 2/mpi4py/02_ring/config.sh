#BSUB -n 4
#BSUB -R span[ptile=2]
#BSUB -q training
#BSUB -J Hello
#BSUB -o Hello.%J.out
#BSUB -e Hello.%J.err

module load anaconda/3
source /apps/anaconda/anaconda3/etc/profile.d/conda.sh
conda deactivate
conda activate ../env

mpirun -n 4 python ring.py
