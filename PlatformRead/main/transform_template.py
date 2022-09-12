from osiris.apis.egress import Egress
from osiris.core.azure_client_authorization import ClientAuthorization
from configparser import ConfigParser
import pandas as pd
import datetime as dt
from main.eds import EDS

config = ConfigParser()
config.read('conf.ini')

client_auth = ClientAuthorization(tenant_id=config['Authorization']['tenant_id'],
                                  client_id=config['Authorization']['client_id'],
                                  client_secret=config['Authorization']['client_secret'])

egress = Egress(client_auth=client_auth,
                egress_url=config['Egress']['url'],
                dataset_guid=config['Egress']['netloss_id'])

start_time = dt.datetime(2021, 11, 5)
end_time = dt.datetime(2021, 11, 6)

datetime_start = EDS.localtime_to_utc(start_time, 'Europe/Copenhagen').strftime('%Y-%m-%dT%H')
datetime_end = EDS.localtime_to_utc(end_time, 'Europe/Copenhagen').strftime('%Y-%m-%dT%H')


json_content = egress.download_json_file(from_date=datetime_start,
                                         to_date=datetime_end)
# We only show the first entry here
#records = json_content

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.2f}'.format

df = pd.DataFrame(json_content)

df.loc[(df['GridAreaMarket'] == 'X'), 'Cat'] = 'GridAreaMarket'
df.loc[(df['GridAreaTSONet'] == 'X'), 'Cat'] = 'GridAreaTSONet'
df.loc[(df['GridAreaInterConnector'] == 'X'), 'Cat'] = 'GridAreaInterConnector'
df.fillna(0.0)

df = df[["TimestampUTC", "PriceArea", "Cat", "Qnt"]]
df = df.groupby(["TimestampUTC", "PriceArea", "Cat"]).sum()
print(df)
#df.set_index(["TimestampUTC", "MunicipalityCode", "Cat"]).unstack(level=-1)
#df = df.set_index(["TimestampUTC", "MunicipalityCode", "Cat"])


df = df.pivot_table(index=["TimestampUTC", "PriceArea"], columns="Cat", values="Qnt")

#df = df.groupby(['TimestampUTC,', 'Cat']).sum()
#print(df.head(10))
df.to_csv("c:\\temp\\wind.csv", sep=";", decimal=",")

total = df.sum()
print(total)



