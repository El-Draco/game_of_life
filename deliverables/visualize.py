#!/usr/bin/env python3
"""
Post-processing visualization for Game of Life snapshots
EXPANDING VIEW - Zooms out smoothly as patterns grow
Perfect for large-scale HPC simulations (4K+, 8K+, 16K+ grids)

Usage:
    python visualize.py --input-dir snapshots_8nodes --output animation.gif --fps 10
    
For heatmaps, use visualize_local.py instead.
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize Game of Life snapshots with expanding view"
    )
    parser.add_argument("--input-dir", type=str, default="hpc_snapshots",
                       help="Directory containing snapshots")
    parser.add_argument("--output", type=str, required=True,
                       help="Output filename (e.g., animation.gif)")
    parser.add_argument("--fps", type=int, default=10,
                       help="Animation FPS (default: 10)")
    parser.add_argument("--initial-size", type=int, default=400,
                       help="Initial zoom window size (default: 400)")
    parser.add_argument("--max-size", type=int, default=2000,
                       help="Maximum zoom window size (default: 2000)")
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


def get_active_bbox(grid, padding=20):
    """Get bounding box of active (alive) cells with padding."""
    alive_coords = np.argwhere(grid > 0)
    
    if len(alive_coords) == 0:
        ny, nx = grid.shape
        return ny//2 - 50, ny//2 + 50, nx//2 - 50, nx//2 + 50
    
    min_y, min_x = alive_coords.min(axis=0)
    max_y, max_x = alive_coords.max(axis=0)
    
    ny, nx = grid.shape
    min_y = max(0, min_y - padding)
    max_y = min(ny, max_y + padding)
    min_x = max(0, min_x - padding)
    max_x = min(nx, max_x + padding)
    
    return min_y, max_y, min_x, max_x


def create_expanding_animation(snapshots, output_file, fps=10, 
                               initial_size=400, max_size=2000):
    """
    Create animated GIF that starts zoomed in and smoothly expands
    as the pattern grows.
    """
    if not HAS_PIL:
        print("Error: PIL required for GIF creation")
        return False
    
    print(f"Creating expanding view animation with {len(snapshots)} frames...")
    print(f"  Initial view: {initial_size}×{initial_size}")
    print(f"  Maximum view: {max_size}×{max_size}")
    
    _, full_grid = snapshots[0]
    full_ny, full_nx = full_grid.shape
    
    # Analyze all frames to determine required view sizes
    print("  Analyzing pattern growth...")
    required_sizes = []
    for _, grid in snapshots:
        min_y, max_y, min_x, max_x = get_active_bbox(grid, padding=80)
        height = max_y - min_y
        width = max_x - min_x
        required_size = max(height, width)
        required_sizes.append(required_size)
    
    # Smooth out the size progression (monotonically increasing)
    view_sizes = [initial_size]
    for req_size in required_sizes[1:]:
        # Gradually increase, never decrease
        new_size = max(view_sizes[-1], min(req_size, view_sizes[-1] + 50))
        new_size = min(new_size, max_size)
        view_sizes.append(new_size)
    
    print(f"  View size range: {min(view_sizes)}px → {max(view_sizes)}px")
    
    # Fixed output image size for consistent frames
    output_size = 2400
    
    images = []
    for idx, ((filename, grid), view_size) in enumerate(zip(snapshots, view_sizes)):
        step = int(os.path.basename(filename).split('_')[1].split('.')[0])
        
        # Get active region
        bbox_min_y, bbox_max_y, bbox_min_x, bbox_max_x = get_active_bbox(grid, padding=60)
        
        # Center view on active region
        center_y = (bbox_min_y + bbox_max_y) // 2
        center_x = (bbox_min_x + bbox_max_x) // 2
        
        half_size = int(view_size // 2)
        min_y = max(0, center_y - half_size)
        max_y = min(full_ny, center_y + half_size)
        min_x = max(0, center_x - half_size)
        max_x = min(full_nx, center_x + half_size)
        
        # Extract and scale (white background, black cells)
        zoomed_grid = grid[min_y:max_y, min_x:max_x]
        img_data = (1 - zoomed_grid).astype(np.uint8) * 255
        
        # Scale to fixed output size
        ny, nx = zoomed_grid.shape
        if ny > 0 and nx > 0:
            scale_y = output_size / ny
            scale_x = output_size / nx
            scale = int(min(scale_y, scale_x))
            scale = max(1, scale)
            
            img_data = np.repeat(np.repeat(img_data, scale, axis=0), scale, axis=1)
        
        # Convert to PIL
        img = Image.fromarray(img_data, mode='L')
        
        # Pad to fixed size with white background
        final_img = Image.new('L', (output_size, output_size), color=255)
        paste_x = (output_size - img.width) // 2
        paste_y = (output_size - img.height) // 2
        final_img.paste(img, (paste_x, paste_y))
        
        # Add info overlay
        draw = ImageDraw.Draw(final_img)
        alive_count = np.sum(grid)
        zoom_pct = (view_size * view_size) / (full_ny * full_nx) * 100
        
        info_text = f"Step {step} | {alive_count} cells | View: {view_size}×{view_size} ({zoom_pct:.1f}%)"
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=36)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), info_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        draw.rectangle([(10, 10), (text_width + 30, text_height + 30)], 
                      fill='white', outline='black', width=3)
        draw.text((20, 20), info_text, fill='black', font=font)
        
        images.append(final_img)
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(snapshots)} frames...")
    
    # Save GIF
    duration_ms = int(1000 / fps)
    images[0].save(
        output_file,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0
    )
    
    print(f"Saved expanding animation: {output_file}")
    return True




def main():
    args = parse_args()
    
    snapshots = load_snapshots(args.input_dir)
    if not snapshots:
        return
    
    create_expanding_animation(snapshots, args.output, args.fps, 
                              args.initial_size, args.max_size)


if __name__ == "__main__":
    main()
