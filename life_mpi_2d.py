#!/usr/bin/env python3
"""
Parallel Conway's Game of Life using MPI (mpi4py) - 2D DECOMPOSITION
SIMULATION ONLY - No visualization (for fast HPC runs)
Saves binary snapshots for post-processing visualization

2-D Decomposition: Grid split into rectangular patches
Each rank handles a subgrid with halo cells on all 4 sides
Communicates with 8 neighbors (N, S, E, W, NE, NW, SE, SW)
"""

import argparse
import time
import os
import numpy as np
from mpi4py import MPI


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Parallel Conway's Game of Life using MPI (Simulation Only)"
    )
    parser.add_argument(
        "--nx", type=int, default=16384,
        help="Grid width (default: 16384)"
    )
    parser.add_argument(
        "--ny", type=int, default=16384,
        help="Grid height (default: 16384)"
    )
    parser.add_argument(
        "--steps", type=int, default=2000,
        help="Number of generations (default: 2000)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for initial state (default: 42)"
    )
    parser.add_argument(
        "--pattern", type=str, default="glider_gun",
        choices=["glider_gun", "random", "glider", "r_pentomino"],
        help="Initial pattern (default: glider_gun)"
    )
    parser.add_argument(
        "--decomp", type=str, default="2d",
        choices=["2d"],
        help="Decomposition strategy: '2d' for 2-D decomposition (default: 2d)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="snapshots",
        help="Directory to save snapshots (default: snapshots)"
    )
    parser.add_argument(
        "--save-interval", type=int, default=100,
        help="Save snapshot every N steps (default: 100). Set to 0 to save only final state"
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Output timing statistics in machine-readable format"
    )
    return parser.parse_args()


def create_glider_gun(grid, start_x=0, start_y=0):
    """Create a Gosper Glider Gun pattern (36x9)."""
    gun_pattern = np.array([
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ], dtype=np.int8)
    
    for i in range(gun_pattern.shape[0]):
        for j in range(gun_pattern.shape[1]):
            y = (start_y + i) % grid.shape[0]
            x = (start_x + j) % grid.shape[1]
            grid[y, x] = gun_pattern[i, j]


def create_glider(grid, start_x=0, start_y=0):
    """Create a simple glider pattern (3x3)."""
    glider = np.array([[0,1,0],[0,0,1],[1,1,1]], dtype=np.int8)
    for i in range(3):
        for j in range(3):
            y = (start_y + i) % grid.shape[0]
            x = (start_x + j) % grid.shape[1]
            grid[y, x] = glider[i, j]


def create_r_pentomino(grid, start_x=0, start_y=0):
    """Create an R-pentomino pattern (3x3)."""
    r_pentomino = np.array([[0,1,1],[1,1,0],[0,1,0]], dtype=np.int8)
    for i in range(3):
        for j in range(3):
            y = (start_y + i) % grid.shape[0]
            x = (start_x + j) % grid.shape[1]
            grid[y, x] = r_pentomino[i, j]


def initialize_grid(nx, ny, pattern="glider_gun", seed=42):
    """Initialize the global grid with a pattern."""
    np.random.seed(seed)
    grid = np.zeros((ny, nx), dtype=np.int8)
    
    if pattern == "random":
        grid = np.random.choice([0, 1], size=(ny, nx), p=[0.9, 0.1]).astype(np.int8)
    elif pattern == "glider_gun":
        create_glider_gun(grid, start_x=max(20, nx//4), start_y=max(20, ny//4))
    elif pattern == "glider":
        create_glider(grid, start_x=max(10, nx//2), start_y=max(10, ny//2))
    elif pattern == "r_pentomino":
        create_r_pentomino(grid, start_x=max(10, nx//2), start_y=max(10, ny//2))
    
    return grid


def update_cell(current, neighbors):
    """Apply Conway's Game of Life rules (B3/S23)."""
    if current == 1:
        return 1 if (neighbors == 2 or neighbors == 3) else 0
    else:
        return 1 if neighbors == 3 else 0


def compute_next_generation_2d(local_grid):
    """
    Compute next generation for 2-D decomposition.
    local_grid includes halo cells on all four sides.
    Returns new local grid without halo cells.
    """
    local_rows = local_grid.shape[0] - 2
    local_cols = local_grid.shape[1] - 2
    next_gen = np.zeros((local_rows, local_cols), dtype=np.int8)
    
    for i in range(1, local_grid.shape[0] - 1):
        for j in range(1, local_grid.shape[1] - 1):
            neighbors = 0
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    neighbors += local_grid[i + di, j + dj]
            
            next_gen[i-1, j-1] = update_cell(local_grid[i, j], neighbors)
    
    return next_gen


def exchange_halo_2d(local_grid, cart_comm, coords, dims):
    """
    Exchange halo cells with 8 neighbors in 2-D decomposition.
    Uses cartesian topology for neighbor finding.
    Non-blocking communication for performance.
    """
    local_rows = local_grid.shape[0] - 2
    local_cols = local_grid.shape[1] - 2
    
    # Get neighbors from cartesian topology
    north, south = cart_comm.Shift(0, 1)
    west, east = cart_comm.Shift(1, 1)
    
    # Diagonal neighbors
    nw = cart_comm.Get_cart_rank(((coords[0] - 1) % dims[0], (coords[1] - 1) % dims[1]))
    ne = cart_comm.Get_cart_rank(((coords[0] - 1) % dims[0], (coords[1] + 1) % dims[1]))
    sw = cart_comm.Get_cart_rank(((coords[0] + 1) % dims[0], (coords[1] - 1) % dims[1]))
    se = cart_comm.Get_cart_rank(((coords[0] + 1) % dims[0], (coords[1] + 1) % dims[1]))
    
    # Prepare send buffers (interior data)
    north_row = local_grid[1, 1:local_cols+1].copy()
    south_row = local_grid[local_rows, 1:local_cols+1].copy()
    west_col = local_grid[1:local_rows+1, 1].copy()
    east_col = local_grid[1:local_rows+1, local_cols].copy()
    
    nw_cell = np.array([local_grid[1, 1]], dtype=np.int8)
    ne_cell = np.array([local_grid[1, local_cols]], dtype=np.int8)
    sw_cell = np.array([local_grid[local_rows, 1]], dtype=np.int8)
    se_cell = np.array([local_grid[local_rows, local_cols]], dtype=np.int8)
    
    # Prepare receive buffers
    recv_north = np.zeros(local_cols, dtype=np.int8)
    recv_south = np.zeros(local_cols, dtype=np.int8)
    recv_west = np.zeros(local_rows, dtype=np.int8)
    recv_east = np.zeros(local_rows, dtype=np.int8)
    recv_nw = np.zeros(1, dtype=np.int8)
    recv_ne = np.zeros(1, dtype=np.int8)
    recv_sw = np.zeros(1, dtype=np.int8)
    recv_se = np.zeros(1, dtype=np.int8)
    
    # Non-blocking communication
    reqs = []
    
    # Post receives first
    reqs.append(cart_comm.Irecv(recv_north, source=north, tag=0))
    reqs.append(cart_comm.Irecv(recv_south, source=south, tag=1))
    reqs.append(cart_comm.Irecv(recv_west, source=west, tag=2))
    reqs.append(cart_comm.Irecv(recv_east, source=east, tag=3))
    reqs.append(cart_comm.Irecv(recv_nw, source=nw, tag=4))
    reqs.append(cart_comm.Irecv(recv_ne, source=ne, tag=5))
    reqs.append(cart_comm.Irecv(recv_sw, source=sw, tag=6))
    reqs.append(cart_comm.Irecv(recv_se, source=se, tag=7))
    
    # Then send
    reqs.append(cart_comm.Isend(south_row, dest=south, tag=0))
    reqs.append(cart_comm.Isend(north_row, dest=north, tag=1))
    reqs.append(cart_comm.Isend(east_col, dest=east, tag=2))
    reqs.append(cart_comm.Isend(west_col, dest=west, tag=3))
    reqs.append(cart_comm.Isend(se_cell, dest=se, tag=4))
    reqs.append(cart_comm.Isend(sw_cell, dest=sw, tag=5))
    reqs.append(cart_comm.Isend(ne_cell, dest=ne, tag=6))
    reqs.append(cart_comm.Isend(nw_cell, dest=nw, tag=7))
    
    MPI.Request.Waitall(reqs)
    
    # Update halo cells
    local_grid[0, 1:local_cols+1] = recv_north
    local_grid[local_rows+1, 1:local_cols+1] = recv_south
    local_grid[1:local_rows+1, 0] = recv_west
    local_grid[1:local_rows+1, local_cols+1] = recv_east
    local_grid[0, 0] = recv_nw[0]
    local_grid[0, local_cols+1] = recv_ne[0]
    local_grid[local_rows+1, 0] = recv_sw[0]
    local_grid[local_rows+1, local_cols+1] = recv_se[0]
    
    return local_grid


def gather_grid_2d(local_grid, cart_comm, dims, ny, nx):
    """Gather local subgrids from all ranks to reconstruct the global grid (2-D)."""
    rank = cart_comm.Get_rank()
    size = cart_comm.Get_size()
    
    # Extract interior cells (without halo)
    local_rows = local_grid.shape[0] - 2
    local_cols = local_grid.shape[1] - 2
    local_data = local_grid[1:local_rows+1, 1:local_cols+1].copy()
    
    # Gather to rank 0
    if rank == 0:
        # Calculate how grid is distributed
        rows_per_proc = ny // dims[0]
        cols_per_proc = nx // dims[1]
        row_remainder = ny % dims[0]
        col_remainder = nx % dims[1]
        
        global_grid = np.zeros((ny, nx), dtype=np.int8)
        
        # Receive from each rank
        for proc_row in range(dims[0]):
            for proc_col in range(dims[1]):
                nrows = (rows_per_proc + 1) if proc_row < row_remainder else rows_per_proc
                ncols = (cols_per_proc + 1) if proc_col < col_remainder else cols_per_proc
                
                target_rank = cart_comm.Get_cart_rank((proc_row, proc_col))
                
                if target_rank == 0:
                    patch = local_data
                else:
                    patch = np.zeros((nrows, ncols), dtype=np.int8)
                    cart_comm.Recv(patch, source=target_rank, tag=99)
                
                row_start = sum([(rows_per_proc + 1) if r < row_remainder else rows_per_proc 
                                for r in range(proc_row)])
                col_start = sum([(cols_per_proc + 1) if c < col_remainder else cols_per_proc 
                                for c in range(proc_col)])
                
                global_grid[row_start:row_start+nrows, col_start:col_start+ncols] = patch
        
        return global_grid
    else:
        cart_comm.Send(local_data, dest=0, tag=99)
        return None


def save_snapshot(grid, step, output_dir, metadata=None):
    """Save grid snapshot as compressed numpy file."""
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"step_{step:06d}.npz")
    
    if metadata:
        np.savez_compressed(filename, grid=grid, **metadata)
    else:
        np.savez_compressed(filename, grid=grid)
    
    return filename


def main():
    """Main simulation function with 2-D decomposition."""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    args = parse_args()
    ny, nx = args.ny, args.nx
    
    # Create 2-D cartesian topology
    dims = MPI.Compute_dims(size, [0, 0])  # Let MPI decide balanced dimensions
    cart_comm = comm.Create_cart(dims, periods=[True, True], reorder=True)
    cart_rank = cart_comm.Get_rank()
    coords = cart_comm.Get_coords(cart_rank)
    
    # Only rank 0 initializes the full grid
    if rank == 0:
        global_grid = initialize_grid(nx, ny, args.pattern, args.seed)
        print(f"Initialized {args.pattern} pattern on {nx}x{ny} grid")
        print(f"Running with {size} MPI processes ({dims[0]}x{dims[1]} grid) for {args.steps} steps")
        print(f"Decomposition: 2-D (8 neighbors per rank)")
        if args.save_interval > 0:
            print(f"Saving snapshots to '{args.output_dir}/' every {args.save_interval} steps")
    else:
        global_grid = None
    
    # Calculate 2-D distribution
    rows_per_proc = ny // dims[0]
    cols_per_proc = nx // dims[1]
    row_remainder = ny % dims[0]
    col_remainder = nx % dims[1]
    
    # My local dimensions
    local_rows = (rows_per_proc + 1) if coords[0] < row_remainder else rows_per_proc
    local_cols = (cols_per_proc + 1) if coords[1] < col_remainder else cols_per_proc
    
    # Calculate my starting position in global grid
    my_row_start = sum([(rows_per_proc + 1) if r < row_remainder else rows_per_proc 
                        for r in range(coords[0])])
    my_col_start = sum([(cols_per_proc + 1) if c < col_remainder else cols_per_proc 
                        for c in range(coords[1])])
    
    # Distribute grid from rank 0
    if rank == 0:
        # Send patches to all ranks
        for proc_row in range(dims[0]):
            for proc_col in range(dims[1]):
                nrows = (rows_per_proc + 1) if proc_row < row_remainder else rows_per_proc
                ncols = (cols_per_proc + 1) if proc_col < col_remainder else cols_per_proc
                
                row_start = sum([(rows_per_proc + 1) if r < row_remainder else rows_per_proc 
                                for r in range(proc_row)])
                col_start = sum([(cols_per_proc + 1) if c < col_remainder else cols_per_proc 
                                for c in range(proc_col)])
                
                patch = global_grid[row_start:row_start+nrows, col_start:col_start+ncols].copy()
                
                target_rank = cart_comm.Get_cart_rank((proc_row, proc_col))
                if target_rank == 0:
                    local_data = patch
                else:
                    cart_comm.Send(patch, dest=target_rank, tag=0)
    else:
        local_data = np.zeros((local_rows, local_cols), dtype=np.int8)
        cart_comm.Recv(local_data, source=0, tag=0)
    
    # Add halo cells (all four sides)
    local_grid = np.zeros((local_rows + 2, local_cols + 2), dtype=np.int8)
    local_grid[1:local_rows+1, 1:local_cols+1] = local_data
    
    # Initial halo exchange
    local_grid = exchange_halo_2d(local_grid, cart_comm, coords, dims)
    
    # Save initial state
    if args.save_interval > 0:
        initial_grid = gather_grid_2d(local_grid, cart_comm, dims, ny, nx)
        if rank == 0:
            save_snapshot(initial_grid, 0, args.output_dir, 
                         metadata={'nx': nx, 'ny': ny, 'pattern': args.pattern, 'seed': args.seed})
    
    # Main simulation loop
    if rank == 0:
        start_time = time.time()
    
    for step in range(args.steps):
        # Compute next generation
        next_gen = compute_next_generation_2d(local_grid)
        
        # Update local grid
        local_grid[1:local_rows+1, 1:local_cols+1] = next_gen
        
        # Exchange halo for next iteration
        if step < args.steps - 1:
            local_grid = exchange_halo_2d(local_grid, cart_comm, coords, dims)
        
        # Save snapshot at intervals
        if args.save_interval > 0 and (step + 1) % args.save_interval == 0:
            frame_grid = gather_grid_2d(local_grid, cart_comm, dims, ny, nx)
            if rank == 0:
                save_snapshot(frame_grid, step + 1, args.output_dir)
    
    # Synchronize
    comm.Barrier()
    
    if rank == 0:
        elapsed_time = time.time() - start_time
        
        if args.benchmark:
            print(f"BENCHMARK: ranks={size}, grid={nx}x{ny}, steps={args.steps}, time={elapsed_time:.6f}, time_per_step={elapsed_time/args.steps if args.steps > 0 else 0:.6f}")
        else:
            print(f"\nCompleted {args.steps} steps in {elapsed_time:.4f} seconds")
            if args.steps > 0:
                print(f"Average time per step: {elapsed_time/args.steps*1000:.4f} ms")
    
    # Gather final grid
    final_grid = gather_grid_2d(local_grid, cart_comm, dims, ny, nx)
    
    if rank == 0:
        checksum = np.sum(final_grid)
        alive_cells = np.sum(final_grid)
        
        if args.benchmark:
            print(f"BENCHMARK: checksum={checksum}, alive_cells={alive_cells}")
        else:
            print(f"Final checksum: {checksum}")
            print(f"Alive cells: {alive_cells} ({100.0*alive_cells/(nx*ny):.2f}%)")
        
        # Save final state
        save_snapshot(final_grid, args.steps, args.output_dir,
                     metadata={'checksum': int(checksum), 'alive_cells': int(alive_cells),
                              'elapsed_time': elapsed_time})
        
        if not args.benchmark:
            print(f"\nSnapshots saved to: {args.output_dir}/")
            print(f"Use visualize.py to create animations from snapshots")


if __name__ == "__main__":
    main()

