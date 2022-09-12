"""
Adb-Masterdata Adapter for Ingress
"""

from typing import Optional

from osiris.core.configuration import ConfigurationWithCredentials
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.adapters.ingress_adapter import IngressAdapter

from .dbmanager import DbManager
from pandas import DataFrame
import pandas as pd
import sys

configuration = ConfigurationWithCredentials(__file__)
config = configuration.get_config()
credentials_config = configuration.get_credentials_config()
logger = configuration.get_logger()


class AdbmasterdataAdapter(IngressAdapter):
    """
    The Adb-Masterdata Adapter.
    Implements the retrieve_data method.
    """

    def __init__(self, ingress_url: str,  # pylint: disable=too-many-arguments
                 tenant_id: str,
                 client_id: str,
                 client_secret: str,
                 dataset_guid: str,
                 adb_hostname: str,
                 oracle_sid: str,
                 user: str,
                 password: str):
        client_auth = ClientAuthorization(tenant_id, client_id, client_secret)
        super().__init__(client_auth=client_auth, ingress_url=ingress_url, dataset_guid=dataset_guid)
        self.dbmanager = DbManager(adb_hostname, oracle_sid, user, password)

    def retrieve_data(self) -> Optional[bytes]:
        """
        Retrieves the data from Adb-Masterdata.
        """
        logger.debug('Running the ADB-Masterdata Ingress Adapter')

        filename = f'e:\\data\\Plants.csv'
        dataframe = pd.read_csv(filename, sep=';', encoding='iso-8859-1')

        dataframe = self.__convert_data(dataframe)

        sqlcmd = """SELECT DISTINCT pra.PRA_GSRN as gsrn, pra.PRA_KORT_NAVN AS turbine_short_name,
                pra.PRA_NAVN AS turbine_name, pra.PRA_KATEGORI AS turbine_type, parents.PRA_GSRN AS parent_gsrn,
                pra.PRA_IDRIFT AS in_service, pra.PRA_AFMELDT AS out_service, pra.PRA_BBR_KOMMUNE AS bbr_municipal,
                pra.PRA_PLAC_TYPE AS placement, pra.PRA_UTM_X AS utm_x, pra.PRA_UTM_Y AS utm_y,
                pra.PRA_UTM_PRECISION AS utm_precision, pra.PRA_INST_EL_KW AS capacity_kw, pra.PRA_MODEL AS model,
                pra.PRA_FABRIKAT AS manufacturer, pra.PRA_ROTOR AS rotor_diameter, 
                pra.PRA_NAV_HOEJDE AS navhub_height,
                pra.PRA_FULDLAST_SALDO AS fullload_amount, pra.PRA_FULDLAST_KVOTE AS fullload_quota,
                pra.PRA_FULDLAST_TIDSPUNKT AS fullload_datetime, bal.BA_KORT_NAVN as actor_short_name,
                bal.BA_FULDT_NAVN as actor_name,
                to_char(LEAST(pra.valid_til, tsp.valid_til, bal.valid_til), 'yyyy-MM-DD HH24:MI:SS') as valid_to,
                to_char(GREATEST(pra.valid_fra, tsp.valid_fra, bal.valid_fra), 'yyyy-MM-DD HH24:MI:SS') AS valid_from
            FROM ADB.tab_anl_vindmoelle pra
                LEFT OUTER JOIN adb.ts_per tsp
                    ON tsp.pra_c106 = pra.stmp_id
                LEFT OUTER JOIN adb.tab_akt_balanceansvarlig bal
                    ON bal.stmp_id = tsp.ba_c14
                LEFT OUTER JOIN ADB.tab_anl_vindmoelle parents
                    ON parents.ID = pra.PRA_TILH_ANLAEG
            WHERE pra.pra_kategori IN('P', 'H', 'W', 'M')
                AND(tsp.tso_c189 IS NOT NULL
                OR pra.pra_kategori = 'M')
                ORDER BY gsrn, valid_from DESC"""

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


def ingest_adb_masterdata_data():
    """
    Setups the adapter and runs it.
    """
    adapter = AdbmasterdataAdapter(config['Azure Storage']['ingress_url'],
                                   credentials_config['Authorization']['tenant_id'],
                                   credentials_config['Authorization']['client_id'],
                                   credentials_config['Authorization']['client_secret'],
                                   config['Datasets']['source'],
                                   config['Oracle Server']['adb_hostname'],
                                   config['Oracle Server']['oracle_sid'],
                                   credentials_config['Oracle Server']['user'],
                                   credentials_config['Oracle Server']['password']
                                   )

    adapter.upload_json_data_event_time(False)
    print('Finished')


if __name__ == "__main__":
    ingest_adb_masterdata_data()
