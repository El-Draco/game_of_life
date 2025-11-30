# 🖥️ Almesbar HPC Setup Guide

## 📋 Before You Start

### 1. Get Your Account Information
You need to know:
- **Username**: Your Almesbar username (format: `username@kunet.ae`)
- **Project Code**: Your HPC project allocation code
  - Replace `hpc_project_code` in all `.sbatch` files with your actual code

### 2. Update Scripts with Your Project Code

**Edit these files and replace `hpc_project_code`:**
```bash
# On Almesbar, edit:
nano submit.sbatch          # Line 9: --account=YOUR_PROJECT_CODE
nano submit_all.sbatch      # Line 9: --account=YOUR_PROJECT_CODE  
nano benchmark_hpc.sh       # Line 9: --account=YOUR_PROJECT_CODE
```

---

## 📤 Step 1: Transfer Files to Almesbar

### Option A: Using FileZilla (GUI)
1. Open FileZilla
2. Click arrow next to "Site Manager"
3. Select `Almesbar_HPC`
4. Enter your password
5. Navigate to your home directory on Almesbar
6. Upload the entire `dist_sys` folder

### Option B: Using rsync (Command Line)
```bash
# From your Mac:
rsync -avz --exclude='.venv' --exclude='.git' \
    ~/Documents/dist_sys/ username@almesbar.ku.ac.ae:~/dist_sys/
```

### Option C: Using scp
```bash
# From your Mac:
scp -r ~/Documents/dist_sys username@almesbar.ku.ac.ae:~/
```

---

## 🔧 Step 2: Setup on Almesbar

### SSH to Almesbar
```bash
ssh username@almesbar.ku.ac.ae
```

### Navigate to project directory
```bash
cd dist_sys
ls -la
```

### Check available modules
```bash
# Check Python versions
module avail python

# Check MPI versions  
module avail mpi
module avail openmpi

# Example output:
# python/3.10.5
# openmpi/4.1.4
```

### Update module names if needed
If your module names are different, edit the scripts:
```bash
nano submit.sbatch
# Update lines 17-18:
# module load python/YOUR_VERSION
# module load openmpi/YOUR_VERSION
```

### Setup Python environment
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install numpy mpi4py matplotlib scipy pillow
```

---

## 🧪 Step 3: Quick Test (Recommended!)

### Create a test job
```bash
nano test_quick.sbatch
```

### Paste this content:
```bash
#!/bin/bash
#SBATCH --job-name=life_test
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --time=00:10:00
#SBATCH --partition=devel
#SBATCH --account=hpc_project_code

mkdir -p logs test_output

module purge
module load python/3.10.5
module load openmpi/4.1.4

source .venv/bin/activate

mpirun -np 4 python life_mpi.py \
    --nx 128 --ny 128 \
    --steps 10 \
    --decomp rows \
    --pattern glider \
    --output-dir test_output \
    --save-interval 0 \
    --benchmark

echo ""
echo "✓ Test successful!"
rm -rf test_output
```

### Submit test job
```bash
sbatch test_quick.sbatch
```

### Monitor test
```bash
# Check job status
squeue --user=$USER

# Watch output in real-time
tail -f logs/life_test-*.out

# Check job details
scontrol show job JOBID
```

### Verify test passed
```bash
# Check output file
cat logs/life_test-*.out

# Should see:
# "Initialized glider pattern..."
# "BENCHMARK: ranks=4..."
# "✓ Test successful!"
```

---

## 🚀 Step 4: Submit Full Job

### For benchmark + production (recommended):
```bash
sbatch submit_all.sbatch
```

### For production only:
```bash
sbatch submit.sbatch
```

### Monitor job:
```bash
# Check queue
squeue --user=$USER

# Output:
# JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
#  1234      prod life_full username  R      10:23      4 cn-02-[01-04]

# Watch live output
tail -f logs/life_full-*.out

# Get detailed job info
scontrol show job JOBID
```

### Cancel if needed:
```bash
scancel JOBID
```

---

## 📊 Step 5: Check Results

### After job completes:
```bash
# Check if job finished
squeue --user=$USER
# (should be empty when done)

# View output log
cat logs/life_full-*.out

# Check generated files
ls -lh snapshots/
ls -lh benchmark_data/

# View benchmark results
cat benchmark_data/results.txt
```

---

## 📥 Step 6: Download Results to Your Mac

### Option A: FileZilla
1. Connect to Almesbar_HPC
2. Navigate to `dist_sys` folder
3. Select `snapshots/` and `benchmark_data/` folders
4. Right-click → Download

### Option B: rsync (Recommended)
```bash
# From your Mac:
rsync -avz username@almesbar.ku.ac.ae:~/dist_sys/snapshots/ \
    ~/Documents/dist_sys/snapshots/

rsync -avz username@almesbar.ku.ac.ae:~/dist_sys/benchmark_data/ \
    ~/Documents/dist_sys/benchmark_data/

# Download logs too
rsync -avz username@almesbar.ku.ac.ae:~/dist_sys/logs/*.out \
    ~/Documents/dist_sys/logs/
```

### Option C: scp
```bash
# From your Mac:
scp -r username@almesbar.ku.ac.ae:~/dist_sys/snapshots ./
scp -r username@almesbar.ku.ac.ae:~/dist_sys/benchmark_data ./
```

---

## 🎨 Step 7: Create Visualizations Locally

```bash
# On your Mac:
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

# Speedup plots
python plot_speedup.py benchmark_data/results.txt
```

---

## 🔍 Useful Almesbar Commands

```bash
# Check your account allocation
sshare -U

# View partition info
sinfo

# View your recent jobs
sacct --user=$USER --starttime=today

# View detailed job info (after completion)
sacct -j JOBID --format=JobID,JobName,Partition,Account,AllocCPUS,State,ExitCode

# Check disk usage
du -sh ~/dist_sys/

# Check available disk space
df -h /home/$USER
```

---

## ⚠️ Important Notes

### Partitions on Almesbar:
- `devel` - Development/testing (max 10 minutes, quick queue)
- `prod` - Production jobs (longer runs, may wait in queue)

### Account Code:
- **REQUIRED** on Almesbar
- Format: `--account=hpc_project_code`
- Get this from your professor or HPC admin
- Edit all 3 `.sbatch` files with your actual code

### Module Names:
- Verify with `module avail`
- Common: `python/3.10.5`, `openmpi/4.1.4`
- Update scripts if different

### File Paths:
- Home directory: `/home/kunet.ae/username/`
- Scratch space (if available): `/scratch/username/`
- Use scratch for large temporary files

---

## 📋 Quick Reference

| Task | Command |
|------|---------|
| **Submit job** | `sbatch submit_all.sbatch` |
| **Check queue** | `squeue --user=$USER` |
| **Cancel job** | `scancel JOBID` |
| **Job details** | `scontrol show job JOBID` |
| **Watch output** | `tail -f logs/*.out` |
| **View history** | `sacct --user=$USER` |
| **Check modules** | `module avail` |
| **Load module** | `module load python/3.10.5` |

---

## 🎓 For Your Report

After successful run, you'll have:
- ✅ Job logs: `logs/life_full-JOBID.out`
- ✅ Benchmark data: `benchmark_data/results.txt`
- ✅ Simulation data: `snapshots/step_*.npz`
- ✅ Animations: Created locally from snapshots
- ✅ Performance graphs: Created with `plot_speedup.py`

---

**Good luck with your submission! 🚀**

