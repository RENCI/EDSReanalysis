#!/bin/bash -l 

firstyear=1979
years=(1990 2000 2001 2010)

# Manually separate out the FIRST year entry so that header names get included in the output files

echo "First year is $firstyear"
. ./RUNME_slurm "$firstyear" "1" 

for i in "${years[@]}"
do
   echo "$i"
   . ./RUNME_slurm "$i" "0"
done

