!/bin/bash -l 

firstyear=1979
years=(1990 2000 2001 2010)

# Manually invoke the FIRST entry so that header names get included in the output files
# Can usualy run a simple slurm script as a simple shell script 

echo "First year is $firstyear"
  cp "$firstyear"_data.csv  full_data.csv 

for i in "${years[@]}"
do
   cat  "$i"_data.csv >> full_data.csv
   echo "$i"
done

