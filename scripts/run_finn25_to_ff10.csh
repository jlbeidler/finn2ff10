#!/bin/csh -f
# Example script for subsetting FINN v2.5 MODIS/VIIRS SAPRC

set glob = global/FINNv2.5.1_modvrs_SAPRC_2022_c20240506.txt
set finncan = canada/finn_2_5_saprc99_2022_canada.csv
./strip_nocan.py $glob $finncan
setenv WORKDIR  $cwd
./finn25_to_ff10.py $finncan finn25_2022 2022
