% Example MATLAB code to extract timeseries from the RENCI/NOAA Reanalysis 
% datasets on the HSOFS grid.

%% parameters
urlpat='http://tds.renci.org/thredds/dodsC/Reanalysis/ADCIRC/ERA5/hsofs/%d%s/%s.d0.no-unlim.T.rc.nc';
pripost='-post'; 
y1=1979;
y2=1980;
ks = {'water level','offset','hsign'};
vs = {{'zeta','fort.63'}
      {'offset','offset.63'}
      {'swan_HS','swan_HS.63'}
      };
F=containers.Map(ks,vs,'UniformValues',false);

varname='water level';

useStrTree=false;

%% read in csv file of points
T=readtable('~/GitHub/RENCI/EDSReanalysis/testdata/NOAA_Stations_141.csv');
%1point.csv');
lon=T.lon;
lat=T.lat;

% ll=[ -75.879  34.784
%      -76.604  33.44];
% lon=ll(:,1);
% lat=ll(:,2);

%%

% if the hsofs grid is available, load it here.
% g=grd_to_opnml('<path to hsofs.grid file>');
% and compute the strtree
% g.strtree=ComputeStrTree(g);
%
% Otherwise, it will be loaded below on the first pass through the year
% loop.

% loop over years
firstcall=true;
Z=[];
T=[];
f=F(varname);
vname=f{1};
fname=f{2};

for y=y1:y2

    fprintf('Working on y=%d\n',y);
    url=sprintf(urlpat,y,pripost,fname);
    %url='http://tds.renci.org/thredds/dodsC/2022/al05/07/ec95d/hatteras.renci.org/ec95d-al05-bob/nhcOfcl/fort.63.nc';
    nc=ncgeodataset(url);
    v=nc{vname};
    t=nctime(nc);

    if firstcall
        fprintf('   First call stuff\n');
        fprintf('      Getting grid ... \n');
        % extract the grid from the nc object
        g=ExtractGrid(nc);
        fprintf('      Finding elements ...\n');
        if useStrTree
            fprintf('         Computing StrTree first ... \n');
            g.strtree=ComputeStrTree(g);
            J=FindElementsInStrTree(g,lon,lat);
        else
            % find elements in g for lon,lat
            J=findelem(g,lon,lat);
        end
        n=g.e(J,:);
        % get interp weights
        fprintf('      Getting interpolation factors ...\n');
        phi=basis2d(g,[lon lat],J);
        firstcall=false;
    end

    % loop over points
    zi=nan(length(t),length(J));
    for j=1:length(J)
        % get timeseries at each element node
        if ~isnan(J(j))
            z1=v(n(j,1),:)';
            z2=v(n(j,2),:)';
            z3=v(n(j,3),:)';
            zi(:,j)=[z1 z2 z3]*phi(j,:)';
        end
    end
    Z=[Z;zi];
    T=[T;t];
end



