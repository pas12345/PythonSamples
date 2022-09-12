from osiris.apis.egress import Egress
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.core.enums import Horizon
from configparser import ConfigParser

import datetime as dt
import pandas as pd

config = ConfigParser()
config.read('conf.ini')

#client_auth = ClientAuthorization(tenant_id=config['Authorization']['tenant_id'],
#                                  client_id=config['Authorization']['client_id'],
#                                  client_secret=config['Authorization']['client_secret'])
#
#egress = Egress(client_auth=client_auth,
#                egress_url=config['Egress']['url'],
#                dataset_guid=config['Egress']['plant_production_id'])
#
#start_day = dt.datetime(2021, 9, 24)
#end_day = start_day + dt.timedelta(days=1)

#json_response = egress.download_json_file(from_date="2021-08-01",
#                                           to_date="2021-08-02")

#pd.set_option('display.max_rows', 00)
#pd.set_option('display.max_columns', 500)
#pd.set_option('display.width', 1000)

#df = pd.DataFrame(json_response)
#print(df)
#df.to_csv('data.csv', index=False)
