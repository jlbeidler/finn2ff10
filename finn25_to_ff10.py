#!/usr/bin/env python
# Converts extracted FINN fire emissions to FF10 point daily format
# Updated 10 May 2017 to fix projection issues. <J. Beidler>
# Updated 20 Aug 2020 to reduce number of othna inventories. <J. Beidler>

import os
import sys
from datetime import datetime
import pandas as pd
from osgeo import ogr
import netCDF4 as ncf 

countries = ['US','CA','MX','ONA']
cty_dict = {'US': 'US', 'MX': 'MEXICO', 'CA': 'CANADA', 'ONA': 'OTHERNORTHAMERICA', 'GEO': 'GLOBAL'}

def main():
    if len(sys.argv) != 4:
        raise ValueError('Path to SAPRC FINN fire and output prefix')
    finn_fire = sys.argv[1]
    prefix = sys.argv[2]
    year = sys.argv[3]
    finn_df = pd.DataFrame()
    finn_df = get_finn_data(finn_fire, year)
    for country in countries:
        print(country, flush=True)
        country_df = finn_df[finn_df['country_cd']==country].copy()
        if country_df.empty:
            print('WARNING: No %s fires for selected days' %country)
        else:
            pday = '{}/invens/ptday_finn25_{}_{}_ff10.csv'.format(os.environ['WORKDIR'], country, prefix)
            write_daily_ff10(country_df[['country_cd','region_cd','facility_id','scc','poll','unit_id',
              'monthnum','day','val','process_id']].copy(), pday, country, year)
            ptinv = '{}/invens/ptinv_finn25_{}_{}_ff10.csv'.format(os.environ['WORKDIR'], country, prefix)
            write_annual_ff10(country_df, ptinv, country, year)
    grid_mask = 'ancillary/GRIDMASK_EDGAR.ncf'
    geo_to_fips = 'ancillary/geocode_to_fips.csv'
    geo_ref = GeoCode(grid_mask, geo_to_fips)
    finn_df = fill_geocodes(finn_df[finn_df['country_cd'] == 'NA'].copy(), geo_ref)
    finn_df = roll_up_geo(finn_df)
    # Drop areas that overlap in Central America
    finn_df = finn_df[~ finn_df['region_cd'].isin(('19116','19221','19176'))].copy()
    #geo_ref.ncf.close()
    pday = '{}/invens/ptday_finn_{}_{}_ff10.csv'.format(os.environ['WORKDIR'], 'GEO', prefix)
    write_daily_ff10(finn_df, pday, 'GEO', year)
    ptinv = '{}/invens/ptinv_finn_{}_{}_ff10.csv'.format(os.environ['WORKDIR'], 'GEO', prefix)
    write_annual_ff10(finn_df, ptinv, 'GEO', year)

class na_shape():
    def __init__(self):
        driver = ogr.GetDriverByName('ESRI Shapefile')
        self.shp = driver.Open('ancillary/scuo_large_update.shp')
        if not self.shp:
            raise ValueError('Cannot open shapefile')
        self.layer = self.shp.GetLayer()
        geo = ogr.osr.SpatialReference()
        geo.ImportFromEPSG(4267)
        point_ref = ogr.osr.SpatialReference()
        point_ref.ImportFromEPSG(4326)
        self.trans = ogr.osr.CoordinateTransformation(point_ref, geo)

    def get_loc(self, lon, lat, field_name):
        [lon,lat,z] = self.trans.TransformPoint(lon, lat)
        pt = ogr.Geometry(ogr.wkbPoint)
        pt.SetPoint_2D(0, lon, lat)
        self.layer.SetSpatialFilter(pt)
        idx = self.layer.GetLayerDefn().GetFieldIndex(field_name)
        for feat in self.layer:
            return feat.GetFieldAsString(idx)

def get_country(fips):
    if len(fips) > 0 and fips[0] != '-':
        return countries[int(fips[0])]
    else:
        return 'NA'

def set_date(year, day):
    out_day = datetime.strftime(datetime.strptime('%s%0.3d' %(year, day), '%Y%j'), '%Y%m%d')
    return out_day

def calc_mass(df):
    '''
    Calculate the mass from the species
    gases in moles/day
    aerosols and NMOC in kg/day
    '''
    g_per_ton = 907184.74
    kg_per_ton = g_per_ton / 1000
    mwtbl = {'CO': 28., 'SO2': 64., 'NOX': 46., 'NH3': 17., 'CO2': 44., 
      'CH4': 16., 'HCHO': 30., 'NMOC': 1000, 'PM10-PRI': 1000, 'PM25-PRI': 1000}
    # Sum up the NOx gases and convert to NOX as NO2 mass for CMAQ
    df['NOX'] = df[['NO','NO2','HONO']].sum(axis=1) 
    for spec, mw in mwtbl.items():
        df[spec] = df[spec] * mw / g_per_ton
    # VOC tons = NMOC kg / (tons/kg) 
    df['VOC'] = df['NMOC']
    # BTU = kg/m2 * acres * lb/kg * m2/acre * BTU/lb
    df['HFLUX'] = df['BMASS'] * df['ACRESBURNED'] * 2.2046 * 4046.856 * 8000 
    df['BMASS'] = df['BMASS'] / kg_per_ton
    df.drop(['NO','NO2','HONO','NMOC'], axis=1, inplace=True)
    return df

def fix_finn_fips(df):
    '''
    Remap the FIPS in CA/MX/Othar
    '''
    regions = {'81000': '159000', '82000': '148000', '83000': '147000', '84000': '146000', 
      '85000': '135000', '86000': '124000', '87000': '113000', '88100': '111000', '89000': '112000',
      '90000': '110000', '80100': '160000', '80200': '162000', '80300': '161000', '91140': '202000',
      '91680': '224000', '91860': '231000', '91780': '228000', '91280': '206000', '91380': '212000', 
      '91820': '229000', '91560': '219000', '91220': '207000', '91580': '220000', '91260': '205000', 
      '91240': '208000', '91360': '211000', '91180': '204000', '91520': '217000', '91540': '218000', 
      '91640': '222000', '91840': '230000', '91120': '201000', '91880': '232000', '91320': '209000', 
      '91420': '213000', '91760': '227000', '91620': '221000', '91740': '226000', '91340': '210000', 
      '91660': '223000', '91480': '216000', '91440': '214000', '91460': '215000', '91720': '225000',
      '301000': '301000', '302000': '302000', '303000': '303000', '304000': '304000', 
      '305000': '305000', '306000': '306000', '307000': '307000', '308000': '308000',
      '309000': '309000', '310000': '310000', '311000': '311000', '91160': '203000'}
    regions = pd.DataFrame(list(regions.items()), columns=['fips','region_cd'])
    df = pd.merge(df, regions, on='fips', how='left')
    df.loc[(df['region_cd'].isnull()) & ((df['fips'].notnull()) & (df['fips'] != '')), 'region_cd'] = \
      '0' + df.loc[(df['region_cd'].isnull()) & ((df['fips'].notnull()) & (df['fips'] != '')), 'fips'] 
    df.drop('fips', axis=1, inplace=True)
    df['region_cd'] = df['region_cd'].fillna('-9999')
    return df

def get_finn_data(infile_name, year):
    '''
    Read in the v2.5 FINN data

    DAY,POLYID,FIREID,GENVEG,LATI,LONGI,AREA,BMASS,CO2,CO,CH4,NMOC,H2,NOXasNO,SO2,PM25,TPM,TPC,OC,
    BC,NH3,NO,NO2,NMHC,PM10, ACET,ALK1,ALK2,ALK3,ALK4,ALK5,ARO1,ARO2,BALD,CCHO,CCO_OH,ETHENE,HCHO,
    HCN,HCOOH,HONO,ISOPRENE,MEK,MEOH,METHACRO,MGLY,MVK,OLE1,OLE2,PHEN,PROD2,RCHO,TRP1
    '''
    usecols=['DAY','POLYID','FIREID','GENVEG','LATI','LONGI','AREA','BMASS','CO','SO2','NH3','NMOC',
      'PM10','PM25','CH4','NO','NO2','HONO','CO2','HCHO']
    dtype = {'DAY': str, 'POLYID': str, 'FIREID': str, 'GENVEG': str}
    df = pd.read_csv(infile_name, skipinitialspace=True, index_col=False, usecols=usecols, dtype=dtype)
    '''
    for col in df.columns:
        if col not in ('DAY','GENVEG'):
            df[col] = df[col].str.split('D+').str[0].astype('f') * (10. ** df[col].str.split('D+').str[1].astype('i'))
    '''
    df.rename(columns={'DAY': 'day', 'GENVEG': 'process_id', 'LATI': 'latitude', 'LONGI': 'longitude', 
      'AREA': 'ACRESBURNED', 'PM25': 'PM25-PRI', 'PM10': 'PM10-PRI', 'FIREID': 'facility_id',
      'POLYID': 'unit_id'}, inplace=True) 
    # sqm to acres
    df['ACRESBURNED'] = df['ACRESBURNED'] * 0.000247105
    # Keep fires greater than 50 square meters
    df = df[df['ACRESBURNED'] > 0.012].copy()
    df = calc_mass(df)
    # 0.01 deg ~= 1 km or ~ 1 pixel; Round to 2 decimal for FIPS identification
    df[['longitude','latitude']] = df[['longitude','latitude']].round(2)
    print((len(df), sum(df['CO'])), flush=True)
    cols = ['facility_id','unit_id','process_id','latitude','longitude','day']
    df = df.groupby(cols , as_index=False).sum()
    print((len(df), sum(df['CO'])), flush=True)
    geo_id = na_shape()
    df['fips'] = df[['longitude','latitude']].apply(lambda row: geo_id.get_loc(row['longitude'], 
      row['latitude'], 'FIPS'), axis=1)
    df = fix_finn_fips(df)
    df.reset_index(inplace=True)
    df['date'] = df['day'].astype(int).apply(lambda day: set_date(year, day))
    df['country_cd'] = df['region_cd'].apply(get_country)
    df.loc[df['region_cd'].str.len() == 6, 'region_cd'] = df.loc[df['region_cd'].str.len() == 6, 'region_cd'].str[1:]
    # Non-phase specific WF
    df['scc'] = '2810001000'
    # Set ag fires based on ground veg: 1 = grass; 9 = crops
    df.loc[df['process_id'].astype(int).isin((1,9)), 'scc'] = '2801500000'
    df['monthnum'] = df['date'].apply(lambda x: int(x[4:6]))
    df['day'] = df['date'].apply(lambda x: 'dayval%s' %int(x[6:8]))
    df.drop(['date','index'], axis=1, inplace=True)
    cols = ['country_cd','facility_id','unit_id','monthnum','day','latitude','longitude',
      'region_cd','scc','process_id']
    df = pd.melt(df, id_vars=cols, var_name='poll', value_name='val')
    print(sum(df.loc[df['poll'] == 'CO', 'val']), flush=True)
    return df

def write_daily_ff10(day_df, fname, country, year):
    '''
    Format and write out the daily fires in FF10 daily format
    '''
    idx = ['country_cd','region_cd','facility_id','scc','poll','monthnum','process_id','unit_id']
    day_df = pd.pivot_table(day_df, values='val', index=idx, columns='day')
    day_df.fillna(0, inplace=True)
    day_df['monthtot'] = day_df.sum(axis=1).round(6)
    day_df.reset_index(inplace=True)
    day_df['rel_point_id'] = day_df['facility_id'].str[6:]
    null_cols = ['tribal_code','op_type_cd','calc_method','date_updated','comment']
    for col in null_cols:
        day_df[col] = ''
#    day_df.sort_values(['region_cd','facility_id','scc','poll','monthnum'])
    out_cols = ('country_cd','region_cd','tribal_code','facility_id','unit_id','rel_point_id','process_id',
      'scc','poll','op_type_cd','calc_method','date_updated','monthnum','monthtot','dayval1','dayval2',
      'dayval3','dayval4','dayval5','dayval6','dayval7','dayval8','dayval9','dayval10','dayval11',
      'dayval12','dayval13','dayval14','dayval15','dayval16','dayval17','dayval18','dayval19',
      'dayval20','dayval21','dayval22','dayval23','dayval24','dayval25','dayval26','dayval27',
      'dayval28','dayval29','dayval30','dayval31','comment')
    print('Unique daily fires written: %s' %day_df[['region_cd','facility_id']].drop_duplicates().shape[0], flush=True)
    days = ['dayval%s' %x for x in range(1,32)]
    day_df[days] = day_df[days].fillna(0).round(6)
    print('%s  %s' %(sum(day_df['monthtot']), sum(day_df[days].sum(axis=1))))
    country = cty_dict[country]
    for col in out_cols:
        if col not in list(day_df.columns):
            day_df[col] = ''
    with open(fname, 'w') as pday:
        pday.write('#FORMAT=FF10_DAILY_POINT\n#COUNTRY=%s\n#YEAR=%s\n' %(country, year))
        day_df.to_csv(pday, index=False, columns=out_cols)

def write_annual_ff10(day_df, fname, country, year):
    '''
    Write the annual FF10
    '''
    idx = ['country_cd','region_cd','facility_id','scc','poll','process_id','latitude',
      'longitude','unit_id']
    ann_inv = day_df.groupby(idx, as_index=False).sum()
    ann_inv.rename(columns={'val': 'ann_value'}, inplace=True)
    ann_inv['ann_value'] = ann_inv['ann_value'].round(6)
    ann_inv['rel_point_id'] = ann_inv['facility_id'].str[6:]
    ann_inv['stkhgt'] = '1'
    ann_inv['stkdiam'] = '1'
    ann_inv['stktemp'] = '1'
    ann_inv['stkflow'] = '1'
    ann_inv['stkvel'] = '1'
    ann_inv['facility_name'] = ann_inv['facility_id']
    ann_inv['data_set_id'] = 'EPA_FINN'
    ann_inv['calc_year'] = year
    null_cols = ('tribal_code','agy_facility_id','agy_unit_id','agy_rel_point_id','agy_process_id',
      'ann_pct_red','erptype','naics','ll_datum','stkhgt','stkdiam','stktemp','stkflow','stkvel',
      'horiz_coll_mthd','design_capacity','design_capacity_units','reg_codes','fac_source_type',
      'unit_type_code','control_ids','control_measures','current_cost','cumulative_cost',
      'projection_factor','submitter_id','calc_method','facil_category_code',
      'oris_facility_code','oris_boiler_id','ipm_yn','date_updated','fug_height',
      'fug_width_xdim','fug_length_ydim','fug_angle','zipcode','annual_avg_hours_per_year',
      'jan_value','feb_value','mar_value','apr_value','may_value','jun_value','jul_value','aug_value',
      'sep_value','oct_value','nov_value','dec_value','jan_pctred','feb_pctred','mar_pctred',
      'apr_pctred','may_pctred','jun_pctred','jul_pctred','aug_pctred','sep_pctred','oct_pctred',
      'nov_pctred','dec_pctred','comment')
    for col in null_cols:
        ann_inv[col] = ''
    out_cols = ('country_cd','region_cd','tribal_code','facility_id','unit_id','rel_point_id','process_id',
      'agy_facility_id','agy_unit_id','agy_rel_point_id','agy_process_id','scc','poll','ann_value',
      'ann_pct_red','facility_name','erptype','stkhgt','stkdiam','stktemp','stkflow','stkvel','naics','longitude',
      'latitude','ll_datum','horiz_coll_mthd','design_capacity','design_capacity_units','reg_codes',
      'fac_source_type','unit_type_code','control_ids','control_measures','current_cost',
      'cumulative_cost','projection_factor','submitter_id','calc_method','data_set_id',
      'facil_category_code','oris_facility_code','oris_boiler_id','ipm_yn','calc_year','date_updated',
      'fug_height','fug_width_xdim','fug_length_ydim','fug_angle','zipcode','annual_avg_hours_per_year',
      'jan_value','feb_value','mar_value','apr_value','may_value','jun_value','jul_value','aug_value',
      'sep_value','oct_value','nov_value','dec_value','jan_pctred','feb_pctred','mar_pctred',
      'apr_pctred','may_pctred','jun_pctred','jul_pctred','aug_pctred','sep_pctred','oct_pctred',
      'nov_pctred','dec_pctred','comment')
    country = cty_dict[country]
    for col in out_cols:
        if col not in list(ann_inv.columns):
            ann_inv[col] = ''
    print('  %s' %sum(ann_inv['ann_value']))
    with open(fname, 'w') as ptinv:
        ptinv.write('#FORMAT=FF10_POINT\n#COUNTRY=%s\n#YEAR=%s\n' %(country, year))
        ann_inv.to_csv(ptinv, index=False, columns=out_cols)

class GeoCode():
    def __init__(self, grid_mask, geo_to_fips):
        self._load_grid_mask(grid_mask)
        self._load_fips_xref(geo_to_fips)
        
    def _load_grid_mask(self, grid_mask):
        self.ncf = ncf.Dataset(grid_mask)
        self.geo = self.ncf.variables['GEOCODE'][:]
        self.tz = self.ncf.variables['TZONES'][:]

    def _load_fips_xref(self, geo_to_fips):
        with open(geo_to_fips) as f:
            self.fips = {}
            for l in f:
                if not l.startswith('geo'):
                    l = [cell.strip() for cell in l.strip().split(',')]
                    self.fips[l[0]] = l[1]

    def _get_code(self, lat, lon):
        row = int((lat + 90.)/0.1)
        if lon > 0:
            col = int((lon)/0.1)
        elif lon < 0:
            col = int((360. + lon)/0.1)
        elif lon == 0:
            col = 180
            print('WARNING: Longitude of exactly 0')
        geo = '%0.6d' %self.geo[0,0,row,col]
        tz = '%0.2d' %(self.tz[0,0,row,col] + 13)
        return '%s_%s' %(geo, tz)

    def get_fips(self, lat, lon):
        code = self._get_code(lat,lon)
        return self.fips[code]

def fill_geocodes(df, geo_ref):
    df['region_cd'] = df[['latitude','longitude']].apply(lambda row: \
      geo_ref.get_fips(row['latitude'],row['longitude']), axis=1).str[1:]
    return df

def roll_up_geo(df):
    '''
    Roll up the geocode data to lat/lon 1 decimal place for GEO fires
    This changes some of the EIS identifiers in the process
    '''
    df['latitude'] = df['latitude'].round(1)
    df['longitude'] = df['longitude'].round(1)
    df['process_id'] = 'c'
    cols = ['country_cd','monthnum','day','latitude','longitude','region_cd','scc','poll',
      'process_id','facility_id']
    df = df.groupby(cols, as_index=False).sum()
    df['rel_point_id'] = df['latitude'].astype(str) + df['longitude'].astype(str) 
    df['unit_id'] = df['day']
    return df
      
main()

