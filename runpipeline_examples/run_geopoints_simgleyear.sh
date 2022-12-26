
# Use a larger input geopoints file

python ../examples/geopoints_simple_multiyear_reducedWaterlevels.py --filename 'fort.63.d0.no-unlim.T.rc.nc' --variable_name 'zeta' --geopointsfile '../testdata/hsofs_example_geopoints.csv' --kmax=10 --alt_urlsource 'http://tds.renci.org/thredds/dodsC/Reanalysis/ADCIRC/ERA5/hsofs/%d'

# If you had pre downloaded the set of ADCIRC data files to a local directory you could do something like this instead.
#python ../examples/geopoints_simple_multiyear_reducedWaterlevels.py --filename 'fort.63.d0.no-unlim.T.rc.nc' --variable_name 'zeta' --geopointsfile '../testdata/hsofs_example_geopoints.csv' --kmax=10 --alt_urlsource '/projects/reanalysis/ADCIRC/ERA5/hsofs/%d'


