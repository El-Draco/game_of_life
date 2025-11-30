#!/usr/bin/env python3
"""
Parallel Conway's Game of Life using MPI (mpi4py)
SIMULATION ONLY - No visualization (for fast HPC runs)
Saves binary snapshots for post-processing visualization
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


def compute_next_generation(local_grid, nx):
    """
    Compute next generation for local subgrid.
    local_grid includes halo rows (top and bottom).
    Returns new local grid without halo rows.
    """
    local_rows = local_grid.shape[0] - 2
    next_gen = np.zeros((local_rows, nx), dtype=np.int8)
    
    for i in range(1, local_grid.shape[0] - 1):
        for j in range(nx):
            neighbors = 0
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    ni = i + di
                    nj = (j + dj) % nx
                    neighbors += local_grid[ni, nj]
            
            next_gen[i-1, j] = update_cell(local_grid[i, j], neighbors)
    
    return next_gen


def exchange_halo(local_grid, comm, rank, size, nx):
    """
    Exchange halo rows with neighboring processes.
    Non-blocking communication for performance.
    """
    local_rows_total = local_grid.shape[0]
    local_rows_real = local_rows_total - 2
    
    top_neighbor = (rank - 1) % size
    bottom_neighbor = (rank + 1) % size
    
    top_real_row = local_grid[1, :].copy()
    bottom_real_row = local_grid[local_rows_real, :].copy()
    
    recv_buf_top = np.zeros(nx, dtype=np.int8)
    recv_buf_bottom = np.zeros(nx, dtype=np.int8)
    
    reqs = []
    reqs.append(comm.Irecv(recv_buf_top, source=top_neighbor, tag=0))
    reqs.append(comm.Irecv(recv_buf_bottom, source=bottom_neighbor, tag=1))
    reqs.append(comm.Isend(bottom_real_row, dest=bottom_neighbor, tag=0))
    reqs.append(comm.Isend(top_real_row, dest=top_neighbor, tag=1))
    
    MPI.Request.Waitall(reqs)
    
    local_grid[0, :] = recv_buf_top
    local_grid[local_rows_total - 1, :] = recv_buf_bottom
    
    return local_grid


def gather_grid(local_grid, comm, rank, size, ny, nx):
    """Gather local subgrids from all ranks to reconstruct the global grid."""
    local_rows = local_grid.shape[0] - 2
    local_data = local_grid[1:local_rows+1, :].flatten()
    
    rows_per_rank = ny // size
    remainder = ny % size
    
    recv_counts = []
    displacements = []
    offset = 0
    
    for r in range(size):
        row_count = (rows_per_rank + 1) if r < remainder else rows_per_rank
        recv_counts.append(row_count * nx)
        displacements.append(offset)
        offset += row_count * nx
    
    if rank == 0:
        global_flat = np.zeros(ny * nx, dtype=np.int8)
        comm.Gatherv(
            sendbuf=local_data,
            recvbuf=[global_flat, recv_counts, displacements, MPI.INT8_T],
            root=0
        )
        return global_flat.reshape(ny, nx)
    else:
        comm.Gatherv(sendbuf=local_data, recvbuf=None, root=0)
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
    """Main simulation function."""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    args = parse_args()
    
    # Only rank 0 initializes the full grid
    if rank == 0:
        global_grid = initialize_grid(args.nx, args.ny, args.pattern, args.seed)
        print(f"Initialized {args.pattern} pattern on {args.nx}x{args.ny} grid")
        print(f"Running with {size} MPI processes for {args.steps} steps")
        if args.save_interval > 0:
            print(f"Saving snapshots to '{args.output_dir}/' every {args.save_interval} steps")
    else:
        global_grid = None
    
    # Broadcast grid dimensions
    if rank == 0:
        dims = np.array([args.ny, args.nx], dtype=np.int32)
    else:
        dims = np.array([0, 0], dtype=np.int32)
    
    comm.Bcast(dims, root=0)
    ny, nx = dims[0], dims[1]
    
    # Calculate distribution
    rows_per_rank = ny // size
    remainder = ny % size
    
    send_counts = []
    displacements = []
    offset = 0
    
    for r in range(size):
        row_count = (rows_per_rank + 1) if r < remainder else rows_per_rank
        send_counts.append(row_count * nx)
        displacements.append(offset)
        offset += row_count * nx
    
    # Prepare local receive buffer
    if rank < remainder:
        local_rows = rows_per_rank + 1
    else:
        local_rows = rows_per_rank
    
    local_data = np.zeros(local_rows * nx, dtype=np.int8)
    
    # Scatter the grid
    if rank == 0:
        global_flat = global_grid.flatten()
        comm.Scatterv(
            [global_flat, send_counts, displacements, MPI.INT8_T],
            local_data,
            root=0
        )
    else:
        comm.Scatterv(
            [None, send_counts, displacements, MPI.INT8_T],
            local_data,
            root=0
        )
    
    # Reshape and add halo rows
    local_grid_2d = local_data.reshape(local_rows, nx)
    local_grid = np.zeros((local_rows + 2, nx), dtype=np.int8)
    local_grid[1:local_rows+1, :] = local_grid_2d
    
    # Initial halo exchange
    local_grid = exchange_halo(local_grid, comm, rank, size, nx)
    
    # Save initial state
    if rank == 0 and args.save_interval > 0:
        initial_grid = gather_grid(local_grid, comm, rank, size, ny, nx)
        save_snapshot(initial_grid, 0, args.output_dir, 
                     metadata={'nx': nx, 'ny': ny, 'pattern': args.pattern, 'seed': args.seed})
    elif args.save_interval > 0:
        # All ranks must participate in gather
        gather_grid(local_grid, comm, rank, size, ny, nx)
    
    # Main simulation loop
    if rank == 0:
        start_time = time.time()
    
    for step in range(args.steps):
        # Compute next generation
        next_gen = compute_next_generation(local_grid, nx)
        
        # Update local grid
        local_grid[1:local_rows+1, :] = next_gen
        
        # Exchange halo for next iteration
        if step < args.steps - 1:
            local_grid = exchange_halo(local_grid, comm, rank, size, nx)
        
        # Save snapshot at intervals
        if args.save_interval > 0 and (step + 1) % args.save_interval == 0:
            frame_grid = gather_grid(local_grid, comm, rank, size, ny, nx)
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
    final_grid = gather_grid(local_grid, comm, rank, size, ny, nx)
    
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

