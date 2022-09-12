import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import isodate
from datetime import datetime
import json


datafile = r'c:\temp\data.json'
# date_cols = ['TimestampUTC']


data = pd.read_csv(datafile, sep=";", header = 0, encoding = "utf-8"
        , decimal=","
        #, index_col=0
        )

print(data.head(2))
data = data.sum()
print(data.head(2))
