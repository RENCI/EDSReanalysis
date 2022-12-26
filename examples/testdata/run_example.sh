#!/bin/bash -l 
#SBATCH -t 128:00:00
#SBATCH -p batch
#SBATCH -N 1
#SBATCH -n 2 
#SBATCH -J Geopoints
#SBATCH --mem-per-cpu 128000

export PYTHONPATH=/projects/sequence_analysis/vol1/prediction_work/EDSReanalysis

python ../geopoints_simple_to_performance_reducedWaterlevels.py 
