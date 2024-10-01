# finn2ff10
Tool for converting a FINN v2.5 annual formatted SAPRC speciated text file to a SMOKE ready point flat file (FF10).
Converts pollutant units to tons. Inserts country-level codes based on ancillary data.

FINN v2.5 data available from https://rda.ucar.edu/datasets/d312009/
The text file format with speciated VOC should be selected.


# Install
Prequisites:
Python 3.5+,  pandas 2.1.0+, netCDF4 1.6+, osgeo 3.6+

# Usage
- finn25_to_ff10.py is invoked with the command line options of the (1) path to annual FINN v2.5 text file (2) output name prefix and (3) year
e.g. ./finn25_to_ff10.py input/MODVIRS_FINN25_2023.csv finn25_2023 2023
The WORKDIR environment variable should be set for output path.

This package contains 3 sets of ancillary files in the ancillary path: GRIDMASK_EDGAR.ncf, geocode_to_fips.csv, and scuo_large_update.shp
This should be copied and decompressed in the ancillary path of your run directory.

The "strip_nocan.py" script is shared as an example of subsetting the FINN v2.5 data to target a specified region. This script subsets to the approximate area of Canada.

An example run script is available at scripts/run_finn25_to_ff10.csh
Before running this script create the global, canada, and invens subdirectories.
