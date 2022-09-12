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

env = "eds_prod"
alias = "communityproduction"
eds = EDS(base_url=config[env]['url'], auth=config[env]['secret'])

datetime_start = EDS.localtime_to_utc(dt.datetime(2021, 7, 31, 0, 0), 'Europe/Copenhagen')
datetime_end = EDS.localtime_to_utc(dt.datetime(2021, 9, 1, 2, 0), 'Europe/Copenhagen')

sql_query = f"""SELECT
        "_id"
        FROM "{alias}"
        WHERE "Month" >= '{datetime_start.strftime('%Y-%m-%d')}'
        AND "Month" < '{datetime_end.strftime('%Y-%m-%d')}' """

response = eds.sql_query(sql_query=sql_query)
ids = []
for x in response:
    ids.append(x['_id'])

if len(ids) > 0:
    resource_id = eds.sql_resource_id(alias = alias)
    rows = eds.sql_delete(resource_id, ids)
    print("Rows deleted:" + str(rows))
else:
    print("nothing found")

