"""
Transformation of Neptun masterdata
"""
import sys
import logging
import logging.config
from configparser import ConfigParser

from osiris.core.enums import TimeResolution
from osiris.core.io import PrometheusClient
from osiris.core.instrumentation import TracerConfig

from .transform import TransformNeptunmasterdata


logger = logging.getLogger(__file__)


def __get_pipeline(config, credentials_config) -> TransformNeptunmasterdata:
    account_url = config['Azure Storage']['account_url']
    filesystem_name = config['Azure Storage']['filesystem_name']

    tenant_id = credentials_config['Authorization']['tenant_id']
    client_id = credentials_config['Authorization']['client_id']
    client_secret = credentials_config['Authorization']['client_secret']

    source = config['Datasets']['source']
    destination = config['Datasets']['destination']
    time_resolution = TimeResolution[config['Datasets']['time_resolution']]
    max_files = int(config['Pipeline']['max_files'])

    tracer_config = TracerConfig(config['Jaeger Agent']['name'],
                                 config['Jaeger Agent']['reporting_host'],
                                 config['Jaeger Agent']['reporting_port'])

    prometheus_client = PrometheusClient(environment=config['Prometheus']['environment'],
                                         name=config['Prometheus']['name'],
                                         hostname=config['Prometheus']['hostname'])

    try:
        return TransformNeptunmasterdata(storage_account_url=account_url,
                               filesystem_name=filesystem_name,
                               tenant_id=tenant_id,
                               client_id=client_id,
                               client_secret=client_secret,
                               source_dataset_guid=source,
                               destination_dataset_guid=destination,
                               time_resolution=time_resolution,
                               max_files=max_files,
                               tracer_config=tracer_config,
                               prometheus_client=prometheus_client)
    except Exception as error:  # noqa pylint: disable=broad-except
        logger.error('Error occurred while initializing pipeline: %s', error)
        sys.exit(-1)


def main():
    """
    The main function which runs the transformation.
    """
    config = ConfigParser()
    config.read(['conf.ini', '/etc/osiris/conf.ini'])
    credentials_config = ConfigParser()
    credentials_config.read(['credentials.ini', '/vault/secrets/credentials.ini'])

    logging.config.fileConfig(fname=config['Logging']['configuration_file'],  # type: ignore
                              disable_existing_loggers=False)

    pipeline = __get_pipeline(config, credentials_config)
    logger.info('Running the neptun-masterdata transformation.')
    try:
        pipeline.transform()
    except Exception as error:  # noqa pylint: disable=broad-except
        logger.error('Error occurred while running pipeline: %s', error)
        sys.exit(-1)

    logger.info('Finished running the neptun-masterdata transformation.')


if __name__ == '__main__':
    main()
