"""
TODO: add appropriate docstring
"""
import argparse
import sys
from datetime import datetime

from osiris.core.configuration import ConfigurationWithCredentials
from osiris.core.enums import TimeResolution
from osiris.core.io import PrometheusClient

from .transform import TransformPlantproduction

configuration = ConfigurationWithCredentials(__file__)
config = configuration.get_config()
credentials_config = configuration.get_credentials_config()
logger = configuration.get_logger()


def __init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='TODO: add description')

    parser.add_argument('--ingress_time', type=str, default=None, help='the ingress time to start the ingress from.')

    return parser


def __get_pipeline() -> TransformPlantproduction:
    account_url = config['Azure Storage']['account_url']
    filesystem_name = config['Azure Storage']['filesystem_name']

    tenant_id = credentials_config['Authorization']['tenant_id']
    client_id = credentials_config['Authorization']['client_id']
    client_secret = credentials_config['Authorization']['client_secret']

    source = config['Datasets']['source']
    destination = config['Datasets']['destination']
    time_resolution = TimeResolution[config['Datasets']['time_resolution']]
    max_files = int(config['Pipeline']['max_files'])

    prometheus_hostname = config['Prometheus']['hostname']
    prometheus_environment = config['Prometheus']['environment']
    prometheus_name = config['Prometheus']['name']
    prometheus_client = PrometheusClient(environment=prometheus_environment,
                                         name=prometheus_name,
                                         hostname=prometheus_hostname)

    try:
        return TransformPlantproduction(storage_account_url=account_url,
                               filesystem_name=filesystem_name,
                               tenant_id=tenant_id,
                               client_id=client_id,
                               client_secret=client_secret,
                               source_dataset_guid=source,
                               destination_dataset_guid=destination,
                               time_resolution=time_resolution,
                               max_files=max_files,
                               prometheus_client=prometheus_client)
    except Exception as error:  # noqa pylint: disable=broad-except
        logger.error('Error occurred while initializing pipeline: %s', error)
        sys.exit(-1)


def main():
    """
    The main function which runs the transformation.
    """
    argparser = __init_argparse()
    args, _ = argparser.parse_known_args()
    pipeline = __get_pipeline()
    logger.info('Running the plant-production transformation.')
    try:
        if args.ingress_time and args.ingress_time != '':
            ingress_time = datetime.strptime(args.ingress_time, '%Y-%m-%dT%H')
            pipeline.transform(ingress_time)
        else:
            pipeline.transform()
    except Exception as error:  # noqa pylint: disable=broad-except
        logger.error('Error occurred while running pipeline: %s', error)
        sys.exit(-1)

    logger.info('Finished running the plant-production transformation.')


if __name__ == '__main__':
    main()
