Conway's Game of Life - MPI Parallel Implementation
====================================================

Course: Distributed Systems
Platform: Almesbar HPC (Khalifa University)
Date: November 30, 2025

DELIVERABLES
------------

1. life_mpi.py         - Main simulation code (1-D row decomposition)
2. life_mpi_2d.py      - 2-D decomposition (bonus)
3. submit.sbatch       - SLURM submission script
4. environment.yml     - Conda dependencies
5. report.ipynb        - Project report (1-3 pages)
6. hpc_results.txt     - HPC benchmark results
7. hpc_animation.gif   - Production run visualization (16K x 16K)
8. hpc_snapshots/      - HPC simulation snapshots (.npz files)
9. benchmarks/         - Local benchmark results
10. visualize.py        - HPC visualization script
11. visualize_local.py  - Local visualization script


REQUIREMENTS MET
----------------

[X] 1-D row decomposition implemented
[X] Halo exchange with non-blocking communication
[X] Standard Life rules (B3/S23) on toroidal domain
[X] Performance timing across multiple process counts
[X] Correctness verification via checksums
[X] Glider gun pattern crosses process boundaries
[X] Clean, documented code
[X] SLURM submission script
[X] Comprehensive report


HPC PERFORMANCE SUMMARY
-----------------------

Grid: 512 x 512, Steps: 100

Ranks  | Time (s) | Speedup | Efficiency | Checksum
-------|----------|---------|------------|----------
1      | 83.91    | 1.00x   | 100.0%     | 63
2      | 44.41    | 1.88x   | 94.0%      | 63
4      | 20.96    | 4.00x   | 100.0%     | 63
8      | 10.48    | 8.01x   | 100.0%     | 63
16     | 5.30     | 15.84x  | 99.0%      | 63

Correctness: All runs produce identical checksums
Scaling: Near-perfect efficiency up to 16 cores


LOCAL PERFORMANCE SUMMARY
--------------------------

Grid: 256 x 256, Steps: 1000
Patterns tested: glider_gun, r_pentomino, glider, random

Average across patterns:
Ranks  | Time (s) | Speedup | Efficiency
-------|----------|---------|------------
1      | 64.66    | 1.00x   | 100.0%
2      | 32.66    | 1.97x   | 98.5%
4      | 16.42    | 3.93x   | 98.3%
8      | 9.23     | 7.00x   | 87.5%


RUNNING THE CODE
----------------

Local Testing:
  $ source .venv/bin/activate
  $ mpirun -np 4 python life_mpi.py --nx 256 --ny 256 --steps 1000

HPC Submission:
  $ sbatch submit.sbatch

Check Job Status:
  $ squeue -u $USER


IMPLEMENTATION DETAILS
----------------------

Decomposition: 1-D row decomposition
  - Grid split horizontally among ranks
  - Each rank: ny // nprocs rows (plus remainder)
  - Toroidal boundaries (wrap-around)

Communication: Non-blocking MPI
  - Irecv + Isend for halo exchange
  - Waitall to ensure completion
  - Prevents deadlocks

Load Balance:
  - Even row distribution
  - Maximum imbalance: 1 row

Communication Volume:
  - 2 * nx cells per rank per step
  - O(nx) complexity


FILES DESCRIPTION
-----------------

life_mpi.py:
  Main simulation code implementing 1-D row decomposition with MPI.
  Includes pattern initialization, halo exchange, and Game of Life rules.

submit.sbatch:
  SLURM submission script configured for Almesbar HPC.
  Uses 2 nodes, 52 tasks per node, 4096 x 4096 grid, 2000 steps.

report.ipynb:
  Jupyter notebook containing:
  - Implementation overview
  - Correctness verification
  - Performance analysis
  - Decomposition explanation
  - Future work (2-D decomposition)

hpc_results.txt:
  Complete output from HPC benchmark run including timing,
  speedup, efficiency, and checksums for np=1,2,4,8,16.

hpc_animation.gif:
  Visualization of production run (16384 x 16384, 2000 steps).
  Shows glider gun pattern evolution.

hpc_snapshots/:
  Binary snapshot files (.npz) from HPC production run.
  Contains grid state at each save interval.
  Used to generate hpc_animation.gif.

benchmarks/:
  Local benchmark results for 4 patterns over 1000 steps.
  Includes speedup comparison plots.


SUBMISSION
----------

Upload to: /dpc/teach0026/<StudentID>/
Files: All files in this deliverables/ folder


