import sys 
import numpy as np
import pandas as pd
import re
import xarray as xr
from scipy import spatial as sp
from datetime import date, datetime
import time as tm

got_kdtree=None
TOL=10e-5

# Specify total number of available reanalysis years
YEARS=[1979,
       1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
       1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
       2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
       2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
       2020, 2021]

# urldirformat="/projects/reanalysis/ADCIRC/ERA5/hsofs/%d"
# Default standard locztion is on the RENCI TDS
urldirformat="http://tds.renci.org/thredds/dodsC/Reanalysis/ADCIRC/ERA5/hsofs/%d"

# dict for correspondance between internal netCDF variable names and netCDF file names.
# these should be determined by querying the standard names ...

# Typical mappings 
#varnamedict = {
#  "zeta_max": "maxele.63.nc",
#  "vel_max":  "maxvel.63.nc",
#  "inun_max": "maxinundepth.63.nc",
#  "zeta":     "fort.63_transposed_and_rechunked_1024.nc",
#  "swan_HS":  "swan_HS.63_transposed_and_rechunked_1024.nc",
#  "swan_TPS": "swan_TPS.63_transposed_and_rechunked_1024.nc",
#  "swan_DIR": "swan_DIR.63_transposed_and_rechunked_1024.nc"
#}

print("utilities:Xarray Version = {}".format(xr.__version__))

def get_adcirc_grid_from_ds(ds):
    """
    """
    agdict = {}
    agdict['lon'] = ds['x'][:]
    agdict['lat'] = ds['y'][:]
    agdict['ele'] = ds['element'][:,:] - 1
    agdict['depth'] = ds['depth'][:]
    agdict['latmin'] = np.mean(ds['y'][:])  # needed for scaling lon/lat plots
    return agdict

def attach_element_areas(agdict):
    """
    """
    x=agdict['lon'].values
    y=agdict['lat'].values
    e=agdict['ele'].values
    
    # COMPUTE GLOBAL DX,DY, Len, angles
    i1=e[:,0]
    i2=e[:,1]
    i3=e[:,2]

    x1=x[i1];x2=x[i2];x3=x[i3];
    y1=y[i1];y2=y[i2];y3=y[i3];

    # coordinate deltas
    dx23=x2-x3
    dx31=x3-x1
    dx12=x1-x2
    dy23=y2-y3
    dy31=y3-y1
    dy12=y1-y2

    # lengths of sides
    a = np.sqrt(dx12*dx12 + dy12*dy12)
    b = np.sqrt(dx31*dx31 + dy31*dy31)
    c = np.sqrt(dx23*dx23 + dy23*dy23)
    
    agdict['areas'] = ( x1*dy23 + x2*dy31 + x3*dy12 )/2.
    agdict['edge_lengths']=[a, b, c];
    agdict['dl']=np.mean(agdict['edge_lengths'],axis=0)

    return agdict
    
def basis2d_withinElement(phi):
    """
    """
    interior_status = np.all(phi[:]<=1+TOL,axis=1) & np.all(phi[:]>=0-TOL,axis=1)
    return interior_status

def basis2d(agdict,xylist,j):
    """
    """
    # check length of j and xylist
    # check for needed arrays in agdict
    phi=[]
    #nodes for the elements in j
    n3=agdict['ele'][j]
    x=agdict['lon'][n3].values     
    x1=x[:,0];x2=x[:,1];x3=x[:,2];
    y=agdict['lat'][n3].values
    y1=y[:,0];y2=y[:,1];y3=y[:,2];  
    areaj=agdict['areas'][j]
    xp=xylist[:,0]
    yp=xylist[:,1]
    # Basis function 1
    a=(x2*y3-x3*y2)
    b=(y2-y3)
    c=-(x2-x3)
    phi0=(a+b*xp+c*yp)/(2.0*areaj)
    # Basis function 2
    a=(x3*y1-x1*y3)
    b=(y3-y1)
    c=-(x3-x1)
    phi1=(a+b*xp+c*yp)/(2.0*areaj)
    # Basis function 3
    a=(x1*y2-x2*y1)
    b=(y1-y2)
    c=-(x1-x2)
    phi2=(a+b*xp+c*yp)/(2.0*areaj)
    return np.array([phi0, phi1, phi2]).T

def get_adcirc_time_from_ds(ds):
    """
    """
    return {'time': ds['time']}

def f63_to_xr(url):
    """
    """
    dropvars=['neta', 'nvel',  'max_nvdll', 'max_nvell']
    return xr.open_dataset(url,drop_variables=dropvars)

def get_adcirc_slice_from_ds(ds,v,it=0):
    """
    """
    advardict = {}
    var = ds.variables[v]
    if re.search('max', v) or re.search('depth', v):
        var_d = var[:] # the actual data
    else:
        if ds.variables[v].dims[0] == 'node':
            #print('ds: transposed data found')
            var_d = var[it,:].T # the actual data
        elif ds.variables[v].dims[0] == 'time':
            var_d = var[:,it] # the actual data
        else:
            print(f'Unexpected leading variable name {ds.variables[v].dims}: Abort')
            sys.exit(1)
    #var_d[var_d.mask] = np.nan
    advardict['var'] = var_d.data
    return advardict

def ComputeTree(agdict):
    """
    Given the pre-loaded lon,lat,ele entries in agdict,compute the means and 
    generate the full ADCIRC grid KDTree
    """

    global got_kdtree # Try not too if already done
    t0=tm.time()
    try:
        x=agdict['lon'].values.ravel() # ravel; not needed
        y=agdict['lat'].values.ravel()
        e=agdict['ele'].values
    except Exception as e:
        print('Failed in finding lon,lat,ele data in agdict. Perhaps check for preprocesing using attach_element_areas method. {}'.format(e))
        sys.exit(1)
    xe=np.mean(x[e],axis=1)
    ye=np.mean(y[e],axis=1)
    if got_kdtree is None: # Still want to build up the data for agdict, we just do not need the tree reevaluated for every year
        agdict['tree']=tree = sp.KDTree(np.c_[xe,ye])
        got_kdtree=tree
    else:
        agdict['tree']=got_kdtree
    print(f'Build annual KDTree time is {tm.time()-t0}s')
    return agdict

def ComputeQuery(xylist, agdict, kmax=10):
    """
    Generate the kmax-set of nearest neighbors to each lon,lat pair in xylist.
    Each test point (each lon/lat pair) gets associated distance (dd) and element (j) objects 
    At this stage it is possible that some test points are not interior to the nearest element. We will
    subsequently check that.

    dd: num points by neighbors
    j: num points by neighbors
    """
    t0=tm.time()
    agresults=dict()
    dd, j = agdict['tree'].query(xylist, k=kmax)
    if kmax==1:
        dd=dd.reshape(-1,1)
        j=j.reshape(-1,1)
    agresults['distance']=dd
    agresults['elements']=j
    agresults['number_neighbors']=kmax
    agresults['geopoints']=xylist # We shall use this later
    print(f'KDTree query of size {kmax} took {tm.time()-t0}s')
    return agresults

def ComputeBasisRepresentation(xylist, agdict, agresults):
    """
    For each test point with kmax number_neighbors, compute basis representations for
    each neighbor. Then, check which, if any, element the test point actually resides within.
    If none, then the returned basis function (weights) are set to nans. Doing it this way
    will retain the order of user supplied test points, overall

    Now if the user chooses an exact grid point for the input geopoint, then ambiguity
    may arise regarding the best element and multiple True statuses can occur. Here we 
    also keep the nearest element value. We do this by reverse iterating in the zip function
    """

    # First build all the basis weights and determine if it was interior or not
    t0=tm.time()
    kmax = agresults['number_neighbors']
    j = agresults['elements']
    phival_list=list()
    within_interior=list()
    for k_value in range(0,kmax):
        phival=basis2d(agdict,xylist,j[:,k_value])
        phival_list.append(phival)
        within_interior.append(basis2d_withinElement(phival))
    #
    #detailed_weights_elements(phival_list, j)

    # Second only retain the "interior" results or nans if none
    final_weights= np.full( (phival_list[0].shape[0],phival_list[0].shape[1]),np.nan)
    final_jvals = np.full( j.T[0].shape[0],-99999)
    final_status = np.full( within_interior[0].shape[0],False)
    # Loop backwards. thus keeping the "nearest" True for each geopoints for each k in kmax
    for pvals,jvals,testvals in zip(phival_list[::-1], j.T[::-1], within_interior[::-1]):  # THis loops over Kmax values
        final_weights[testvals] = pvals[testvals]
        final_jvals[testvals]=jvals[testvals]
        final_status[testvals] = testvals[testvals]

    agresults['final_weights']=final_weights
    agresults['final_jvals']=final_jvals
    agresults['final_status']=final_status
    print(f'Identify best annual basis weights took {tm.time()-t0}s')
    # Keep the list if the user needs to know after the fact
    outside_elements = np.argwhere(np.isnan(final_weights).all(axis=1)).ravel()
    agresults['outside_elements']=outside_elements
    return agresults

def detailed_weights_elements(phival_list, j):
    """
    This is only used for understanding better the detailed behavior of a particular grid
    It is not invoked for general use
    """
    for pvals,jvals in zip(phival_list,j.T):
        df_pvals = pd.DataFrame(pvals, columns=['Phi0','Phi1','Phi2'])
        df_pvals.index = df_pvals.index
        df_jvals = pd.DataFrame(jvals+1,columns=['Element+1'])
        df = pd.concat([df_pvals,df_jvals],axis=1)
        df.index = df.index+1
        df.index = df.index.astype(int)
        print(df.loc[2].to_frame().T)

def WaterLevelReductions(t, data_list, final_weights):
    """
    Each data_list is a df for a single test point containing 3 columns. 
    These columns are reduced using the final_weights previously calculated
    
    A final df is returned with index=time and a single column for each of the
    input test points (some of which may be partially or completely nan)
    """
    final_list = list()
    for index,dataseries,weights in zip(range(0,len(data_list)), data_list,final_weights):
        reduced_data = np.matmul(dataseries.values, weights.T)
        df = pd.DataFrame(reduced_data, index=t, columns=[f'P{index+1}'])
        final_list.append(df)
    df_final_data = pd.concat(final_list, axis=1)
    return df_final_data

def GenerateMetadata(agresults):
    """
    Here we want to simply assist the user by reporting back the lon/lat values for each geopoint.
    This should be the same as the input dataset.-99999 elements means none found
    """
    df_lonlat=pd.DataFrame(agresults['geopoints'], columns=['LON','LAT'])
    df_elements = pd.DataFrame(agresults['final_jvals']+1, columns=['ELE+1'])
    df_elements.replace(-99998,-99999,inplace=True)
    df_meta=pd.concat( [df_lonlat,df_elements], axis=1)
    df_meta['GEOPOINT']=df_meta.index+1
    df_meta.set_index('GEOPOINT', inplace=True)
    df_meta.rename('P{}'.format, inplace=True)
    return df_meta

def ConstructReducedWaterLevelData_from_ds(ds, agdict, agresults, variable_name=None): 
    """
    This method acquires ADCIRC water levels for the list of geopoints/elements (three for the current grids). for each specified element of the grid
    the resulting time series' are reduced to a single time series using a (basis2d) weighted sum. For a non-nan value to 
    result in the final data, the product data must:
    1) Be non-nan for each time series at the specified time tick
    2) The test point must be interior to the specified element
    """
    if variable_name is None:
        print('User MUST supply the correct variable name')
        sys.exit(1)
    print(f'Variable name is {variable_name}')
    t0 = tm.time()
    data_list=list()
    final_weights = agresults['final_weights']
    final_jvals = agresults['final_jvals']
    acdict=get_adcirc_time_from_ds(ds)
    t=acdict['time'].values
    e = agdict['ele'].values
    for vstation in final_jvals:
        advardict = get_adcirc_slice_from_ds(ds,variable_name,it=e[vstation])
        df = pd.DataFrame(advardict['var'])
        data_list.append(df)
    print(f'Time to fetch annual all test station (triplets) was {tm.time()-t0}s')
    df_final=WaterLevelReductions(t, data_list, final_weights)
    t0=tm.time()
    df_meta=GenerateMetadata(agresults) # This is here mostly for future considerations
    print(f'Time to reduce annual {len(final_jvals)} test stations is {tm.time()-t0}s')
    agresults['final_reduced_data']=df_final
    agresults['final_meta_data']=df_meta
    return agresults

def return_sorted_years(year_tuple):
    """
    Range of years (inclusive) to test: (start_year,end_year)
    Sort and ensure existance
    """
    print(year_tuple)
    start_year=year_tuple[0] if year_tuple[0] in YEARS else None
    end_year=year_tuple[1] if year_tuple[1] in YEARS else None
    if all(year_tuple):
        year_tuple=tuple(sorted((start_year,end_year)))
    else:
        print(f'One or more bad years were specified {year_tuple}')
        print(f'Choose from only {YEARS}')
        sys.exit(1)
    return year_tuple[0],year_tuple[1]
  
def Combined_multiyear_pipeline(year_tuple=None, filename=None, geopoints=None, variable_name=None, nearest_neighbors=10, alt_urlsource=None): 
    """
    User must provide the proper filename (eg fort.63.nc) from which to access the data
         must provide the associated variable_nae for the data product
         May provide an alternative storage location, with caveats, else the TDS server is used.
    """
    urlfetchdir=urldirformat if alt_urlsource is None else alt_urlsource
    list_data=list()
    list_meta=list()
    start_year,end_year=return_sorted_years(year_tuple)
    print(f'Final sorted input years {year_tuple}')
    print(f'Chosen ADCIRC data source {urlfetchdir}')
    for year in range(start_year,end_year+1):
        print(year)
        url=f'{urlfetchdir % year}/{filename}'
        print(url)
        df_data, df_metadata, df_excluded=Combined_pipeline(url, variable_name, geopoints, nearest_neighbors=nearest_neighbors)
        list_data.append(df_data)
        list_meta.append(df_metadata)
    df_final_data=pd.concat(list_data,axis=0)
    df_final_metadata=pd.concat(list_meta,axis=0)
    return df_final_data, df_final_metadata, df_excluded # Just grab last df_excluded since they are al the same (or should be)

# NOTE We do not need to rebuild the treee for each year since the grid is unchanged.
def Combined_pipeline(url, variable_name, geopoints, nearest_neighbors=10):
    """
    Simply run the series of steps as part of this method to shield users from some
    of the details of the processing

    df_excluded_geopoints list only those stations excluded by element interiority tests. Some could be all nans due to dry points

    """
    ds = f63_to_xr(url)
    agdict=get_adcirc_grid_from_ds(ds)
    agdict=attach_element_areas(agdict)

    print('Start annual KDTree pipeline')
    agdict=ComputeTree(agdict)
    agresults=ComputeQuery(geopoints, agdict, kmax=nearest_neighbors)
    agresults=ComputeBasisRepresentation(geopoints, agdict, agresults)
    agresults=ConstructReducedWaterLevelData_from_ds(ds, agdict, agresults, variable_name=variable_name)
    ##print('Final set of weights')
    ##print(agresults['final_weights'])

    print(f'Basis function Tolerance value is {TOL}')
    print(f'List of {len(agresults["outside_elements"])} stations not assigned to any grid element follows for kmax {nearest_neighbors}')
    df_product_data=agresults['final_reduced_data']
    df_product_metadata=agresults['final_meta_data']
    df_excluded_geopoints=pd.DataFrame(geopoints[agresults['outside_elements']], index=agresults['outside_elements']+1, columns=['lon','lat'])
    print('Finished annual Combined_pipeline')
    return df_product_data, df_product_metadata, df_excluded_geopoints
