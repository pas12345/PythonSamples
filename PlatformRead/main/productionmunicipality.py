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

env = "eds_prod"
alias = "communityproduction"
eds = EDS(base_url=config[env]['url'], auth=config[env]['secret'])

datetime_start = EDS.localtime_to_utc(dt.datetime(2021, 8, 1, 0, 0), 'Europe/Copenhagen')
datetime_end = EDS.localtime_to_utc(dt.datetime(2021, 9, 1, 0, 0), 'Europe/Copenhagen')

sql_query = f"""SELECT
        "Month",
        "OnshoreWindPower",
        "OnshoreWindPower",
        "OffshoreWindPower",
        "SolarPower",
        "CentralPower",
        "DecentralPower"
        FROM "communityproduction"
        WHERE "Month" >= '{datetime_start.strftime('%Y-%m-%d')}'
        AND "Month" < '{datetime_end.strftime('%Y-%m-%d')}' """

# sql_query = f"""SELECT "MunicipalityNo", "SolarPower"
#        FROM "communityproduction"
#        WHERE "Month" >= '{datetime_start.strftime('%Y-%m-%d')}'
#        AND "Month" < '{datetime_end.strftime('%Y-%m-%d')}' """


records = eds.sql_query(sql_query=sql_query)
#records = response['result']['records']

pd.set_option('display.max_rows', 00)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.2f}'.format

df = pd.DataFrame(records)
df.fillna(0.0)
df.to_csv("c:\\temp\\communityproduction.csv", sep=";", decimal=",")
print(df.head(50))

