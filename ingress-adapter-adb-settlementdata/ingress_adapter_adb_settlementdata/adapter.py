"""
Adb-Settlementdata Adapter for Ingress
"""

from typing import Optional

from osiris.core.configuration import ConfigurationWithCredentials
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.adapters.ingress_adapter import IngressAdapter

from pandas import DataFrame
import pandas as pd
import sys

configuration = ConfigurationWithCredentials(__file__)
config = configuration.get_config()
credentials_config = configuration.get_credentials_config()
logger = configuration.get_logger()


class AdbsettlementdataAdapter(IngressAdapter):
    """
    The Adb-Settlementdata Adapter.
    Implements the retrieve_data method.
    """

    def __init__(self, ingress_url: str,  # pylint: disable=too-many-arguments
                 tenant_id: str,
                 client_id: str,
                 client_secret: str,
                 dataset_guid: str):
        client_auth = ClientAuthorization(tenant_id, client_id, client_secret)
        super().__init__(client_auth=client_auth, ingress_url=ingress_url, dataset_guid=dataset_guid)

    def retrieve_data(self) -> Optional[bytes]:
        """
        Retrieves the data from Adb-Settlementdata.
        """
        logger.debug('Running the Adb-Settlementdata Ingress Adapter')

        filename = f'e:\\data\\Plants.csv'
        dataframe = pd.read_csv(filename, sep=';', encoding='iso-8859-1')

        dataframe = self.__convert_data(dataframe)

        return dataframe.to_json(orient='records', date_format='iso').encode('UTF-8')

    @staticmethod
    def __convert_data(dataframe: DataFrame):
        # 2021.06.30 23:00:00
        return dataframe

    @staticmethod
    def get_event_time() -> str:
        return ""

    @staticmethod
    def get_filename() -> str:
        # Here is an example for a naming schema for json data:
        # return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ') + '.json'

        return 'test.data'


def ingest_adb_settlementdata_data():
    """
    Setups the adapter and runs it.
    """
    adapter = AdbsettlementdataAdapter(config['Azure Storage']['ingress_url'],
                                       credentials_config['Authorization']['tenant_id'],
                                       credentials_config['Authorization']['client_id'],
                                       credentials_config['Authorization']['client_secret'],
                                       config['Datasets']['source'])

    adapter.upload_json_data_event_time(False)
    print('Finished')


if __name__ == "__main__":
    ingest_adb_settlementdata_data()
