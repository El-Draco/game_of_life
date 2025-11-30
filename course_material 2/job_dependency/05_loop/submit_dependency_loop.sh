# Submit first job
jobid=$(sbatch --parsable slurm_config.sh 777 20)
echo $jobid

for i in $(seq 1 9)
do
    jobid=$(sbatch --parsable --dependency=afterok:$jobid  slurm_config.sh 777 20)
    echo $jobid
done

