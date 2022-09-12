"""
Module containing the SAP service
"""
import base64
from datetime import datetime

import pandas as pd
import requests


# pylint: disable=too-few-public-methods
class SAPService:
    """
    Wraps calls to the SAP service.
    """

    def __init__(self, sap_service_url: str, service: str, auth_api_key: str):
        self.sap_service_url = sap_service_url
        self.service = service
        self.base64_auth_api_key = base64.b64encode(auth_api_key.encode()).decode()

    def get_data_as_dataframe(self, start_date: datetime, end_date:  # pylint: disable=too-many-arguments
                              datetime, method: str, aggregate: str, query: str):
        """
        Returns data corresponding to the given query and from the specified time period.
        """

        start_date_str = start_date.strftime("%Y.%m.%d 00:00:00")
        end_date_str = end_date.strftime("%Y.%m.%d 00:00:00")

        period_params = f"(IP_FROM_TIME='{start_date_str}',IP_TO_TIME='{end_date_str}',AGGREGATION_LEVEL='{aggregate}')"
        url = f"{self.sap_service_url}/{self.service}.xsodata/{method}{period_params}/" + \
              f"Execute?$format=json&$select={query}"

        headers = {'Authorization': f'Basic {self.base64_auth_api_key}'}
        response = requests.get(url, headers=headers)
        if response.ok:
            data = response.json()

            dataframe = pd.DataFrame(data["d"]['results'])
            if '__metadata' in dataframe.columns:
                dataframe.drop('__metadata', axis=1, inplace=True)
            return dataframe
        else:
            return None
