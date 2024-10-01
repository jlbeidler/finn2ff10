#!/usr/bin/env csh
#
# c-shell script to download selected files from rda.ucar.edu using Wget
# NOTE: if you want to run under a different shell, make sure you change
#       the 'set' commands according to your shell's syntax
# after you save the file, don't forget to make it executable
#   i.e. - "chmod 755 <name_of_script>"
#
# Experienced Wget Users: add additional command-line flags to 'opts' here
#   Use the -r (--recursive) option with care
#   Do NOT use the -b (--background) option - simultaneous file downloads
#       can cause your data access to be blocked
set opts = "-N"
#
# Check wget version.  Set the --no-check-certificate option 
# if wget version is 1.10 or higher
set v = `wget -V |grep 'GNU Wget ' | cut -d ' ' -f 3`
set a = `echo $v | cut -d '.' -f 1`
set b = `echo $v | cut -d '.' -f 2`
if(100 * $a + $b > 109) then
  set cert_opt = "--no-check-certificate"
else
  set cert_opt = ""
endif

set filelist= ( \
  https://data.rda.ucar.edu/ds312.9/eachfire_modisviirs/FINNv2.5_modvrs_SAPRC_2017_c20211213.txt.gz  \
  https://data.rda.ucar.edu/ds312.9/eachfire_modisviirs/FINNv2.5_modvrs_SAPRC_2018_c20211213.txt.gz  \
  https://data.rda.ucar.edu/ds312.9/eachfire_modisviirs/FINNv2.5_modvrs_SAPRC_2019_c20211213.txt.gz  \
  https://data.rda.ucar.edu/ds312.9/eachfire_modisviirs/FINNv2.5_modvrs_SAPRC_2020_c20211213.txt.gz  \
)
while($#filelist > 0)
  set syscmd = "wget $cert_opt $opts $filelist[1]"
  echo "$syscmd ..."
  $syscmd
  shift filelist
end
