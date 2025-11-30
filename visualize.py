#!/usr/bin/env python3
"""
Post-processing visualization for Game of Life snapshots
Creates animations and heatmaps from saved simulation data
"""

import argparse
import os
import glob
import numpy as np

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not available. Install with: pip install Pillow")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")

try:
    from scipy.ndimage import gaussian_filter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def parse_args():
    parser = argparse.ArgumentParser(description="Visualize Game of Life snapshots")
    parser.add_argument("--input-dir", type=str, default="snapshots",
                       help="Directory containing snapshots")
    parser.add_argument("--output", type=str, required=True,
                       help="Output filename (e.g., animation.gif or heatmap.gif)")
    parser.add_argument("--fps", type=int, default=10,
                       help="Animation FPS (default: 10)")
    parser.add_argument("--show-ranks", action="store_true",
                       help="Create rank heatmap visualization")
    parser.add_argument("--ranks", type=int, default=4,
                       help="Number of MPI ranks used in simulation (for heatmap)")
    return parser.parse_args()


def load_snapshots(input_dir):
    """Load all snapshots from directory."""
    pattern = os.path.join(input_dir, "step_*.npz")
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"Error: No snapshots found in {input_dir}/")
        return None
    
    snapshots = []
    for f in files:
        data = np.load(f)
        snapshots.append((f, data['grid']))
    
    print(f"Loaded {len(snapshots)} snapshots from {input_dir}/")
    return snapshots


def create_simple_animation(snapshots, output_file, fps=10):
    """Create simple animated GIF from snapshots."""
    if not HAS_PIL:
        print("Error: PIL required for GIF creation")
        return False
    
    print(f"Creating animation with {len(snapshots)} frames...")
    
    images = []
    for _, grid in snapshots:
        # Convert to image (black=alive, white=dead for visibility)
        img_data = (1 - grid.astype(np.int32)) * 255
        img_data = img_data.astype(np.uint8)
        
        # Scale up small grids
        ny, nx = grid.shape
        scale = max(1, min(4, 800 // max(nx, ny)))
        if scale > 1:
            img_data = np.repeat(np.repeat(img_data, scale, axis=0), scale, axis=1)
        
        images.append(Image.fromarray(img_data, mode='L'))
    
    duration_ms = int(1000 / fps)
    images[0].save(
        output_file,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0
    )
    
    print(f"✓ Saved animation: {output_file}")
    return True


def create_rank_heatmap_animation(snapshots, output_file, num_ranks, fps=10):
    """Create animated heatmap showing rank workload distribution."""
    if not HAS_MATPLOTLIB:
        print("Error: matplotlib required for heatmap")
        return False
    
    print(f"Creating rank heatmap animation with {len(snapshots)} frames...")
    
    # Get grid dimensions from first snapshot
    _, first_grid = snapshots[0]
    ny, nx = first_grid.shape
    
    # Calculate rank boundaries
    rows_per_rank = ny // num_ranks
    remainder = ny % num_ranks
    rank_boundaries = []
    current_row = 0
    
    for r in range(num_ranks):
        local_rows = (rows_per_rank + 1) if r < remainder else rows_per_rank
        end_row = current_row + local_rows
        rank_boundaries.append((current_row, end_row))
        current_row = end_row
    
    # Create frames
    temp_frames = []
    heat_grid = np.zeros((ny, nx), dtype=np.float32)
    
    for idx, (filename, grid) in enumerate(snapshots):
        step = int(os.path.basename(filename).split('_')[1].split('.')[0])
        
        # Update heat grid
        heat_grid *= 0.85  # Decay
        heat_grid += grid.astype(np.float32) * 0.3  # Computation heat
        
        # Add communication heat at boundaries
        for r in range(num_ranks):
            start_row, end_row = rank_boundaries[r]
            if start_row > 0:
                heat_grid[start_row, :] += 0.4
            if end_row < ny:
                heat_grid[end_row - 1, :] += 0.4
        
        heat_grid = np.clip(heat_grid, 0, 1.0)
        
        # Blur for visibility
        if HAS_SCIPY:
            regional_heat = gaussian_filter(heat_grid, sigma=3.0)
        else:
            regional_heat = heat_grid
        
        # Calculate workloads
        rank_workloads = []
        for start_row, end_row in rank_boundaries:
            alive_cells = np.sum(grid[start_row:end_row, :])
            rank_workloads.append(alive_cells)
        
        total_alive = np.sum(grid)
        workload_percentages = [(w / total_alive) * 100 if total_alive > 0 else 0 for w in rank_workloads]
        
        # Create figure
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1], hspace=0.35, wspace=0.3)
        
        # TOP: Game of Life
        ax_life = fig.add_subplot(gs[0, :])
        ax_life.imshow(grid, cmap='binary', interpolation='nearest', aspect='equal')
        ax_life.set_title(f'Game of Life - Step {step}\n({ny}×{nx} grid, {num_ranks} ranks)',
                         fontsize=14, fontweight='bold')
        ax_life.set_xlabel('Grid X', fontsize=11)
        ax_life.set_ylabel('Grid Y', fontsize=11)
        ax_life.set_aspect('equal', adjustable='box')
        
        # BOTTOM LEFT: Heatmap
        ax_heat = fig.add_subplot(gs[1, 0])
        im = ax_heat.imshow(regional_heat, cmap='hot', interpolation='bilinear',
                           aspect='equal', vmin=0, vmax=1.0)
        
        for start_row, end_row in rank_boundaries[:-1]:
            ax_heat.axhline(y=end_row - 0.5, color='cyan', linewidth=3, linestyle='--', alpha=0.8)
        
        for r in range(num_ranks):
            start_row, end_row = rank_boundaries[r]
            mid_row = (start_row + end_row) // 2
            ax_heat.text(5, mid_row, f"R{r}",
                        ha='left', va='center', fontsize=13, fontweight='bold',
                        color='white',
                        bbox=dict(boxstyle='round,pad=0.4', facecolor='black',
                                 edgecolor='cyan', linewidth=2, alpha=0.9))
        
        cbar = plt.colorbar(im, ax=ax_heat, fraction=0.046, pad=0.04)
        cbar.set_label('Heat', rotation=270, labelpad=20, fontsize=10)
        ax_heat.set_title('Workload Heatmap', fontsize=12, fontweight='bold')
        ax_heat.set_xlabel('Grid X', fontsize=11)
        ax_heat.set_ylabel('Grid Y', fontsize=11)
        
        # BOTTOM RIGHT: Bar chart
        ax_metrics = fig.add_subplot(gs[1, 1])
        ranks_list = [f'Rank {r}' for r in range(num_ranks)][::-1]
        workloads_rev = rank_workloads[::-1]
        pcts_rev = workload_percentages[::-1]
        colors = plt.cm.hot(np.linspace(0.3, 0.9, num_ranks))[::-1]
        
        bars = ax_metrics.barh(ranks_list, workloads_rev, color=colors, 
                               edgecolor='black', linewidth=1.5)
        
        for bar, workload, pct in zip(bars, workloads_rev, pcts_rev):
            width = bar.get_width()
            if width > 0:
                ax_metrics.text(width + max(rank_workloads) * 0.02,
                               bar.get_y() + bar.get_height()/2,
                               f'{workload} ({pct:.1f}%)',
                               ha='left', va='center', fontsize=10, fontweight='bold')
        
        ax_metrics.set_xlabel('Alive Cells', fontsize=11, fontweight='bold')
        ax_metrics.set_title(f'Load Distribution', fontsize=12, fontweight='bold')
        ax_metrics.grid(axis='x', alpha=0.3)
        
        if total_alive > 0:
            avg_line = total_alive / num_ranks
            ax_metrics.axvline(avg_line, color='green', linestyle='--', 
                              linewidth=2, label=f'Avg: {avg_line:.0f}')
            ax_metrics.legend(fontsize=10)
        
        fig.text(0.5, 0.01,
                f'Total cells: {total_alive} | Cyan lines = rank boundaries',
                ha='center', fontsize=10, style='italic')
        
        plt.subplots_adjust(left=0.08, right=0.95, top=0.94, bottom=0.06, hspace=0.35, wspace=0.3)
        
        temp_file = f"temp_frame_{idx:06d}.png"
        plt.savefig(temp_file, dpi=100, bbox_inches='tight')
        plt.close(fig)
        temp_frames.append(temp_file)
    
    # Create GIF
    if HAS_PIL:
        images = [Image.open(f) for f in temp_frames]
        duration_ms = int(1000 / fps)
        images[0].save(output_file, save_all=True, append_images=images[1:],
                      duration=duration_ms, loop=0)
        
        # Cleanup
        for f in temp_frames:
            os.remove(f)
        
        print(f"✓ Saved heatmap animation: {output_file}")
        return True
    
    return False


def main():
    args = parse_args()
    
    snapshots = load_snapshots(args.input_dir)
    if not snapshots:
        return
    
    if args.show_ranks:
        create_rank_heatmap_animation(snapshots, args.output, args.ranks, args.fps)
    else:
        create_simple_animation(snapshots, args.output, args.fps)


if __name__ == "__main__":
    main()

