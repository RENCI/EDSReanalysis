#!/usr/bin/env python
import sys
import random
import time
import numpy as np
import netCDF4 as nc4
import xarray as xr

def main(args):

    f=args.f
    N=args.N
    Screen=args.screen
    Seed=args.seed

    if Seed: random.seed(Seed)

    if Screen: print(f'Screen={Screen}')
    if Screen: print(f'NC File={f}')
    ds=xr.open_dataset(f,drop_variables={'neta','nvel'})
    zeta=ds.zeta

    T=False
    if zeta.dims[0] == 'node':
        T=True
        nnodes, ntimes = zeta.shape
        if Screen: 
            print('file is transposed')
            print(f"Nnodes,Ntimes = {nnodes, ntimes}")
    else:
        ntimes, nnodes = zeta.shape
        if Screen: 
            print('file is NOT transposed')
            print(f"Ntimes,Nnodes = {ntimes,nnodes}")

    Nsamp=np.sort(random.sample(range(0, nnodes),N))
    if Screen: print(Nsamp, " (0-based)")

    overall_start_time = time.time()
    if Screen: 
        print("Starting Loop...\ni     n    shape[0]  time[sec]\n----------------------------------------")
        print(f'Start time = {overall_start_time}')
    inner_dt=[]
    for j,i in enumerate(Nsamp):
        inner_start_time=time.time()
        if T: z=zeta[i,:].values
        else: z=zeta[:,i].values
        inner_end_time=time.time()
        inner_dt.append(inner_end_time-inner_start_time)
        if Screen: 
            temp=inner_dt[-1]
            print(f'{j:3d} {i:6d} {z.shape[0]:6d} {temp:7.4f}')

    if Screen: print("----------------------------------------")
    overall_end_time = time.time()
    print(f'Stop time = {overall_end_time}')
    overall_dt=overall_end_time-overall_start_time
    average_dt_no_first=np.sum(inner_dt[1:-1])/(N-1)
    average_dt=overall_dt/N
    std_dt=np.std(inner_dt)
    std_dt_no_first=np.std(inner_dt[1:-1])
    if Screen: 
        print(f"Elapsed seconds = {overall_dt:.4f}")
        print(f"Average seconds = {average_dt:.4f}")
        print(f"Std Dev seconds = {std_dt:.4f}\n")
        print(f"Average w/o first = {average_dt_no_first:.4f}")
        print(f"Std Dev w/o first = {std_dt_no_first:.4f}\n")
    else: print(overall_dt,average_dt,std_dt,std_dt_no_first)


if __name__ == '__main__':

    from argparse import ArgumentParser
    import sys
    parser = ArgumentParser()

    parser.add_argument('--file', action='store', dest='f', default='fort.63.nc', help='String: file to process.')
    parser.add_argument('--nsamp', action='store', dest='N', default=10, type=int, help='Int: number of accesses.')
    parser.add_argument('--seed', action='store', dest='seed', default=None, type=int, help='Int: random gen seed, default=None.')
    parser.add_argument('--screen', dest='screen', action='store_true')
    parser.add_argument('--no-screen', dest='screen', action='store_false')

    args = parser.parse_args()
    sys.exit(main(args))
