"""
TODO: add appropriate docstring
"""
import logging
import logging.config
import argparse
from configparser import ConfigParser

from osiris.core.enums import TimeResolution
from osiris.core.io import PrometheusClient
from osiris.core.instrumentation import TracerConfig

from .transform import TransformDeclarationProduction


logger = logging.getLogger(__file__)


def __init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Transform Declarationproduction from ingress to event time \
                                                 on the configured time resolution')

    parser.add_argument('--conf',
                        nargs='+',
                        default=['conf.ini', '/etc/osiris/conf.ini'],
                        help='setting the configuration file')
    parser.add_argument('--credentials',
                        nargs='+',
                        default=['credentials.ini', '/vault/secrets/credentials.ini'],
                        help='setting the credential file')

    return parser



def __get_pipeline(config, credentials_config) -> TransformDeclarationProduction:
    account_url = config['Azure Storage']['account_url']
    filesystem_name = config['Azure Storage']['filesystem_name']

    tenant_id = credentials_config['Authorization']['tenant_id']
    client_id = credentials_config['Authorization']['client_id']
    client_secret = credentials_config['Authorization']['client_secret']

    tracer_config = TracerConfig(config['Jaeger Agent']['name'],
                                 config['Jaeger Agent']['reporting_host'],
                                 config['Jaeger Agent']['reporting_port'])

    prometheus_client = PrometheusClient(environment=config['Prometheus']['environment'],
                                         name=config['Prometheus']['name'],
                                         hostname=config['Prometheus']['hostname'])

    return TransformDeclarationProduction(storage_account_url=account_url,
                           filesystem_name=filesystem_name,
                           tenant_id=tenant_id,
                           client_id=client_id,
                           client_secret=client_secret,
                           config=config,
                           tracer_config=tracer_config,
                           prometheus_client=prometheus_client)


def main():
    """
    The main function which runs the transformation.
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

    logger.info('Running the declaration-production transformation.')

    pipeline = __get_pipeline(config=config, credentials_config=credentials_config)
    pipeline.transform()

    logger.info('Finished running the declaration-production transformation.')


if __name__ == '__main__':
    main()
