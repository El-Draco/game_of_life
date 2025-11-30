# Conway's Game of Life - MPI Parallel Implementation

Distributed systems project implementing Conway's Game of Life using MPI for parallel computation with 1D row decomposition.

## 🚀 Quick Start

### Local Run (macOS)

```bash
# Setup environment
./setup_local.sh

# Run simulation (saves snapshots)
uv run mpirun -np 4 python life_mpi.py \
    --nx 512 --ny 512 \
    --steps 500 \
    --pattern glider_gun \
    --output-dir snapshots \
    --save-interval 50

# Create animation
uv run python visualize.py \
    --input-dir snapshots \
    --output animation.gif \
    --fps 10
```

### HPC Cluster (SLURM)

```bash
# Submit job
sbatch submit.sbatch

# After completion, create visualizations
python visualize.py \
    --input-dir snapshots \
    --output animation.gif
```

## 📁 Project Structure

```
Core Files:
├── life_mpi.py               # Main simulation (MPI parallelized)
├── visualize.py              # Post-processing visualization
├── submit.sbatch             # SLURM job submission script
└── setup_local.sh            # Local environment setup

Testing & Benchmarking:
├── test_correctness_local.sh # Verify correctness across different np
├── benchmark_local.sh        # Local performance benchmarking
└── benchmark_hpc.sh          # HPC performance benchmarking

Configuration:
├── pyproject.toml            # Python dependencies
├── uv.lock                   # Dependency lock file
└── .python-version           # Python version (3.12)

Documentation:
├── README.md                 # This file
└── USAGE.md                  # Detailed usage guide
```

## ✨ Features

✅ **1D Row Decomposition** - Grid partitioned across MPI ranks by rows  
✅ **Toroidal Boundaries** - Wrap-around edges (Pac-Man style)  
✅ **Non-blocking Communication** - `Isend`/`Irecv` + `Waitall` for efficiency  
✅ **Halo Exchange** - Automatic ghost cell communication  
✅ **Binary Snapshots** - Compressed `.npz` format for fast I/O  
✅ **Post-processing Visualization** - Separate from simulation for HPC  
✅ **Rank Heatmap** - Visualize workload distribution across ranks  
✅ **Correctness Testing** - Verify identical output across different process counts  
✅ **Performance Benchmarking** - Measure speedup and parallel efficiency  

## 🧪 Testing

### Correctness Test
```bash
./test_correctness_local.sh
```
Runs with `np=1,2,4,8` and verifies all produce identical checksums.

### Performance Benchmark
```bash
./benchmark_local.sh
```
Measures execution time, speedup, and efficiency. Generates plots.

## 📊 Example Results

### Small Grid (512×512, 4 ranks)
- Time: ~0.5 seconds for 200 steps
- Speedup: 3.2× (vs 1 rank)
- Efficiency: 80%

### Large Grid (16K×16K, 32 ranks)
- Time: ~120 seconds for 500 steps
- Output: ~400MB snapshots (save-interval=100)

### Massive Grid (64K×64K, 512 ranks)
- Feasible on HPC with proper resource allocation
- Snapshots saved for post-processing

## 🎯 Patterns

- **`glider_gun`** - Gosper glider gun (generates gliders)
- **`glider`** - Simple moving pattern
- **`r_pentomino`** - Chaotic, long-lived pattern
- **`random`** - Random initial state

## 📖 Documentation

See **`USAGE.md`** for:
- Detailed command-line options
- HPC SLURM scripts
- Visualization examples
- Troubleshooting guide
- Performance optimization tips

## 🛠️ Technical Details

### Decomposition Strategy

**Why 1-D Row Decomposition?**

We chose 1-D row decomposition for several practical reasons:

1. **Simplicity** - Each rank owns a contiguous block of rows, making data distribution straightforward
2. **Minimal Communication** - Only 2 neighbors per rank (top and bottom), reducing message count
3. **Cache Efficiency** - Row-major storage in numpy means contiguous memory access patterns
4. **Good Scaling** - Suitable for grids where `rows >> num_ranks` (e.g., 16K rows, 32 ranks = 512 rows/rank)
5. **Load Balance** - Easy to distribute remainder rows evenly when grid doesn't divide perfectly

**When would 2-D be better?** For very large rank counts (100+) or highly non-square grids, 2-D decomposition reduces per-rank communication overhead at the cost of implementation complexity.

**Our implementation:** Each rank handles `⌈ny/size⌉` rows plus 2 halo rows (top/bottom), exchanges boundaries each step with toroidal wraparound.

### MPI Operations Used:
- `COMM_WORLD` - Communicator
- `Get_rank()`, `Get_size()` - Process identification
- `Bcast()` - Broadcast grid dimensions
- `Scatterv()` - Distribute variable-sized chunks
- `Gatherv()` - Collect results
- `Isend()`, `Irecv()` - Non-blocking point-to-point
- `Waitall()` - Wait for all requests
- `Barrier()` - Synchronization

### Game of Life Rules (B3/S23):
- **Birth**: Dead cell with exactly 3 neighbors becomes alive
- **Survival**: Live cell with 2-3 neighbors stays alive
- **Death**: Otherwise, cell dies

### Architecture:
1. **Simulation** (`life_mpi.py`) - Fast, minimal overhead
2. **Visualization** (`visualize.py`) - Separate post-processing
3. **Testing** - Automated correctness and performance checks

## 🔧 Requirements

- Python 3.10.5+
- `mpi4py` - MPI bindings
- `numpy` - Array operations
- `matplotlib` - Visualization (optional, for post-processing)
- `scipy` - Gaussian filter for heatmap (optional)
- `pillow` - GIF creation (optional)

## 📝 Notes

- Optimized for large-scale HPC runs (64K×64K grids)
- Simulation and visualization separated for efficiency
- All MPI communication is non-blocking to avoid deadlocks
- Toroidal boundaries ensure no edge effects
- Binary snapshots compressed with `numpy.savez_compressed`

## 🎓 Academic Context

Graduate-level Distributed Systems course project demonstrating:
- MPI parallelization techniques
- Domain decomposition strategies
- Performance analysis and optimization
- Scalability testing
- Load balancing visualization

---

**Author:** RRyas  
**Course:** Distributed Systems  
**Implementation:** 1D Row Decomposition with MPI
