import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import isodate
from datetime import datetime
import json


datafile = r'c:\temp\data.json'
# date_cols = ['TimestampUTC']


data = pd.read_json(datafile, encoding = "utf-8"
        #, index_col=0
        )

print(data.head(2))
data.to_csv("c:\\temp\\scada_plant.csv", sep=";", decimal=",")
