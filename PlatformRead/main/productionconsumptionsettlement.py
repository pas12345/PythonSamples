import os
import pytz
import json
import typing
import logging
import requests
from configparser import ConfigParser
import typing
import pandas as pd
import datetime as dt
from main.eds import EDS

config = ConfigParser()
config.read('conf.ini')
print(config)
eds = EDS(base_url=config['eds']['test_url'])

datetime_start = EDS.localtime_to_utc(dt.datetime(2021, 8, 1, 0, 0), 'Europe/Copenhagen')
datetime_end = EDS.localtime_to_utc(dt.datetime(2021, 8, 2, 0, 0), 'Europe/Copenhagen')

sql_query = f"""SELECT "HourUTC",
"CentralPowerMWh",
"LocalPowerMWh",
"CommercialPowerMWh",
        "OnshoreWindLt50kW_MWh",
        "OnshoreWindGe50kW_MWh",
        "OffshoreWindLt100MW_MWh",
        "OffshoreWindGe100MW_MWh",
"SolarPowerLt10kW_MWh",
"SolarPowerGe10Lt40kW_MWh",
"SolarPowerGe40kW_MWh",
"SolarPowerSelfConMWh",        
"SolarPowerLt10kW_MWh"+"SolarPowerGe10Lt40kW_MWh"+"SolarPowerGe40kW_MWh"+"SolarPowerSelfConMWh" as solar,  
"HydroPowerMWh"
        FROM "productionconsumptionsettlement"
        WHERE "HourUTC" >= '{datetime_start.strftime('%Y-%m-%dT%H:%M:%SZ')}'
        AND "HourUTC" < '{datetime_end.strftime('%Y-%m-%dT%H:%M:%SZ')}'
        order by "HourUTC" """


#"OffshoreWindLt100MW_MWh",
#"OffshoreWindGe100MW_MWh",
#"HydroPowerMWh"

response = eds.sql_query(sql_query=sql_query)
records = response['result']['records']

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.6f}'.format

df = pd.DataFrame(records)
df["Onshore"] = df["OnshoreWindLt50kW_MWh"]+df["OnshoreWindGe50kW_MWh"]
#df = df.groupby(['HourUTC']).sum()
df.to_csv("c:\\temp\\productionconsumptionsettlement.csv", sep=";", decimal=",")
df.fillna(0.0)


df = df.sum()

#print(df.keys())

#df['qnt'] = df['solarpowerge10lt40kw_mwh'] \
#            + df['solarpowerge40kw_mwh'] + \
#            df['solarpowerselfconmwh'] + \
#            df['solarpowerlt10kw_mwh']
# df = df.groupby(['HourUTC'])['OnshoreWindMWh'].sum()
print(df.head(50))

# df = df.groupby(['HourUTC'])['OffshoreWindGe100MW_MWh','OnshoreWindMWh'].sum()
#print(df.head(50))

