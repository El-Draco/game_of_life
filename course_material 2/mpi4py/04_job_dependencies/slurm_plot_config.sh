#!/bin/bash
#SBATCH --nodes=1                       #requests 1 compute nodes.
#SBATCH --ntasks=1                      #requests 1 CPU cores.
#SBATCH --ntasks-per-node=1             #requests 1 CPU cores per node.
#SBATCH --job-name=Plot                 #sets the name of the job as "hello".
#SBATCH --time=00:02:00                 #sets a runtime of 2 minutes
#SBATCH --partition=prod                #submits to "prod" queue.
#SBATCH --account=projectname           #submits the job against "projectname" project.
#SBATCH --output=Plot.%j.out            #writes standard output to "Plot.JobID.out".
#SBATCH --error=Plot.%j.err             #writes error output to "Plot.JobID.out".

module purge
module load miniconda/3

conda deactivate
conda activate ../env

python plot_relaxation.py

