#!/usr/bin/env python
# coding: utf-8

import sys
import pandas as pd
import numpy as np
import time as tm
import utilities as utilities

def main(args):
    variable_name=args.variable_name
    filename=args.filename
    geopointsfile=args.geopointsfile

    nearest_neighbors=args.kmax

    print(f'Geopoints coming from the file {geopointsfile}')
    print(f'Selected nearest neighbors values is {nearest_neighbors}')
##
    df_geopoints = pd.read_csv(geopointsfile, index_col=0, header=0)
    print(df_geopoints) # Keep this for later comparisons.
    geopoints = df_geopoints[['lon','lat']].to_numpy()
    print(f'Number of input geopoints is {len(geopoints)}')
## 
## Run the full pipeline
##
    year_tuple=(1979,1982)
    df_product_data, df_product_metadata, df_excluded = utilities.Combined_multiyear_pipeline(year_tuple=year_tuple,filename=filename, variable_name=variable_name,geopoints=geopoints,nearest_neighbors=nearest_neighbors, alt_urlsource=args.alt_urlsource)
    df_product_data.to_csv('data.csv',header=True)
    df_product_metadata.to_csv('meta.csv',header=True)
    print(df_excluded)
    df_excluded.to_csv('excluded_geopoints.csv')
    print(df_product_data)
    print('Finished')

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--filename', action='store', dest='filename', default=None, type=str,
                        help='ADCIRC data filename to fetch ADCIRC netCDF data')
    parser.add_argument('--geopointsfile', action='store', dest='geopointsfile', default=None, type=str,
                        help='filename to find geopoints lons/lats file data')
    parser.add_argument('--variable_name', action='store', dest='variable_name', default='zeta', type=str,
                        help='Variable name of interest from the supplied url')
    parser.add_argument('--kmax', action='store', dest='kmax', default=10, type=int,
                        help='nearest_neighbors values when performing the Query')
    parser.add_argument('--alt_urlsource', action='store', dest='alt_urlsource', default=None, type=str,
                        help='Alternative location for the ADCIRC data - NOTE specific formatting requirements exist')
    args = parser.parse_args()
    sys.exit(main(args))
