# Submit first job
jobid1=$(sbatch --parsable slurm_config.sh 777 40)
echo $jobid1

# Submit second job
jobid2=$(sbatch --parsable slurm_config.sh 888 40)
echo $jobid2

# Submit third job with multiple dependencies
sbatch --dependency=afterok:$jobid1,afternotok:$jobid2 slurm_config.sh 999 40 
