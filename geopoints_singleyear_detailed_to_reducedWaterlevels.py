#!/usr/bin/env python
# coding: utf-8

import sys
import pandas as pd
import numpy as np
import time as tm
import utilities as utilities

#urldirformat="/projects/reanalysis/ADCIRC/ERA5/hsofs/%d"
urldirformat=utilities.urldirformat  # ="http://tds.renci.org/thredds/dodsC/Reanalysis/ADCIRC/ERA5/hsofs/%d"

def main(args):
    """
    """
    variable_name=args.variable_name
    filename=args.filename
    geopointsfile=args.geopointsfile
    year=args.year

    nearest_neighbors=args.kmax

    print(f'Geopoints coming from the file {geopointsfile}')
    print(f'Selected nearest neighbors values is {nearest_neighbors}')

    df_geopoints = pd.read_csv(geopointsfile, index_col=0, header=0)
    print(df_geopoints) # Keep this for later comparisons.
    geopoints = df_geopoints[['lon','lat']].to_numpy()
    print(f'Number of input geopoints is {len(geopoints)}')

    print(f'Indicated var name is {variable_name}')
    print(f'Geopoints coming from the file {geopointsfile}')
    print(f'Selected nearest neighbors values is {nearest_neighbors}')

##
## Initialize input the ADCIRC and populate with grid properties
##
    urldir=urldirformat % year
    url=f'{urldir}/{filename}'

    ds=utilities.f63_to_xr(url)
    agdict=utilities.get_adcirc_grid_from_ds(ds)
    agdict=utilities.attach_element_areas(agdict)

##
## Perform the Tree building, Query and Weighted averaging of the timeseries (reduction)
##
    agdict=utilities.ComputeTree(agdict)
    agresults=utilities.ComputeQuery(geopoints, agdict, kmax=nearest_neighbors)
    agresults=utilities.ComputeBasisRepresentation(geopoints, agdict, agresults)
    agresults=utilities.ConstructReducedWaterLevelData_from_ds(ds, agdict, agresults, variable_name=variable_name)

##
## For future ref what geopoints were not assigned to any element
##
    print(f'List of {len(agresults["outside_elements"])} points not assigned to any grid element follows for kmax={nearest_neighbors}')
    print('List of points determined to not be within any element for kmax={}, {}'.format(nearest_neighbors,df_geopoints.loc[agresults['outside_elements']]))

##
## Assemble data for storage
##
    df_product_data=agresults['final_reduced_data']
    df_product_metadata=agresults['final_meta_data']
    df_product_data.to_csv('data.csv',header=True)
    df_product_metadata.to_csv('meta.csv',header=True)

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
    args = parser.parse_args()
    sys.exit(main(args))
