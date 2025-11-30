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
    from PIL import Image, ImageDraw, ImageFont
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
    parser.add_argument("--min-alive", type=int, default=1,
                       help="Trim trailing frames whose alive cells <= this value (default: 1)")
    parser.add_argument("--no-zoom", action="store_true",
                       help="Disable auto-zoom to active regions")
    return parser.parse_args()


def load_snapshots(input_dir):
    """Load all snapshots from directory."""
    pattern = os.path.join(input_dir, "step_*.npz")
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"Error: No snapshots found in {input_dir}/")
        return None
    
    snapshots = []
    alive_counts = []
    for f in files:
        data = np.load(f)
        grid = data['grid']
        snapshots.append((f, grid))
        alive_counts.append(int(np.sum(grid)))
    
    print(f"Loaded {len(snapshots)} snapshots from {input_dir}/")
    return snapshots, alive_counts


def trim_inactive_tail(snapshots, alive_counts, min_alive):
    """Trim trailing frames that have <= min_alive cells."""
    last_active_idx = len(alive_counts) - 1
    while last_active_idx >= 0 and alive_counts[last_active_idx] <= min_alive:
        last_active_idx -= 1
    
    if last_active_idx == len(alive_counts) - 1:
        return snapshots, alive_counts  # nothing trimmed
    
    trimmed = last_active_idx + 1
    if trimmed == 0:
        print("Warning: All frames have <= min-alive cells. Keeping original snapshots.")
        return snapshots, alive_counts
    
    print(f"Trimming {len(snapshots) - trimmed} trailing frames with <= {min_alive} alive cells.")
    return snapshots[:trimmed], alive_counts[:trimmed]


def get_active_bbox(grid, padding=50):
    """Get bounding box of active (alive) cells with padding."""
    alive_coords = np.argwhere(grid > 0)
    
    if len(alive_coords) == 0:
        # No alive cells, return center region
        ny, nx = grid.shape
        return max(0, ny//2 - 100), min(ny, ny//2 + 100), \
               max(0, nx//2 - 100), min(nx, nx//2 + 100)
    
    min_y, min_x = alive_coords.min(axis=0)
    max_y, max_x = alive_coords.max(axis=0)
    
    # Add padding but ensure minimum size for visibility
    ny, nx = grid.shape
    min_y = max(0, min_y - padding)
    max_y = min(ny, max_y + padding)
    min_x = max(0, min_x - padding)
    max_x = min(nx, max_x + padding)
    
    # Ensure minimum region size of at least 200x200 for visibility
    # but cap maximum to 800x800 to avoid too much empty space
    height = max_y - min_y
    width = max_x - min_x
    
    min_size = 200
    max_size = 800
    
    # If too small, expand
    if height < min_size:
        expand = (min_size - height) // 2
        min_y = max(0, min_y - expand)
        max_y = min(ny, max_y + expand)
    
    if width < min_size:
        expand = (min_size - width) // 2
        min_x = max(0, min_x - expand)
        max_x = min(nx, max_x + expand)
    
    # If too large, shrink to max_size
    if height > max_size:
        center_y = (min_y + max_y) // 2
        min_y = max(0, center_y - max_size // 2)
        max_y = min(ny, center_y + max_size // 2)
    
    if width > max_size:
        center_x = (min_x + max_x) // 2
        min_x = max(0, center_x - max_size // 2)
        max_x = min(nx, center_x + max_size // 2)
    
    return min_y, max_y, min_x, max_x


def create_simple_animation(snapshots, alive_counts, output_file, fps=10, auto_zoom=True):
    """Create animated GIF with auto-zoom to active regions."""
    if not HAS_PIL:
        print("Error: PIL required for GIF creation")
        return False
    
    print(f"Creating animation with {len(snapshots)} frames...")
    print(f"Auto-zoom: {'enabled' if auto_zoom else 'disabled'}")
    
    _, full_grid = snapshots[0]
    full_ny, full_nx = full_grid.shape
    
    # For traveling patterns (gliders), use a fixed reasonable size around center of mass
    if auto_zoom:
        print("  Using adaptive zoom following the pattern...")
        # We'll compute per-frame, no fixed bbox
        global_min_y, global_min_x = None, None
        global_max_y, global_max_x = None, None
    else:
        global_min_y, global_min_x = 0, 0
        global_max_y, global_max_x = full_ny, full_nx
    
    # Determine a fixed SIZE to use (to prevent jitter)
    target_region_size = 600  # Fixed size for consistent frames
    
    images = []
    for idx, (filename, grid) in enumerate(snapshots):
        step = int(os.path.basename(filename).split('_')[1].split('.')[0])
        
        # Compute bbox for THIS frame, but use fixed size
        if auto_zoom:
            min_y, max_y, min_x, max_x = get_active_bbox(grid, padding=50)
            
            # Find center of current active region
            center_y = (min_y + max_y) // 2
            center_x = (min_x + max_x) // 2
            
            # Use fixed size window centered on active region
            half_size = target_region_size // 2
            min_y = max(0, center_y - half_size)
            max_y = min(full_ny, center_y + half_size)
            min_x = max(0, center_x - half_size)
            max_x = min(full_nx, center_x + half_size)
            
            # Ensure we actually got the target size
            if (max_y - min_y) < target_region_size:
                if min_y == 0:
                    max_y = min(full_ny, target_region_size)
                else:
                    min_y = max(0, full_ny - target_region_size)
            
            if (max_x - min_x) < target_region_size:
                if min_x == 0:
                    max_x = min(full_nx, target_region_size)
                else:
                    min_x = max(0, full_nx - target_region_size)
        else:
            min_y, min_x = 0, 0
            max_y, max_x = full_ny, full_nx
        
        zoomed_grid = grid[min_y:max_y, min_x:max_x]
        
        # Create image (white=alive, black=dead for better visibility)
        img_data = zoomed_grid.astype(np.uint8) * 255
        
        # Scale up for visibility - fixed target size for smooth animation
        ny, nx = zoomed_grid.shape
        target_size = 2000  # Large size for detail
        scale = max(4, min(20, target_size // max(nx, ny)))
        img_data = np.repeat(np.repeat(img_data, scale, axis=0), scale, axis=1)
        
        # Convert to PIL and add info text
        img = Image.fromarray(img_data, mode='L')
        draw = ImageDraw.Draw(img)
        
        # Add step info
        alive_count = alive_counts[idx] if alive_counts else int(np.sum(grid))
        info_text = f"Step {step} | {alive_count} alive cells"
        if auto_zoom:
            zoom_pct = ((max_y - min_y) * (max_x - min_x)) / (full_ny * full_nx) * 100
            info_text += f" | Zoom: {zoom_pct:.1f}% of grid"
        
        # Draw text background
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=32)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=24)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), info_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        draw.rectangle([(5, 5), (text_width + 15, text_height + 15)], 
                      fill='black', outline='white', width=2)
        draw.text((10, 10), info_text, fill='white', font=font)
        
        images.append(img)
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(snapshots)} frames...")
    
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


def create_rank_heatmap_animation(snapshots, alive_counts, output_file, num_ranks, fps=10):
    """Create animated heatmap showing rank workload distribution."""
    if not HAS_MATPLOTLIB:
        print("Error: matplotlib required for heatmap")
        return False
    
    print(f"Creating rank heatmap animation with {len(snapshots)} frames...")
    
    # Get grid dimensions
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
    
    # Use adaptive zoom with fixed size window
    print("  Using adaptive zoom (follows the pattern)...")
    target_region_size = 800  # Fixed size for heatmap
    
    # Create frames
    temp_frames = []
    heat_grid = np.zeros((ny, nx), dtype=np.float32)
    
    for idx, (filename, grid) in enumerate(snapshots):
        step = int(os.path.basename(filename).split('_')[1].split('.')[0])
        
        # Compute bbox for THIS frame with fixed size window
        bbox_min_y, bbox_max_y, bbox_min_x, bbox_max_x = get_active_bbox(grid, padding=50)
        
        # Center on active region with fixed size
        center_y = (bbox_min_y + bbox_max_y) // 2
        center_x = (bbox_min_x + bbox_max_x) // 2
        
        half_size = target_region_size // 2
        min_y = max(0, center_y - half_size)
        max_y = min(ny, center_y + half_size)
        min_x = max(0, center_x - half_size)
        max_x = min(nx, center_x + half_size)
        
        # Ensure target size
        if (max_y - min_y) < target_region_size:
            if min_y == 0:
                max_y = min(ny, target_region_size)
            else:
                min_y = max(0, ny - target_region_size)
        
        if (max_x - min_x) < target_region_size:
            if min_x == 0:
                max_x = min(nx, target_region_size)
            else:
                min_x = max(0, nx - target_region_size)
        
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
            regional_heat = gaussian_filter(heat_grid, sigma=2.0)
        else:
            regional_heat = heat_grid
        
        # Calculate workloads
        rank_workloads = []
        for start_row, end_row in rank_boundaries:
            alive_cells = np.sum(grid[start_row:end_row, :])
            rank_workloads.append(alive_cells)
        
        total_alive = alive_counts[idx] if alive_counts else int(np.sum(grid))
        workload_percentages = [(w / total_alive) * 100 if total_alive > 0 else 0 
                               for w in rank_workloads]
        
        # Filter active ranks (those with >1% workload)
        active_ranks = [r for r in range(num_ranks) if workload_percentages[r] > 1.0]
        if not active_ranks:
            active_ranks = list(range(num_ranks))
        
        # Create figure with better layout - LARGE for detail
        fig = plt.figure(figsize=(24, 12))
        gs = fig.add_gridspec(2, 3, height_ratios=[1.8, 1], width_ratios=[2.5, 1.5, 1],
                             hspace=0.35, wspace=0.45)
        
        # TOP LEFT: Game of Life (zoomed to active region)
        ax_life = fig.add_subplot(gs[0, 0:2])
        zoomed_life = grid[min_y:max_y, min_x:max_x]
        ax_life.imshow(zoomed_life, cmap='binary', interpolation='nearest')
        ax_life.set_title(f'Game of Life - Step {step} (Active Region)\n' +
                         f'{total_alive} alive cells | {ny}×{nx} grid, {num_ranks} ranks',
                         fontsize=14, fontweight='bold')
        ax_life.set_xlabel('X', fontsize=11)
        ax_life.set_ylabel('Y', fontsize=11)
        ax_life.grid(True, alpha=0.2)
        
        # TOP RIGHT: Workload percentages (large text)
        ax_summary = fig.add_subplot(gs[0, 2])
        ax_summary.axis('off')
        
        summary_text = f"📊 WORKLOAD\n\n"
        for r in active_ranks:
            pct = workload_percentages[r]
            cells = rank_workloads[r]
            bar = "█" * max(1, int(pct / 3))  # 1 block per 3% for better visual
            summary_text += f"R{r:3d}: {bar}\n"
            summary_text += f"      {cells:,} cells\n"
            summary_text += f"      {pct:.1f}%\n\n"
        
        ax_summary.text(0.05, 0.95, summary_text, 
                       transform=ax_summary.transAxes,
                       fontsize=13, fontfamily='monospace', fontweight='bold',
                       verticalalignment='top',
                       bbox=dict(boxstyle='round,pad=0.8', facecolor='wheat', 
                                edgecolor='black', linewidth=2, alpha=0.9))
        
        # BOTTOM LEFT: Heatmap (zoomed to active region)
        ax_heat = fig.add_subplot(gs[1, 0:2])
        zoomed_heat = regional_heat[min_y:max_y, min_x:max_x]
        im = ax_heat.imshow(zoomed_heat, cmap='hot', interpolation='bilinear',
                           aspect='auto', vmin=0, vmax=1.0)
        
        # Draw rank boundaries that are visible in zoomed region
        for r in range(num_ranks):
            start_row, end_row = rank_boundaries[r]
            if min_y <= start_row < max_y:
                ax_heat.axhline(y=start_row - min_y, color='cyan', 
                               linewidth=2, linestyle='--', alpha=0.7)
            
            # Label visible ranks
            if min_y <= start_row < max_y or min_y <= end_row < max_y:
                mid_row = ((start_row + end_row) // 2) - min_y
                if 0 <= mid_row < (max_y - min_y):
                    ax_heat.text(10, mid_row, f"R{r}",
                                ha='left', va='center', fontsize=14, fontweight='bold',
                                color='white',
                                bbox=dict(boxstyle='round,pad=0.5', facecolor='black',
                                         edgecolor='cyan', linewidth=2, alpha=0.9))
        
        cbar = plt.colorbar(im, ax=ax_heat, fraction=0.046, pad=0.04)
        cbar.set_label('Heat (work + communication)', rotation=270, labelpad=20, fontsize=10)
        ax_heat.set_title('Workload Heatmap (Active Region)', fontsize=12, fontweight='bold')
        ax_heat.set_xlabel('X', fontsize=11)
        ax_heat.set_ylabel('Y', fontsize=11)
        
        # BOTTOM RIGHT: Active ranks bar chart
        ax_metrics = fig.add_subplot(gs[1, 2])
        
        if len(active_ranks) > 0:
            active_labels = [f'R{r}' for r in active_ranks][::-1]
            active_workloads = [rank_workloads[r] for r in active_ranks][::-1]
            active_pcts = [workload_percentages[r] for r in active_ranks][::-1]
            colors = plt.cm.hot(np.linspace(0.3, 0.9, len(active_ranks)))[::-1]
            
            bars = ax_metrics.barh(active_labels, active_workloads, color=colors, 
                                   edgecolor='black', linewidth=1.5)
            
            for bar, workload, pct in zip(bars, active_workloads, active_pcts):
                width = bar.get_width()
                if width > 0:
                    label = f'{pct:.0f}%' if pct >= 10 else f'{pct:.1f}%'
                    ax_metrics.text(width * 0.5,
                                   bar.get_y() + bar.get_height()/2,
                                   label,
                                   ha='center', va='center', 
                                   fontsize=11, fontweight='bold', color='white')
            
            ax_metrics.set_xlabel('Alive Cells', fontsize=11, fontweight='bold')
            ax_metrics.set_title(f'Active Ranks ({len(active_ranks)}/{num_ranks})', 
                               fontsize=12, fontweight='bold')
            ax_metrics.grid(axis='x', alpha=0.3)
        else:
            ax_metrics.text(0.5, 0.5, 'No active ranks', 
                          ha='center', va='center', fontsize=12)
            ax_metrics.axis('off')
        
        plt.suptitle(f'Conway\'s Game of Life - MPI Performance Visualization',
                    fontsize=16, fontweight='bold', y=0.98)
        
        temp_file = f"temp_frame_{idx:06d}.png"
        plt.savefig(temp_file, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        temp_frames.append(temp_file)
        
        if (idx + 1) % 5 == 0:
            print(f"  Processed {idx + 1}/{len(snapshots)} frames...")
    
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
    
    loaded = load_snapshots(args.input_dir)
    if not loaded:
        return
    snapshots, alive_counts = loaded
    
    snapshots, alive_counts = trim_inactive_tail(snapshots, alive_counts, args.min_alive)
    if not snapshots:
        print("Error: No snapshots left after trimming.")
        return
    
    if args.show_ranks:
        create_rank_heatmap_animation(snapshots, alive_counts, args.output, args.ranks, args.fps)
    else:
        create_simple_animation(snapshots, alive_counts, args.output, args.fps, 
                               auto_zoom=not args.no_zoom)


if __name__ == "__main__":
    main()
