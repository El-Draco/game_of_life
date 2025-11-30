# Submit first job
jobid=$(sbatch  --parsable slurm_array_config.sh 40)
echo $jobid

# Submit second job with dependency "afterok"
sbatch --dependency=afterok:$jobid slurm_array_config.sh 40
