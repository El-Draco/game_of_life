from mpi4py import MPI
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nprocs = comm.Get_size()
name = MPI.Get_processor_name()

next_process = rank + 1
previous_process = rank - 1
if rank == nprocs - 1: #Last process will send data to process 0
    next_process = 0
if rank == 0:
    previous_process = nprocs - 1
        
if rank == 0:
    print('Number of processes = {}'.format(nprocs))
    data = 0
    comm.send(data, dest=next_process)
    print('Process {} on {} sends data = {} to process {}'.format(rank, name, data, next_process))
    
    data = comm.recv(source=previous_process)
    print('Process {} on {} receives final result = {} from process {}'.format(rank, name, data, previous_process))
else:  
    data = comm.recv(source=rank-1)
    print('Process {} on {} receives data = {} from process {}'.format(rank, name, data, previous_process))

    print('Process {} on {} updates data ({} + {} = {})...'.format(rank, name, data, rank, data+rank))    
    data = data + rank
    time.sleep(2)
    
    comm.send(data, dest=next_process)
    print('Process {} on {} sends (new) data = {} to process {}\n'.format(rank, name, data, next_process))