# Conway's Game of Life - MPI Implementation

## 📁 Project Architecture (Optimized for HPC)

### Core Files:
- **`life_mpi.py`** - Simulation only (fast, optimized for large grids)
- **`visualize.py`** - Post-processing (create animations from snapshots)
- **`test_correctness_local.sh`** - Verify correctness locally
- **`benchmark_local.sh`** - Performance benchmarking locally
- **`benchmark_hpc.sh`** - HPC SLURM benchmark script

---

## 🚀 Quick Start

### 1. Local Testing (macOS with uv)

```bash
# Run simulation (saves snapshots)
uv run mpirun -np 4 python life_mpi.py \
    --nx 512 --ny 512 \
    --steps 500 \
    --pattern glider_gun \
    --output-dir snapshots \
    --save-interval 50

# Create animation from snapshots
python visualize.py \
    --input-dir snapshots \
    --output animation.gif \
    --fps 10

# Create heatmap visualization
python visualize.py \
    --input-dir snapshots \
    --output heatmap.gif \
    --show-ranks \
    --ranks 4 \
    --fps 10
```

### 2. Test Correctness

```bash
./test_correctness_local.sh
```

Verifies that `np=1,2,4,8` all produce identical checksums.

### 3. Benchmark Performance

```bash
./benchmark_local.sh
```

Measures time, speedup, and parallel efficiency.  
Generates: `benchmark_results.txt` and `benchmark_plot.png`

---

## 🖥️ HPC Usage (SLURM)

### Large-Scale Simulation (64K × 64K grid)

```bash
# Submit simulation job
sbatch <<EOF
#!/bin/bash
#SBATCH --job-name=life_64k
#SBATCH --output=logs/life_%j.out
#SBATCH --error=logs/life_%j.err
#SBATCH --nodes=16
#SBATCH --ntasks-per-node=32
#SBATCH --time=02:00:00
#SBATCH --partition=compute

module load python/3.10.5 openmpi/4.1.4
source .venv/bin/activate

mkdir -p logs snapshots_64k

mpirun -np 512 python life_mpi.py \
    --nx 65536 --ny 65536 \
    --steps 2000 \
    --pattern glider_gun \
    --output-dir snapshots_64k \
    --save-interval 100 \
    --benchmark
EOF
```

### Post-Process on Login Node

```bash
# After simulation completes, create visualization
python visualize.py \
    --input-dir snapshots_64k \
    --output life_64k_animation.gif \
    --fps 10

# Create heatmap showing rank distribution
python visualize.py \
    --input-dir snapshots_64k \
    --output life_64k_heatmap.gif \
    --show-ranks \
    --ranks 512 \
    --fps 5
```

### Run Benchmarks

```bash
sbatch benchmark_hpc.sh
```

---

## 📊 Output Files

### Simulation Output:
```
snapshots/
  step_000000.npz  # Initial state
  step_000100.npz  # After 100 steps
  step_000200.npz  # After 200 steps
  ...
  step_002000.npz  # Final state (includes metadata)
```

### Snapshot Format:
```python
import numpy as np
data = np.load('step_000100.npz')
grid = data['grid']  # (ny, nx) array of 0s and 1s
# Final step also includes:
# - checksum
# - alive_cells
# - elapsed_time
```

---

## 🔧 Key Parameters

### Grid Sizes:
- **Small (testing):** 128 × 128
- **Medium (local):** 512 × 512
- **Large (HPC):** 4096 × 4096
- **Huge (HPC):** 16384 × 16384
- **Massive (HPC):** 65536 × 65536

### Patterns:
- `glider_gun` - Gosper glider gun (generates gliders)
- `glider` - Simple moving pattern
- `r_pentomino` - Chaotic pattern
- `random` - Random initial state

### Save Intervals:
- `--save-interval 0` - Only save final state (fastest)
- `--save-interval 100` - Save every 100 steps
- For animations: Use smaller intervals (20-50)

---

## ⚡ Performance Tips

### For Maximum Speed:
```bash
# Disable snapshots during simulation
python life_mpi.py --save-interval 0 --benchmark

# Only visualize small grids
# For 64K grids: subsample or skip visualization
```

### Memory Usage:
- Grid: `nx × ny × 1 byte` per rank
- Example: 16K × 16K with 64 ranks = ~4MB per rank
- Example: 64K × 64K with 512 ranks = ~8MB per rank

### Optimal Process Count:
- Local (Mac): 4-8 processes
- HPC: Aim for 128-2048 rows per rank
- Too many ranks → communication overhead
- Too few ranks → load imbalance

---

## 🧪 Testing Workflow

1. **Correctness** (local):
   ```bash
   ./test_correctness_local.sh
   ```

2. **Small benchmark** (local):
   ```bash
   ./benchmark_local.sh
   ```

3. **Large run** (HPC):
   ```bash
   sbatch submit.sbatch  # Or custom SLURM script
   ```

4. **Visualization** (after completion):
   ```bash
   python visualize.py --input-dir snapshots --output result.gif
   ```

---

## 🐛 Troubleshooting

### "No module named 'mpi4py'":
```bash
uv pip install mpi4py numpy
# or on HPC:
pip install --user mpi4py numpy
```

### "No snapshots found":
- Check `--output-dir` path
- Ensure `--save-interval > 0`
- Verify simulation completed successfully

### Slow visualization:
- Use `--save-interval` to skip frames
- Subsample large grids in `visualize.py`
- Create animations on login node, not compute nodes

### Memory issues:
- Reduce grid size
- Increase number of ranks
- Check snapshot directory size

---

## 📈 Example Results

### 512×512 grid, 4 ranks, 200 steps:
```
Time: ~0.5 seconds
Speedup (vs 1 rank): 3.2x
Efficiency: 80%
```

### 16K×16K grid, 32 ranks, 500 steps:
```
Time: ~120 seconds
Output: ~400MB of snapshots (with interval=100)
```

---

## 🎓 What's Implemented:

✅ **1D Row Decomposition** with toroidal boundaries  
✅ **Non-blocking MPI** (`Isend`/`Irecv` + `Waitall`)  
✅ **Halo exchange** for ghost cells  
✅ **Correctness testing** across different process counts  
✅ **Performance benchmarking** with speedup/efficiency  
✅ **Binary snapshot format** (compressed, fast I/O)  
✅ **Post-processing visualization** (separated from simulation)  
✅ **Rank heatmap** visualization (shows load distribution)  
✅ **HPC SLURM scripts** with proper resource management  

---

## 📝 Notes:

- All MPI communication uses **non-blocking** calls to avoid deadlocks
- Toroidal boundaries: top connects to bottom, left to right
- Rank 0 handles I/O (initialization, gathering, saving)
- Conway's rules: B3/S23 (birth on 3, survive on 2-3)
- Checksum = sum of all alive cells (for correctness verification)

For questions or issues, see the code comments or ask your instructor! 🚀

