#!/usr/bin/env python
# Script to subset the FINN v2.5 input file to include only Canada

import sys
import pandas as pd

infile_name = sys.argv[1]
outfile_name = sys.argv[2]
df = pd.read_csv(infile_name, skipinitialspace=True, index_col=False,
  usecols=['DAY','GENVEG','LATI','LONGI','AREA','BMASS','CO','SO2','NH3','NMOC','PM10','PM25','CH4','NO','NO2','HONO','POLYID','CO2','FIREID','HCHO'])
# Just keep the locations that are around Canada 
df = df[(df['LATI'] > 41) & (df['LONGI'] < -52) & (df['LONGI'] > -141)].copy()
df.to_csv(outfile_name, index=False)
print('END')
