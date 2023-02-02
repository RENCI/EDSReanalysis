#!/usr/bin/env python
# coding: utf-8

# This is a simple version of the codes in this suite.Here, we simply input the stationids, and ADCIRC Nodes
# From which to read the proper data. 
#

import sys
import pandas as pd
import numpy as np
import time as tm
import utilities as utilities

def main(args):
    """
    """
    #urldirformat="/projects/reanalysis/ADCIRC/ERA5/hsofs/%d"
    urldirformat="http://tds.renci.org/thredds/dodsC/Reanalysis/ADCIRC/ERA5/hsofs/%d"
    #urldirformat="http://tds.renci.org/thredds/dodsC/Reanalysis/ADCIRC/ERA5/ec95d/%d"

    year=args.year
    if args.urlbase is not None:
        print('No urlbase was supplied. We assume you want to get the reanalysis data and so will default to that value')
        urldirformat=args.urlbase

    try:
        urldir=urldirformat % year
    except TypeError:
        print('Got a TypeError prob this means you are specifying a specific urldir with no year formatting')
        urldir=urldirformat
    except Exception as e:
        print(f'urlbase formatting error: {e} ')
        sys.exit(1)

    print(f'urldir is {urldir}')

    variable_name=args.variable_name
    filename=args.filename
    geopointsfile=args.geopointsfile

    # NOTE: This geopoints file MUST include stationid,Node

    print(f'Geopoints coming from the file {geopointsfile}')

    df_geopoints = pd.read_csv(geopointsfile, index_col=0, header=0)
    print(df_geopoints) # Keep this for later comparisons.
    print(f'Number of input geopoints is {len(df_geopoints)}')
    print(f'Indicated var name is {variable_name}')
    print(f'Geopoints coming from the file {geopointsfile}')

##
## Initialize input the ADCIRC and populate with grid properties
##
    url=f'{urldir}/{filename}'
    print(f'Final URL is {url}')
    ds=utilities.f63_to_xr(url)
    agdict=utilities.get_adcirc_grid_from_ds(ds)

    df_geopoints.set_index('stationid',inplace=True)
    agresults=utilities.FetchWaterLevelData_from_ds(df_geopoints, ds, variable_name=variable_name)

##
## Assemble data for storage
##
    df_product_data=agresults['final_data']
    df_product_data.to_csv('data.csv',header=True)
    print(df_product_data)
    print('Finished')

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--filename', action='store', dest='filename', default=None, type=str,
                        help='ADCIRC data filename to fetch ADCIRC netCDF data')
    parser.add_argument('--geopointsfile', action='store', dest='geopointsfile', default=None, type=str,
                        help='filename to find geopoints lons/lats file data')
    parser.add_argument('--variable_name', action='store', dest='variable_name', default=None, type=str,
                        help='Variable name of interest from the supplied url')
    parser.add_argument('--kmax', action='store', dest='kmax', default=10, type=int,
                        help='nearest_neighbors values when performing the Query')
    parser.add_argument('--year', action='store', dest='year', default=None, type=int,
                        help='Choose year to process')
    parser.add_argument('--urlbase', action='store', dest='urlbase', default=None, type=str,
                        help='The base URL info to find fort.63.nc or equiv')

    args = parser.parse_args()
    sys.exit(main(args))
