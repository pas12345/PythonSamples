import json
import base64
import pytz
from datetime import datetime, timedelta
import pandas as pd

import requests


class SAPService:
    baseurl = f"http://10.178.4.36:8002/eds_service"

    def get_data(self, start: datetime, service:str, method: str, aggregate: str, select: str):
        end = start + timedelta(days=1)

        end = end.astimezone(pytz.utc)
        start = start.astimezone(pytz.utc)

        start_str = start.strftime("%Y.%m.%d %H:00:00")
        end_str = end.strftime("%Y.%m.%d %H:00:00")

        periodparam = f"(IP_FROM_TIME='{start_str}',IP_TO_TIME='{end_str}', AGGREGATION_LEVEL='{aggregate}')"
        url = f"{SAPService.baseurl}/{service}.xsodata/{method}{periodparam}/Execute?$format=json&$select={select}"

        # Extract
        pwd = "EDS:EDS2019eds"
        encoded_u = base64.b64encode(pwd.encode()).decode()
        headers = {"Authorization": "Basic %s" % encoded_u}

        res = requests.get(url, headers=headers)
        res = res.content.decode()
        res = json.loads(res)

        # Transform
        df = pd.DataFrame(res["d"]['results'])
        if '__metadata' in df.columns:
            df.drop('__metadata', axis=1, inplace=True)
        return df
