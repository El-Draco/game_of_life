from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nprocs = comm.Get_size()
name = MPI.Get_processor_name()

print('Hello, I am process number {} of {} running on {}'.format(rank, nprocs, name))