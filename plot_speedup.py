#!/usr/bin/env python3
"""
Plot speedup and efficiency from benchmark results
Usage: python plot_speedup.py benchmark_data/results.txt
"""

import sys
import csv

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Error: matplotlib required. Install with: pip install matplotlib")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: python plot_speedup.py <results_file>")
    print("Example: python plot_speedup.py benchmark_data/results.txt")
    sys.exit(1)

results_file = sys.argv[1]
output_prefix = results_file.replace('.txt', '')

# Read data
data = {'ranks': [], 'time': [], 'speedup': [], 'efficiency': []}

try:
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data['ranks'].append(int(row['# ranks']))
            data['time'].append(float(row['time_seconds']))
            data['speedup'].append(float(row['speedup']))
            data['efficiency'].append(float(row['efficiency']))
except FileNotFoundError:
    print(f"Error: File not found: {results_file}")
    sys.exit(1)
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

if not data['ranks']:
    print("Error: No data found in file")
    sys.exit(1)

print(f"Loaded {len(data['ranks'])} data points")

# Create figure with 3 subplots
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Plot 1: Execution Time
ax = axes[0]
ax.plot(data['ranks'], data['time'], 'o-', linewidth=2, markersize=8, color='#2E86AB')
ax.set_xlabel('Number of Processes', fontsize=12, fontweight='bold')
ax.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
ax.set_title('Execution Time', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xticks(data['ranks'])

# Add values on points
for i, (x, y) in enumerate(zip(data['ranks'], data['time'])):
    ax.annotate(f'{y:.1f}s', (x, y), textcoords="offset points", 
                xytext=(0,10), ha='center', fontsize=9)

# Plot 2: Speedup
ax = axes[1]
ax.plot(data['ranks'], data['speedup'], 'o-', linewidth=2, markersize=8, 
        color='#A23B72', label='Actual Speedup')
ax.plot(data['ranks'], data['ranks'], '--', linewidth=2, alpha=0.6, 
        color='#F18F01', label='Ideal Speedup')
ax.set_xlabel('Number of Processes', fontsize=12, fontweight='bold')
ax.set_ylabel('Speedup', fontsize=12, fontweight='bold')
ax.set_title('Speedup vs Processes', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xticks(data['ranks'])

# Add values on points
for i, (x, y) in enumerate(zip(data['ranks'], data['speedup'])):
    ax.annotate(f'{y:.1f}×', (x, y), textcoords="offset points", 
                xytext=(0,10), ha='center', fontsize=9)

# Plot 3: Parallel Efficiency
ax = axes[2]
ax.plot(data['ranks'], data['efficiency'], 'o-', linewidth=2, markersize=8, color='#C73E1D')
ax.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Ideal (100%)')
ax.axhline(y=80, color='orange', linestyle=':', linewidth=1, alpha=0.5, label='Good (80%)')
ax.set_xlabel('Number of Processes', fontsize=12, fontweight='bold')
ax.set_ylabel('Parallel Efficiency (%)', fontsize=12, fontweight='bold')
ax.set_title('Parallel Efficiency', fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xticks(data['ranks'])
ax.set_ylim(0, 110)

# Add values on points
for i, (x, y) in enumerate(zip(data['ranks'], data['efficiency'])):
    ax.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                xytext=(0,10), ha='center', fontsize=9)

plt.tight_layout()

# Save figure
output_file = f"{output_prefix}_plot.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"✓ Saved plot: {output_file}")

# Print summary
print("\n" + "="*60)
print("Performance Summary:")
print("="*60)
print(f"{'Ranks':>8} {'Time (s)':>12} {'Speedup':>10} {'Efficiency':>12}")
print("-"*60)
for i in range(len(data['ranks'])):
    print(f"{data['ranks'][i]:>8} {data['time'][i]:>12.2f} {data['speedup'][i]:>10.2f}× {data['efficiency'][i]:>11.1f}%")
print("="*60)

# Calculate strong scaling efficiency
if len(data['ranks']) > 1:
    first_eff = data['efficiency'][0]
    last_eff = data['efficiency'][-1]
    eff_drop = first_eff - last_eff
    print(f"\nStrong scaling efficiency drop: {eff_drop:.1f}% (from {data['ranks'][0]} to {data['ranks'][-1]} ranks)")
    
    if last_eff > 80:
        print("✓ Excellent scaling! (>80% efficiency)")
    elif last_eff > 60:
        print("✓ Good scaling (60-80% efficiency)")
    elif last_eff > 40:
        print("⚠ Moderate scaling (40-60% efficiency)")
    else:
        print("⚠ Poor scaling (<40% efficiency)")

