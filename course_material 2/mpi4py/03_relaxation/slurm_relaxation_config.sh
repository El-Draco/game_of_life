#!/bin/bash
#SBATCH --nodes=2                       #requests 2 compute nodes.
#SBATCH --ntasks=48                     #requests 48 CPU cores.
#SBATCH --ntasks-per-node=24            #requests 24 CPU cores per node.
#SBATCH --job-name=Relaxation           #sets the name of the job as "hello".
#SBATCH --time=00:02:00                 #sets a runtime of 2 minutes
#SBATCH --partition=prod                #submits to "prod" queue.
#SBATCH --account=projectname           #submits the job against "projectname" project.
#SBATCH --output=Relaxation.%j.out      #writes standard output to "Relaxation.JobID.out".
#SBATCH --error=Relaxation.%j.err       #writes error output to "Relaxation.JobID.out".

module purge
module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

conda deactivate
conda activate ../env

which mpirun
mpirun python relaxation.py

