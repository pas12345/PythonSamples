import os
import pytz
import json
import typing
import logging
import requests
import typing
from configparser import ConfigParser
import pandas as pd
import datetime as dt
from main.eds import EDS

config = ConfigParser()
config.read('conf.ini')

eds = EDS(base_url=config['Eds']['test_url'])


datetime_start = EDS.localtime_to_utc(datetime=dt.datetime(2021, 8, 1, 0, 0), tzname='Europe/Copenhagen')
datetime_end = EDS.localtime_to_utc(datetime=dt.datetime(2021, 8, 2, 0, 0), tzname='Europe/Copenhagen')
sql_query = f"""SELECT "HourUTC",
        "MunicipalityNo",
        "SolarMWh"
        "OffshoreWindLt100MW_MWh", 
        "OffshoreWindGe100MW_MWh", 
        "OnshoreWindMWh",
        "SolarMWh", "ThermalPowerMWh"
        FROM "productionmunicipalityhour"
        WHERE '{datetime_start.strftime('%Y-%m-%dT%H:%M:%SZ')}' <= "HourUTC"
        AND "HourUTC" < '{datetime_end.strftime('%Y-%m-%dT%H:%M:%SZ')}'
         """

response = eds.sql_query(sql_query=sql_query)
records = response['result']['records']

pd.set_option('display.max_rows', 00)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.2f}'.format

df = pd.DataFrame(records)

df.to_csv("c:\\temp\\productionmunicipalityhour.csv", sep=";", decimal=",")
df.fillna(0.0)
#df = df[df['HourUTC']=='2021-08-01T20:00:00']
#df = df[df['MunicipalityNo']=='101']
#df = df[df['OffshoreWindLt100MW_MWh'] > 0]

#df = df.groupby(['HourUTC']).sum()
print(df)

df = df.sum()
print(df.head(50))
#print(df.sum().head(50))

