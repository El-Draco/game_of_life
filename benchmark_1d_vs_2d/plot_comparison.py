import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

data_1d = {'ranks': [], 'time': [], 'speedup': [], 'efficiency': []}
data_2d = {'ranks': [], 'time': [], 'speedup': [], 'efficiency': []}

with open('results.txt', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        decomp = row['# decomp']
        ranks = int(row['ranks'])
        time = float(row['time_seconds'])
        speedup = float(row['speedup'])
        efficiency = float(row['efficiency'])
        
        if decomp == '1d':
            data_1d['ranks'].append(ranks)
            data_1d['time'].append(time)
            data_1d['speedup'].append(speedup)
            data_1d['efficiency'].append(efficiency)
        else:
            data_2d['ranks'].append(ranks)
            data_2d['time'].append(time)
            data_2d['speedup'].append(speedup)
            data_2d['efficiency'].append(efficiency)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Plot 1: Execution Time
axes[0].plot(data_1d['ranks'], data_1d['time'], 'o-', linewidth=2, markersize=8, 
             label='1-D Row', color='blue')
axes[0].plot(data_2d['ranks'], data_2d['time'], 's-', linewidth=2, markersize=8, 
             label='2-D Grid', color='red')
axes[0].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[0].set_ylabel('Time (seconds)', fontweight='bold', fontsize=11)
axes[0].set_title('Execution Time Comparison', fontweight='bold', fontsize=13)
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)

# Plot 2: Speedup
axes[1].plot(data_1d['ranks'], data_1d['speedup'], 'o-', linewidth=2, markersize=8, 
             label='1-D Row', color='blue')
axes[1].plot(data_2d['ranks'], data_2d['speedup'], 's-', linewidth=2, markersize=8, 
             label='2-D Grid', color='red')
ideal_ranks = np.array(sorted(set(data_1d['ranks'] + data_2d['ranks'])))
axes[1].plot(ideal_ranks, ideal_ranks, '--', linewidth=2, alpha=0.5, 
             label='Ideal', color='gray')
axes[1].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[1].set_ylabel('Speedup', fontweight='bold', fontsize=11)
axes[1].set_title('Speedup Comparison', fontweight='bold', fontsize=13)
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

# Plot 3: Efficiency
axes[2].plot(data_1d['ranks'], data_1d['efficiency'], 'o-', linewidth=2, markersize=8, 
             label='1-D Row', color='blue')
axes[2].plot(data_2d['ranks'], data_2d['efficiency'], 's-', linewidth=2, markersize=8, 
             label='2-D Grid', color='red')
axes[2].axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='100%')
axes[2].set_xlabel('Number of Processes', fontweight='bold', fontsize=11)
axes[2].set_ylabel('Parallel Efficiency (%)', fontweight='bold', fontsize=11)
axes[2].set_title('Efficiency Comparison', fontweight='bold', fontsize=13)
axes[2].legend(fontsize=11)
axes[2].grid(True, alpha=0.3)
axes[2].set_ylim([70, 105])

plt.tight_layout()
plt.savefig('1d_vs_2d_comparison.png', dpi=150, bbox_inches='tight')
print("\n✓ Saved: 1d_vs_2d_comparison.png")
