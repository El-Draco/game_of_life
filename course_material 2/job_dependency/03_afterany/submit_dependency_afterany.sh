# Submit first job
jobid=$(sbatch --parsable slurm_config.sh 222 40)
echo $jobid

# Submit second job with dependency "afterany"
sbatch --dependency=afterany:$jobid slurm_config.sh 222 40
