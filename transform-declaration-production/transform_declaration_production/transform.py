"""
Module to handle pipeline for timeseries
"""
import logging
import json
from abc import ABC
from datetime import timedelta, datetime
import pandas as pd
import io
from configparser import ConfigParser

import apache_beam as beam
import apache_beam.transforms.core as beam_core
from apache_beam.options.pipeline_options import PipelineOptions

from osiris.core.enums import TimeResolution
from osiris.pipelines.azure_data_storage import Dataset
from osiris.core.instrumentation import TracerClass, TracerConfig, TracerDoFn
from osiris.pipelines.file_io_connector import DatalakeFileSource, FileBatchController
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.core.io import PrometheusClient

from transform_declaration_production.hydroproduction import HydroProduction
from transform_declaration_production.plantdeclaration import PlantDeclaration
from transform_declaration_production.plantproduction import PlantProduction
from transform_declaration_production.solarproduction import SolarProduction
from transform_declaration_production.windproduction import WindProduction
from transform_declaration_production.co2calculation import CO2Calculation


logger = logging.getLogger(__file__)

class _UploadEventsToStorage(beam_core.DoFn, ABC):
    def __init__(self, dataset):
        super().__init__()

        self.dataset = dataset

    def process(self, element, *args, **kwargs):
        period, connection, data = element['declaration']

        path = f'year={period.year}/month={period.month:02d}/day={period.day:02d}/data.parquet'

        # This is needed when transforming to parquet
        # - The index is not kept from DataFrame to Parquet file
        # - We reset index to remove it
        data['UTC time'] = data.index
        data['UTC time'] = data['UTC time'].dt.strftime('%Y-%m-%dT%H:%M')
        data.reset_index(drop=True, inplace=True)

        bytes_io_file = io.BytesIO()
        data.to_parquet(bytes_io_file, engine='pyarrow', compression='snappy')
        bytes_io_file.seek(0)

        self.dataset.upload_file(path, bytes_io_file)

        return [element]


class TransformDeclarationProduction:
    """
    TODO: add appropriate docstring
    """

    # pylint: disable=too-many-arguments, too-many-instance-attributes, too-few-public-methods
    def __init__(self, storage_account_url: str, filesystem_name: str, tenant_id: str, client_id: str,
                 client_secret: str,
                 config: ConfigParser,
                 tracer_config: TracerConfig, prometheus_client: PrometheusClient):
        """
        :param storage_account_url: The URL to Azure storage account.
        :param filesystem_name: The name of the filesystem.
        :param tenant_id: The tenant ID representing the organisation.
        :param client_id: The client ID (a string representing a GUID).
        :param client_secret: The client secret string.
        """
        if None in [storage_account_url, filesystem_name, tenant_id, client_id, client_secret]:
            raise TypeError

        self.storage_account_url = storage_account_url
        self.filesystem_name = filesystem_name
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.config = config
        self.tracer_config = tracer_config
        self.prometheus_client = prometheus_client
        self.max_files = 2

    def transform(self):
        """
        TODO: add appropriate docstring
        """
        logger.info('Initializing TransformDeclarationProduction.transform')
        tracer = TracerClass(self.tracer_config)
        datasets = 'Datasets_prod'

        client_auth = ClientAuthorization(tenant_id=self.tenant_id,
                                          client_id=self.client_id,
                                          client_secret=self.client_secret)

        plant_declaration_source = Dataset(client_auth=client_auth.get_local_copy(),
                                           account_url=self.storage_account_url,
                                           filesystem_name=self.filesystem_name,
                                           guid=self.config[datasets]['plant_declaration_id'],
                                           prometheus_client=self.prometheus_client)

        plant_production_source = Dataset(client_auth=client_auth.get_local_copy(),
                                          account_url=self.storage_account_url,
                                          filesystem_name=self.filesystem_name,
                                          guid=self.config[datasets]['plant_production_id'],
                                          prometheus_client=self.prometheus_client)

        solar_production_source = Dataset(client_auth=client_auth.get_local_copy(),
                                          account_url=self.storage_account_url,
                                          filesystem_name=self.filesystem_name,
                                          guid=self.config[datasets]['solar_production_id'],
                                          prometheus_client=self.prometheus_client)

        wind_production_source = Dataset(client_auth=client_auth.get_local_copy(),
                                         account_url=self.storage_account_url,
                                         filesystem_name=self.filesystem_name,
                                         guid=self.config[datasets]['wind_production_id'],
                                         prometheus_client=self.prometheus_client)

        hydro_production_source = Dataset(client_auth=client_auth.get_local_copy(),
                                          account_url=self.storage_account_url,
                                          filesystem_name=self.filesystem_name,
                                          guid=self.config[datasets]['hydro_production_id'],
                                          prometheus_client=self.prometheus_client)

        dataset_destination = Dataset(client_auth=client_auth,
                                      account_url=self.storage_account_url,
                                      filesystem_name=self.filesystem_name,
                                      guid=self.config[datasets]['destination'],
                                      prometheus_client=self.prometheus_client)

        self.start_date = self.config['Settings']['start_date']

        date_range = pd.date_range(self.start_date, datetime.utcnow().replace(day=1),
                                   freq='MS', tz='UTC', closed='left', normalize=True)

        with beam.Pipeline(options=PipelineOptions(['--runner=DirectRunner'])) as pipeline:
            _ = (
                    pipeline  # noqa
                    | beam_core.Create(date_range.tolist())  # noqa
                    | beam_core.ParDo(PlantDeclaration(
                ,
            ))  # noqa
                    | beam_core.ParDo(HydroProduction(hydro_production_source))  # noqa
                    | beam_core.ParDo(PlantProduction(plant_production_source))  # noqa
                    | beam_core.ParDo(SolarProduction(solar_production_source))  # noqa
                    | beam_core.ParDo(WindProduction(wind_production_source))  # noqa
                    | beam_core.ParDo(CO2Calculation())  # noqa
                    # TODO: Implement rest of the pipeline
                    | beam_core.ParDo(_UploadEventsToStorage(dataset_destination))  # noqa
            )

            logger.info('declarations.transform: batch processed and saving state')

        tracer.close()
        logger.info('TransformDeclarationProduction.transform: Finished')
