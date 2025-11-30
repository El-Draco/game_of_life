# Submit first job
jobid=$(sbatch --parsable slurm_config.sh 222 40)
echo $jobid

# Submit second job with dependency "afternotok"
sbatch --dependency=afternotok:$jobid slurm_config.sh 222 40
