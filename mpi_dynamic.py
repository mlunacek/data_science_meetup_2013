#!/usr/bin/env python
from mpi4py import MPI

import os, sys
from time import sleep
import numpy as np

#import tau


# Create some enumerated types
def enum(**enums):
    return type('Enum', (), enums)

tags = enum(WORK=1, WORK_DONE=2, KILL=3)

def simulator(input_time):
    sleep(input_time)
    # start_time = time.time()
#     index = 0
#     while time.time()-start_time < int(input_time):
#         r1 = random.uniform(0,1)
#         r2 = random.uniform(1,2)
#         r3 = r2 - r1
#         index+=r3
    #print os.uname()[1], time.time()-start_time
    return True

def create_queue(filename):
    import os
    file_in = open(os.path.join(os.getcwd(), filename),'r') 
    line = file_in.readline().rstrip('\n')
    work_queue = []
    while line:
        #print line
        work_queue.append(line)
        line = file_in.readline().rstrip('\n')
    file_in.close()
    return work_queue
    
def create_queue_args(args_jobs, args_time):
   
    work_queue = []
    for i in range(args_jobs):
        work_queue.append(args_time)
        
    return work_queue

#not used right now...
def kill_switch(comm, rank, size):
    if rank == 0:
        requests = [MPI.REQUEST_NULL] * (size-1)
        for r in range(1,size):
            index = r-1
            data = 0
            requests[index] = comm.isend(data, r, tags.KILL)
        MPI.Request.Waitall(requests)        

def load_balance(work_queue, comm, size):
    
    # Send everyone something to do
    requests = [MPI.REQUEST_NULL] * (size-1)
    for r in range(1,size):
        index = r-1
        data = work_queue[index]
        requests[index] = comm.isend(data, r, tags.WORK)
        
    MPI.Request.Waitall(requests)    
    
    status = MPI.Status()
    index = size-1
    while index < len(work_queue):    
        # Receive work
        msg = comm.Probe(MPI.ANY_SOURCE, tag=tags.WORK_DONE, status=status)
        r = status.Get_source()
        data = comm.recv(source=r, tag=tags.WORK_DONE)
        # Send out more work
        data = work_queue[index]
        comm.send(data, dest=r, tag=tags.WORK)
        index += 1
        if index%10000 == 0:
            print index
            sys.stdout.flush()
        
    # Recv extra messages and send kill signal  
    for r in range(1,size):
        msg = comm.Probe(MPI.ANY_SOURCE, tag=tags.WORK_DONE, status=status)
        r = status.Get_source()
        data = comm.recv(source=r, tag=tags.WORK_DONE)
        index = r-1
        data = 0
        requests[index] = comm.isend(data, r, tags.KILL)
        
    MPI.Request.Waitall(requests)

def get_args(argv, size):
    import argparse 
    parser = argparse.ArgumentParser(
                    description='A python MPI load balancer',
                    epilog='monte.lunacek@colorado.edu')
                    
    parser.add_argument('-l', '--lower', type=int, help='lower bound (s)')
    parser.add_argument('-u', '--upper', help='upper bound (s)')
    parser.add_argument('-j', '--jobs', help='number of jobs')
    parser.set_defaults(jobs=10*int(size))
    
    return parser.parse_args(argv)
                
def master(comm, rank, size):
    
    #print 'rank', rank
    import sys
    args = get_args(sys.argv[1:], size)
    #print args
    np.random.seed(1045)
    work_queue = np.random.uniform(float(args.lower), float(args.upper), int(args.jobs))
    #print work_queue
    t_start = MPI.Wtime()
    load_balance(work_queue, comm, size)  
    t_end = MPI.Wtime()
    
    data = {}
    data['jobs'] = len(work_queue)
    data['LB time'] = (t_end - t_start) 
    
    return data

def worker(comm, rank, size):

    while True:
        status = MPI.Status()
        msg = comm.Probe(0, MPI.ANY_TAG, status=status)
        if status.Get_tag() == tags.WORK:
            data = comm.recv(source=0, tag=tags.WORK)
            simulator(data)
            tmp = 1
            comm.send(tmp, dest=0, tag=tags.WORK_DONE)
        
        if status.Get_tag() == tags.KILL:
            data = comm.recv(source=0, tag=tags.KILL)
            done = True
            break

def main():
    
    t_start = MPI.Wtime()
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    if rank == 0:
        data = master(comm, rank, size)
    else:
        worker(comm, rank, size)
    
    comm.Barrier()
    t_end = MPI.Wtime()
        
    if rank == 0:
        print size, data['jobs'], (t_end - t_start) 

if __name__ == '__main__':
    main()

    
    
    
    
    
    
    
    
    
    
    
    