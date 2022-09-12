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

eds = EDS(base_url=config['Eds']['test_url'])

datetime_start = EDS.localtime_to_utc(dt.datetime(2021, 8, 1, 0, 0), 'Europe/Copenhagen')
datetime_end = EDS.localtime_to_utc(dt.datetime(2021, 8, 2, 0, 0), 'Europe/Copenhagen')

#query Dataset
#{
#    electricitysupplierspergridarea(where: {Month: {_gte: "2021-10-01T00:00:00.000Z", _lt: "2021-10-02T00:00:00.000Z"}},
#    order_by: {Month: desc}, limit: 100, offset: 0)  {Month, GridCompany, ActiveSupplierPerGridArea}
#}

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