#!/bin/bash
#SBATCH --nodes=1                       #requests 1 compute node.
#SBATCH --ntasks=1                      #requests 1 CPU core.
#SBATCH --job-name=INC                  #sets the name of the job as "INC".
#SBATCH --time=00:20:00                 #sets a runtime of 20 minutes
#SBATCH --partition=prod                #submits to "general" queue.
#SBATCH --account=projectname           #submits the job against "projectname" project.
#SBATCH --output=inc.%j.out             #writes standard output to "inc.JobID.out".
#SBATCH --error=inc.%j.err              #writes error output to "inc.JobID.out".

bash increment.sh $1 $2
