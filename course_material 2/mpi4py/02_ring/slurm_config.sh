#!/bin/bash
#SBATCH --nodes=2                       #requests 2 compute nodes.
#SBATCH --ntasks=4                      #requests 4 CPU cores.
#SBATCH --ntasks-per-node=2             #requests 2 CPU cores per node.
#SBATCH --job-name=Ring                 #sets the name of the job as "hello".
#SBATCH --time=00:02:00                 #sets a runtime of 2 minutes
#SBATCH --partition=prod                #submits to "prod" queue.
#SBATCH --account=projectname           #submits the job against "projectname" project.
#SBATCH --output=Ring.%j.out            #writes standard output to "Ring.JobID.out".
#SBATCH --error=Ring.%j.err             #writes error output to "Ring.JobID.out".

module purge
module load gcc/9.3
module load openmpi/4.0
module load miniconda/3

conda deactivate
conda activate ../env

which mpirun
mpirun python ring.py

