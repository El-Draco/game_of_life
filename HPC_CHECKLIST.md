# 🚀 HPC Submission Checklist

## ✅ Pre-Upload Verification (ALL PASSED!)

- [x] **Python syntax** - All .py files valid
- [x] **Bash syntax** - All .sh and .sbatch files valid
- [x] **File permissions** - All scripts executable
- [x] **Project structure** - Clean and organized
- [x] **Dependencies** - Listed in scripts
- [x] **Output directories** - Will be created automatically

---

## 📤 Upload to HPC

```bash
# From your Mac:
scp -r ~/Documents/dist_sys username@hpc-cluster:~/

# Or use rsync (better for large transfers):
rsync -avz --exclude='.venv' --exclude='.git' \
    ~/Documents/dist_sys/ username@hpc-cluster:~/dist_sys/
```

---

## ⚠️ IMPORTANT: Adjust Module Names!

Your scripts use these modules (lines 28-29 in submit_all.sbatch):
```bash
module load python/3.10.5
module load openmpi/4.1.4
```

**CHECK YOUR HPC'S MODULE NAMES:**
```bash
# SSH into HPC first, then:
module avail python    # List available Python modules
module avail mpi       # List available MPI modules
module avail openmpi   # Check OpenMPI versions
```

**Common variations:**
- `python/3.10.5` or `python/3.10` or `python3/3.10.5`
- `openmpi/4.1.4` or `mpi/openmpi/4.1.4` or `openmpi/4.1`
- Some HPCs use `intelmpi` instead of `openmpi`

**Edit BOTH files if needed:**
- `submit.sbatch` (lines 18-19)
- `submit_all.sbatch` (lines 28-29)
- `benchmark_hpc.sh` (lines 26-27)

---

## ⚙️ Check Partition Name

Your scripts use: `--partition=compute`

**Verify your HPC's partition names:**
```bash
sinfo                  # List all partitions
squeue -p compute      # Check if 'compute' exists
```

**Common partition names:**
- `compute`, `standard`, `general`
- `gpu` (if you need GPUs)
- `debug`, `devel` (for quick tests)

**If different, edit:**
- Line 8 in `submit.sbatch`
- Line 8 in `submit_all.sbatch`

---

## 🧪 Test on HPC (Recommended!)

### Step 1: Quick Test (5-10 min)

```bash
# SSH to HPC
ssh username@hpc-cluster
cd dist_sys

# Create a test script
cat > test_quick.sbatch << 'EOF'
#!/bin/bash
#SBATCH --job-name=life_test
#SBATCH --output=test_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --time=00:10:00
#SBATCH --partition=compute    # Adjust if needed!

module purge
module load python/3.10.5       # Adjust if needed!
module load openmpi/4.1.4       # Adjust if needed!

# Test setup
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install numpy mpi4py
else
    source .venv/bin/activate
fi

# Quick test run
mkdir -p test_output
mpirun -np 4 python life_mpi.py \
    --nx 128 --ny 128 \
    --steps 10 \
    --pattern glider \
    --output-dir test_output \
    --save-interval 0 \
    --benchmark

echo ""
echo "✓ Test successful!"
rm -rf test_output
EOF

# Submit test
sbatch test_quick.sbatch

# Monitor
squeue -u $USER
tail -f test_*.out  # Watch progress
```

**If test passes** ✅ → Proceed to full run  
**If test fails** ❌ → Check error messages, fix module names

---

## 🚀 Full Submission

### Option 1: Combined (Benchmark + Production)

```bash
sbatch submit_all.sbatch
```

**What it does:**
- Part 1: Benchmark (np=1,2,4,8,16,32) → ~1-2 hours
- Part 2: Production (16K×16K, 2000 steps) → ~1-2 hours
- **Total: ~2-4 hours**

**Output:**
- `logs/life_full_<jobid>.out` - Job log
- `benchmark_data/results.txt` - Performance data
- `snapshots/step_*.npz` - Simulation data

### Option 2: Production Only

```bash
sbatch submit.sbatch
```

**What it does:**
- Single run (16K×16K, 2000 steps) with 32 processes
- **Total: ~1-2 hours**

**Output:**
- `logs/life_<jobid>.out` - Job log
- `snapshots/step_*.npz` - Simulation data

---

## 📊 Monitor Job

```bash
# Check job status
squeue -u $USER

# Watch output in real-time
tail -f logs/life_full_*.out

# Check job details
scontrol show job <jobid>

# Cancel if needed
scancel <jobid>
```

**Job states:**
- `PD` (PENDING) - Waiting for resources
- `R` (RUNNING) - Currently executing
- `CG` (COMPLETING) - Finishing up
- `CD` (COMPLETED) - Done successfully
- `F` (FAILED) - Error occurred
- `TO` (TIMEOUT) - Exceeded time limit

---

## 📥 Download Results

### After job completes:

```bash
# Check what was generated
ls -lh snapshots/ benchmark_data/

# Download from Mac:
scp -r username@hpc:~/dist_sys/snapshots ./
scp -r username@hpc:~/dist_sys/benchmark_data ./
scp username@hpc:~/dist_sys/logs/life_full_*.out ./

# Or everything at once:
rsync -avz username@hpc:~/dist_sys/snapshots ./
rsync -avz username@hpc:~/dist_sys/benchmark_data ./
rsync -avz username@hpc:~/dist_sys/logs/*.out ./logs/
```

---

## 🎨 Create Visualizations (Locally)

```bash
# On your Mac (after downloading):
cd ~/Documents/dist_sys

# Simple animation
python visualize.py \
    --input-dir snapshots \
    --output animation.gif \
    --fps 10

# Heatmap with rank distribution
python visualize.py \
    --input-dir snapshots \
    --output heatmap.gif \
    --show-ranks \
    --ranks 32 \
    --fps 5

# Plot speedup graphs
python plot_speedup.py benchmark_data/results.txt
```

---

## 🐛 Common Issues & Solutions

### Issue: "module: command not found"

**Solution:** Your HPC doesn't use environment modules. Remove/comment out module lines:
```bash
# module purge
# module load python/3.11
# module load openmpi/4.1.4
```

### Issue: "mpirun: command not found"

**Solution:** Use your HPC's MPI launcher:
- Some use `srun` instead of `mpirun`
- Try: `srun python life_mpi.py ...`

### Issue: Job stays PENDING forever

**Solution:**
- Reduce resources: fewer nodes, shorter time
- Check partition: `sinfo` to see available partitions
- Check limits: `sacctmgr show qos` or ask admin

### Issue: "No module named 'mpi4py'"

**Solution:**
```bash
# Install in .venv manually before submitting
ssh hpc
cd dist_sys
python3 -m venv .venv
source .venv/bin/activate
pip install numpy mpi4py matplotlib scipy pillow
# Then submit job
```

### Issue: Job times out

**Solution:** Increase time limit:
```bash
#SBATCH --time=08:00:00  # 8 hours instead of 4
```

Or reduce grid size:
```bash
# In submit_all.sbatch, change:
PROD_NX=8192   # Instead of 16384
PROD_NY=8192
```

---

## 📋 Expected Output

### Successful job log should show:

```
════════════════════════════════════════════════════════
  Conway's Game of Life - Complete HPC Run
════════════════════════════════════════════════════════
Job ID: 123456
Nodes: 4
Total tasks: 32

Setting up Python environment...
✓ Environment ready

════════════════════════════════════════════════════════
  PART 1/2: Running Performance Benchmark
════════════════════════════════════════════════════════
...
✓ Benchmark complete!

════════════════════════════════════════════════════════
  PART 2/2: Production Simulation with Snapshots
════════════════════════════════════════════════════════

Initialized glider_gun pattern on 16384x16384 grid
Running with 32 MPI processes for 2000 steps
...
Completed 2000 steps in 234.56 seconds

✓ Production simulation complete!
```

---

## ✅ Final Checklist Before Submission

- [ ] Updated module names in scripts
- [ ] Verified partition name
- [ ] Ran quick test job successfully
- [ ] Have enough disk quota for outputs (~500MB-2GB)
- [ ] Know how to monitor jobs (`squeue`, `tail -f`)
- [ ] Know how to cancel if needed (`scancel`)
- [ ] Ready to download results after completion

---

## 🎓 For Your Report

After successful run, you'll have:

1. **Performance data** - `benchmark_data/results.txt`
2. **Speedup plots** - Generated with `plot_speedup.py`
3. **Animations** - Generated with `visualize.py`
4. **Logs** - Proving it ran successfully
5. **Checksums** - Proving correctness

**Good luck! 🚀**

