"""
Adapter-Plant-Declaration Adapter for Ingress
"""
import argparse
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Tuple
import logging
import logging.config
from configparser import ConfigParser
import pandas as pd

from osiris.apis.ingress import Ingress
from osiris.core.azure_client_authorization import ClientAuthorization

logger = logging.getLogger(__file__)


def retrieve_data(state: Dict, filename: str) -> Tuple[Optional[bytes], Dict]:
    """
    Retrieves the data from Adapter-Plant-Declaration.
    """
    logger.info('Running the Plant-Declaration Ingress Adapter')

    cols = ['aar', 'VrkGsrn', 'Kilde', 'vrk_ID', 'Vrkkortnavn', 'Prisomraade', 'Vaerkstype'
        , 'ElBrMWhLev', 'GJialtPerMWh'
        , 'ElBrMWh',  'AndelElProd', 'Bkode', 'RapGrp', 'SNAP', 'CO2KWh', 'SO2KWh'
        , 'NOxKWh', 'NmvocKWh', 'CH4KWh', 'COKWh', 'N2OKWh', 'PartiklerKWh', 'FlyveaskeKWh', 'SlaggeKWh'
        , 'AfsvovlKWh', 'AffaldKWh', 'Faktor200', 'Faktor125', 'CO2oprKWh', 'SCADA']

    ingest_data_df = pd.read_csv(filename, sep=";", header=0, encoding='ISO-8859-1'
                                 , usecols=cols
                                 , decimal=","
                                 # , index_col=0
                                 )
    ingest_data_df['aar'] = ingest_data_df['aar'].map(str)

    ingest_data = ingest_data_df.to_json(orient='records', date_format='iso').encode('UTF-8')
    return ingest_data, state


def __init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Ingress Adapter for Adapter-Plant-Declaration')

    parser.add_argument('--conf',
                        nargs='+',
                        default=['conf.ini', '/etc/osiris/conf.ini'],
                        help='setting the configuration file')
    parser.add_argument('--credentials',
                        nargs='+',
                        default=['credentials.ini', '/vault/secrets/credentials.ini'],
                        help='setting the credential file')

    return parser


def main():
    """
    Setups the ingress-api, retrieves state, uploads data to ingress-api, saves state after successful upload.
    """
    arg_parser = __init_argparse()
    args, _ = arg_parser.parse_known_args()

    config = ConfigParser()
    config.read(args.conf)
    credentials_config = ConfigParser()
    credentials_config.read(args.credentials)

    logging.config.fileConfig(fname=config['Logging']['configuration_file'],  # type: ignore
                              disable_existing_loggers=False)

    # To disable azure INFO logging from Azure
    if config.has_option('Logging', 'disable_logger_labels'):
        disable_logger_labels = config['Logging']['disable_logger_labels'].splitlines()
        for logger_label in disable_logger_labels:
            logging.getLogger(logger_label).setLevel(logging.WARNING)

    # Setup authorization
    client_auth = ClientAuthorization(tenant_id=credentials_config['Authorization']['tenant_id'],
                                      client_id=credentials_config['Authorization']['client_id'],
                                      client_secret=credentials_config['Authorization']['client_secret'])

    # Initialize the Ingress API
    ingress_api = Ingress(client_auth=client_auth,
                          ingress_url=config['Azure Storage']['ingress_url'],
                          dataset_guid=config['Datasets']['source'])

    # Get the state from last run.
    # - The state is kept in the ingress-guid as state.json, if it does not exist, an empty dict is returned
    state = ingress_api.retrieve_state()

    # Get the next data to upload
    data_to_ingest, state = retrieve_data(state,
                                          filename=config['Data']['filepath'] + config['Data']['filename'])

    # If no new data, return
    if data_to_ingest is None:
        logger.info('No new data to upload: Adapter-Plant-Declaration Ingress Adapter')
        return

    # There are 4 options to upload data, where the first 2 options cover most cases
    # Option 1: Upload to event time
    # - Use this option when
    #   - No transformation is needed afterward
    #   - No historic data is updated after ingestion to ingress
    # Option 2: Upload to ingress time
    # - Use this option when
    #   - A transformation is needed afterward
    #   - Historic data is updated after ingestion to ingress
    # Option 3: Upload non-json formatted data to event time
    # - This case is not used often - no sample code below
    # Option 3: Upload non-json formatted data to event time
    # - This case is not used often - no sample code below
    # Option 4: Upload non-json formatted data to ingress time
    # - This case is not used often - no sample code below - example is ikontrol-adapter

    file = BytesIO(data_to_ingest)
    file.name = 'data.json'
    # TODO: get event time from data
    event_time = '2020'
    # Set if schema validation is needed
    schema_validate = False

    # This call we raise Exception unless 201 is returned
    ingress_api.upload_json_file_event_time(file=file,
                                            event_time=event_time,
                                            schema_validate=schema_validate)
    # [END] Option 1

    # Save the state
    ingress_api.save_state(state)
    logger.info('Data successfully uploaded: Adapter-Plant-Declaration Ingress Adapter')


if __name__ == "__main__":
    main()
