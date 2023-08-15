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
## Run the full tear pipeline
##
    year = args.year
    print(f'Prcessing year {year}')

    t0=tm.time()
    df_product_data, df_product_metadata, df_excluded, data_list_bob = utilities.Combined_multiyear_pipeline(year_tuple=(year,year),filename=filename, variable_name=variable_name,geopoints=geopoints,nearest_neighbors=nearest_neighbors, alt_urlsource=args.alt_urlsource)

    df_product_data.to_csv(f'{year}_data.csv',header=args.keep_headers)
    df_product_metadata.to_csv(f'{year}_meta.csv',header=args.keep_headers)
    print(df_excluded)
    df_excluded.to_csv(f'{year}_excluded_geopoints.csv')
    print(df_product_data)
    df_product_data.to_pickle(f'{year}_data.pkl')
    print(f'Finished. Runtime was {tm.time()-t0}')
    print(data_list_bob)
    
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
    parser.add_argument('--year', action='store', dest='year', default=None, type=int,
                        help='Choose year to process')
    parser.add_argument('--keep_headers', action='store_true', default=False,
                        help='Boolean: Indicates to add header names to output files')

    args = parser.parse_args()
    sys.exit(main(args))
