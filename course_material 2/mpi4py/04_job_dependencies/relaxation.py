from mpi4py import MPI
import numpy as np
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nprocs = comm.Get_size()
name = MPI.Get_processor_name()
print('Hello, I am process number {} of {} running on {}'.format(rank, nprocs, name))
   
th = 0.0001         #Threshold for convergence
delta = 1           #The maximum difference between it and it-1
nrows = 6           #Number of rows in our matrix of interest (without counting the edges)
ncols = 8           #Number of columns in our matrix of interest (without counting the edges)
kernel = None       #To store the elements submatrix on each
kernel_list = None
mean = None

# Prepare the data
if rank == 0:
    it = 0
    # Mapping processes to matrix elements. Each process will take care of one element (row, col)
    A_map = np.arange(nrows*ncols).reshape(nrows,ncols)
    r_coords, c_coords = np.meshgrid(range(1,nrows+1), range(1, ncols+1), indexing='ij')
    
    #Define the matrix and prepare the edges
    A = np.zeros((nrows+2,ncols+2))
    Az = np.copy(np.atleast_3d(A)) #Store the result of each iteration for plotting
    A[0,:] = np.linspace(-10,10,A.shape[1])
    A[:,0] = np.linspace(-10,10,A.shape[0])
    A[-1,:] = np.linspace(10,-10,A.shape[1])
    A[:,-1] = np.linspace(10,-10,A.shape[0])
    Az = np.append(Az, np.atleast_3d(A), axis=2)

# Main loop
while delta > th:
    # Process 0 prepares the kernel for each process
    if rank == 0:
        kernel_list=[]
        A_new = np.copy(A)
        for proc, row, col in zip(A_map.ravel(), r_coords.ravel(), c_coords.ravel()):
            kernel_list.append(A[row-1:row+2, col-1:col+2])
    # Scatter the kernels
    kernel = comm.scatter(kernel_list, root=0)
    
    # Each process calculate its own kernel's mean
    mean = np.mean(kernel)
    
    # Gather the mean of each kernel in a list
    A_aux = comm.gather(mean, root=0)

    # Process 0 updates the matrix and calculates delta before broadcasting it
    if rank == 0:
        A_aux = np.array(A_aux).reshape(nrows, ncols)
        A_new[1:-1, 1:-1] = A_aux
        delta = np.max(np.abs(A-A_new))
        print('iteration {} -> delta = {}'.format(it,delta))
        it = it + 1
        A = np.copy(A_new)
        Az = np.append(Az, np.atleast_3d(A), axis=2)
        time.sleep(2)
    delta = comm.bcast(delta, root=0)

# Process 0 saves the iteration results on file system    
if rank == 0:
    Az=np.rollaxis(Az,2)
    np.save('Az',Az) 
   
