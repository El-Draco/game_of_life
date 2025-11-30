if [ -f Az.npy ] ; then
    rm Az.npy
fi
if [ -f Surface_relaxation.html ] ; then
    rm Surface_relaxation.html
fi


# Submit first job
jobid=$(sbatch  --parsable slurm_relaxation_config.sh)
echo $jobid

# Submit second job with dependency "afterok"
sbatch --dependency=afterok:$jobid slurm_plot_config.sh 
