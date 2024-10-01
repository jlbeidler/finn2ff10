# commcooking
Tool for generating commercial cooking emissions and associated flat files for modeling in SMOKE from OpenStreetMap restaurant amenity data.
Emissions estimation methods are based on those used for the 2020 National Emissions Inventory: https://www.epa.gov/system/files/documents/2023-03/NEI2020_TSD_Section19_CommercialCooking.pdf

This tool can output to both a point and area style flat file (FF10) for input into the SMOKE emissions model. Assumed stack parameters and geospatially-derived restaurant locations are applied if modeled as a point source in an AQM such as CMAQ.

Required geospatial inputs are not included on this repostory. OSM snapshots can be obtained from sources such as Geofabrik (https://download.geofabrik.de/north-america/us.html). 
County polygons with FIPS can be obtained from the US Census (https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html).

# Install
Prequisites:
Python 3.5+, geopandas 0.14.0+, pandas 2.1.0+, pyrosm 0.6.2+

To install from github source clone or download this repository and run:<br>
<i>python setup.py build sdist</i><br>
<i>pip install dist/commcooking_VERSION.tar.gz</i>

# Configuration
Edit the osm_comm_cooking script. The section at the top of the script in the "User editable portion" section can be modified as needed.
- osm_pbf: defined the locations of the OSM PBF to use as a source of restaurant information
- comm_label: specifies the emissions output file label corresponding to the OSM PBF
- gapfill_cuisine: defines the SIC cuisine type to use to gapfill cuisines when they could not be determined from the restaurant information
- fips_shp: Is the path to the county polygons for labeling the FIPS codes of the restaurants
- fips_id: Defines the column of the county polygon shapefile to use for the FIPS
- ef_table: Is the path to a dataset of emission factors for commercial cooking by cooking device, food/meat type, pollutant, and emission factor (lb emitted/ton cooked)

Edit the gen_comm_cooking_invens script. At the top 3 variables can be set to generate FF10s from the osm_comm_cooking output
- lst: Is the new-line delimited list of osm_comm_cooking outputs to include in the inventories
- label: Defines the label to give the inventories
- year: Is the year that the inventory is intended to represent


# Usage

To generate the commercial cooking emissions estimate for one state, download an OSM snapshot for the state. Configure the osm_comm_cooking script to point to this state. Run osm_comm_cooking.
To generate an FF10 for one or more states: put the path to each osm_comm_cooking emissions output file on a newline in a list file, configure the gen_comm_cooking_invens to use this list file. Run gen_comm_cooking_invens.


# Data
Data included in the package:
- nemo_efs_table.csv: Emission factors derived from the 2020 NEI methods
- diurnal.csv: Diurnal profiles derived from the ARB study https://ww2.arb.ca.gov/sites/default/files/classic/research/apr/reports/l943.pdf
- dow_profile.csv: Day-of-week temporal profiles derived from the ARB study
- monthly.csv: Flat monthly temporal profiles
- tref.csv: Cross-reference from the commercial cooking SCCs to the temporal profiles


# Examples
- ri_food_cuisine_loc.csv: Example intermediate location output for Rhode Island
- ri_food_emissions.csv: Example osm_comm_cooking emissions output file for Rhode Island
- states.lst: Example list file for input into gen_comm_cooking_invens

Contact: beidler.james@epa.gov for assistance with this project

Disclaimer: The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. EPA has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by EPA. The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government. 
