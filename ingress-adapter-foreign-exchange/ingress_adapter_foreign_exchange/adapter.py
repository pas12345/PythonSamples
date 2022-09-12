"""
Foreign Exchange Adapter for Ingress
"""
from typing import Optional
from datetime import datetime, timedelta

from osiris.core.configuration import ConfigurationWithCredentials
from osiris.adapters.ingress_adapter import IngressAdapter

from pandas import DataFrame
import pandas as pd
import sys

from .sap_service import SAPService

configuration = ConfigurationWithCredentials(__file__)
config = configuration.get_config()
credentials_config = configuration.get_credentials_config()
logger = configuration.get_logger()


class ForeignExchangeAdapter(IngressAdapter):
    """
    The Foreign-exchange Adapter.
    Implements the retrieve_data method.
    """
    def __init__(self, ingress_url: str,  # pylint: disable=too-many-arguments
                 tenant_id: str,
                 client_id: str,
                 client_secret: str,
                 dataset_guid: str,
                 sap_service_url: str,
                 sap_auth_api_key: str,
                 start_date: datetime):

        self.start_date = datetime( start_date.year, start_date.month, start_date.day)
        self.end_date = self.start_date + timedelta(days=1)
        super().__init__(ingress_url, tenant_id, client_id, client_secret, dataset_guid)

        self.service = SAPService(sap_service_url, 'eds_service', sap_auth_api_key)

    def retrieve_data(self) -> Optional[bytes]:
        """
        Retrieves the data from foreign-exchange.
        """
        logger.debug('Running the Foreign-exchange Ingress Adapter')

        select = "UTC_HOUR_TEXT_FULL,FOREIGN_CONNECTION,FOREIGN_IMPORT_EKSPORT,FOREIGN_PRICE_AREA," + \
                 "FOREIGN_CONNECTED_AREA,NETTO_VALUE&$filter=FOREIGN_PLACEMENT eq 'DK'"

        dataframe = self.service.get_data_as_dataframe(self.start_date, self.end_date, 'FOREIGN_EXCHANGE', 'QUARTER', select)

        if dataframe.empty:
            return None

        dataframe = self.__convert_data(dataframe)

        return dataframe.to_json(orient='records', date_format='iso').encode('UTF-8')

    @staticmethod
    def __convert_data(dataframe: DataFrame):
        # 2021.06.30 23:00:00
        dataframe['TimestampUTC'] = pd.to_datetime(dataframe['UTC_HOUR_TEXT_FULL'], format='%Y.%m.%d %H:%M:%S')
        dataframe['NETTO_VALUE'] = dataframe['NETTO_VALUE'].astype(float)

        dataframe.rename(columns={'FOREIGN_CONNECTION': 'Connection',
                                   'NETTO_VALUE': 'Qnt'}, inplace=True)

        dataframe['InArea'] = dataframe['FOREIGN_PRICE_AREA']\
            .where(dataframe['FOREIGN_IMPORT_EKSPORT'] == 'Import', dataframe['FOREIGN_CONNECTED_AREA'])
        dataframe['OutArea'] = dataframe['FOREIGN_PRICE_AREA']\
            .where(dataframe['FOREIGN_IMPORT_EKSPORT'] == 'Eksport', dataframe['FOREIGN_CONNECTED_AREA'])

        dataframe['Qnt'] = dataframe['Qnt'].abs()
        dataframe.drop('FOREIGN_IMPORT_EKSPORT', axis=1, inplace=True)
        dataframe.drop('FOREIGN_CONNECTED_AREA', axis=1, inplace=True)
        dataframe.drop('FOREIGN_PRICE_AREA', axis=1, inplace=True)
        dataframe.drop('UTC_HOUR_TEXT_FULL', axis=1, inplace=True)

        return dataframe

    @staticmethod
    def get_filename() -> str:
        return 'data.json'

    @staticmethod
    def get_event_time() -> str:
        return start_date.strftime("%Y-%m-%d")


def ingest_foreign_exchange_data(start_date: datetime):
    """
    Setups the adapter and runs it.
    """
    adapter = ForeignExchangeAdapter(config['Azure Storage']['ingress_url'],
                                     credentials_config['Authorization']['tenant_id'],
                                     credentials_config['Authorization']['client_id'],
                                     credentials_config['Authorization']['client_secret'],
                                     config['Datasets']['source'],
                                     config['SAP Server']['server_url'],
                                     credentials_config['SAP Server']['auth_api_key'],
                                     start_date)

    adapter.upload_json_data_event_time(False)

    print('Finished')


if __name__ == "__main__":
    data_until = datetime.utcnow() - timedelta(days=8)
    end_date = data_until
    start_date = data_until - timedelta(days=3)
    if (len(sys.argv) > 1):
        start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d")
    if (len(sys.argv) > 2):
        dt = datetime.strptime(sys.argv[2], "%Y-%m-%d")
        if (dt < data_until):
            end_date = dt

    print(start_date.strftime("%Y-%m-%d") + ' - ' + end_date.strftime("%Y-%m-%d") )
    while start_date < end_date:
        print( start_date.strftime("%Y-%m-%d"))
        ingest_foreign_exchange_data(start_date)
        start_date += timedelta(days=1)

        dataframe.rename(columns={'FOREIGN_CONNECTION': 'Connection',
                                   'NETTO_VALUE': 'Qnt'}, inplace=True)

