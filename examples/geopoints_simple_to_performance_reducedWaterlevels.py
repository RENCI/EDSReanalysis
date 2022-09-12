#!/usr/bin/env python
# coding: utf-8

import sys
import pandas as pd
import numpy as np
import time as tm
import random
import utilities as utilities

# Specify available reanalysis years
ymin=1979
ymax=2021
YEARS=[item for item in range(ymin, ymax+1)]

# How many geopoints ot test with ?
POINTS=[10,50,100,500,1000,5000,10000]

# Choose URLs type:
urlformat='/projects/reanalysis/ADCIRC/ERA5/hsofs/%s/fort.63_transposed_and_rechunked_1024.nc'
variable_name='zeta'
#urlformat='/projects/reanalysis/ADCIRC/ERA5/hsofs/%s/swan_HS.63_transposed_and_rechunked_1024.nc'
#variable_name='swan_HS'

print(f'input URL selected {urlformat}')

# Read in previously saved hsofs grid points from an ADCIRC file as geopoints

geopointsfile='hsofs_fullgrid_lonlat.csv'
print(f'Geopoints coming from the file {geopointsfile}')
df_geopoints=pd.read_csv(geopointsfile,header=0)
df_geopoints.drop('node',axis=1, inplace=True)
print(df_geopoints) # Keep this for later comparisons.

random.shuffle(YEARS) # Try to subvert any disk cachine

runtimes=list()
for index,numpoints in zip(range(0,len(POINTS)),POINTS):
    t1=tm.time()
    year = YEARS[index]
    url = urlformat % year
    print(f'numpoints {numpoints} year {year}')
    df_test_geopoints=df_geopoints.sample(n=numpoints)
    geopoints = df_test_geopoints[['lon','lat']].to_numpy()
    print(f'Number of input geopoints is {len(geopoints)}')
    # Run the job
    df_product_data, df_product_metadata, df_excluded = utilities.Combined_pipeline(url, variable_name, geopoints,nearest_neighbors=10)
    tout=tm.time()-t1
    runtimes.append((numpoints,tout))

print(runtimes)
xy=[d[1] for d in runtimes]
y=[d[1]/d[0] for d in runtimes]
print(y)

# Plot the data
#plt.scatter(*zip(*runtimes))
plt.plot(*zip(*runtimes))
#plt.title('HSOFS: Reanalysis: Single year: geopoints to reduced WL')
#plt.xlabel('Number of geopoints')
#plt.xlim(0,5000)
#plt.ylabel('Time/s')
#plt.show()

# The following are example timings when accessing data from/projects directly
#[(10, 23.27109456062317), (50, 43.37220215797424), (100, 57.82859563827515), (500, 236.5611023902893), (1000, 428.45812344551086), (5000, 2001.8462417125702), (10000, 3579.1538910865784)]
# Normalized by numpoints data are:
#>>> xy=[d[1] for d in runtimes]
#>>> y=[d[1]/d[0] for d in runtimes]
#>>> y
#[2.327109456062317, 0.8674440431594849, 0.5782859563827515, 0.4731222047805786, 0.4284581234455109, 0.40036924834251403, 0.35791538910865783]

# The following are example timings when accessing the TDS


