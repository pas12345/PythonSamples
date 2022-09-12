"""
Module to handle pipeline for timeseries
"""
import json
from datetime import timedelta, datetime
import io


import pandas as pd
import apache_beam as beam
import apache_beam.transforms.core as beam_core
from apache_beam.options.pipeline_options import PipelineOptions

from osiris.core.enums import TimeResolution
from osiris.pipelines.azure_data_storage import Dataset
from osiris.pipelines.file_io_connector import DatalakeFileSource, FileBatchController
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.core.configuration import ConfigurationWithCredentials
from osiris.core.io import PrometheusClient

configuration = ConfigurationWithCredentials(__file__)
config = configuration.get_config()
credentials_config = configuration.get_credentials_config()
logger = configuration.get_logger()

class _RetrievePlantdefinitions(beam_core.DoFn):
    def __init__(self,
                 dataset_decl: Dataset,
                 dataset_scada_def: Dataset):
        super().__init__()

        self.dataset_decl = dataset_decl
        self.dataset_scada_def = dataset_scada_def

    @staticmethod
    def __load_content(content):
        records = pd.read_parquet(io.BytesIO(content), engine='pyarrow')  # type: ignore
        # JSONResponse cannot handle NaN values
        records = records.fillna('null')

        # It would be better to use records.to_dict, but pandas uses narray type which JSONResponse can't handle.
        return json.loads(records.to_json(orient='records'))

    def process(self, element, *args, **kwargs):
        period, content_month, content_year = element

        content_decl = self.dataset_decl.read_file('data.parquet')
        content_decl = self.__load_content(content_decl)

        content_scada = self.dataset_scada.read_file('data.parquet')
        content_scada = self.__load_content(content_scada)

        return [(element, content_decl, content_scada)]

class _RetrieveSCADAData(beam_core.DoFn):
    def __init__(self,
                 delfin_1h : Dataset):
        super().__init__()

        self.delfin_1h = delfin_1h

    @staticmethod
    def __load_content(content):
        records = pd.read_parquet(io.BytesIO(content), engine='pyarrow')  # type: ignore
        # JSONResponse cannot handle NaN values
        records = records.fillna('null')

        # It would be better to use records.to_dict, but pandas uses narray type which JSONResponse can't handle.
        return json.loads(records.to_json(orient='records'))

    def process(self, element, *args, **kwargs):
        path = f'year={element.year}/month={element.month:02d}/day={element.day:02d}/hour={element.hour:02d}/data.parquet'

        content = self.delfin_1h.read_file(path)
        content = self.__load_content(content)

        return [(element, content)]

class TransformPlantproduction:
    """
    TODO: add appropriate docstring
    """

    # pylint: disable=too-many-arguments, too-many-instance-attributes, too-few-public-methods
    def __init__(self, storage_account_url: str, filesystem_name: str, tenant_id: str, client_id: str,
                 client_secret: str, source_dataset_guid: str, destination_dataset_guid: str,
                 time_resolution: TimeResolution, max_files: int,
                 prometheus_client: PrometheusClient):

        tenant_id = credentials_config['Authorization']['tenant_id']
        client_id = credentials_config['Authorization']['client_id']
        client_secret = credentials_config['Authorization']['client_secret']

        prometheus_client = PrometheusClient(environment=config['Prometheus']['environment'],
                                             name=config['Prometheus']['name'],
                                             hostname=config['Prometheus']['hostname'])

        client_auth = ClientAuthorization(tenant_id=tenant_id,
                                          client_id=client_id,
                                          client_secret=client_secret)

        account_url = config['Azure Storage']['account_url']
        filesystem_name = config['Azure Storage']['filesystem_name']

        self.plant_declaration = Dataset(client_auth=client_auth,
                                       account_url=account_url,
                                       filesystem_name=filesystem_name,
                                       guid=config['Datasets']['plant_declaration'],
                                       prometheus_client=prometheus_client)

        self.scada_plant = Dataset(client_auth=client_auth,
                                       account_url=account_url,
                                       filesystem_name=filesystem_name,
                                       guid=config['Datasets']['scada_plant'],
                                       prometheus_client=prometheus_client)

        self.delfin_1h = Dataset(client_auth=client_auth,
                                       account_url=account_url,
                                       filesystem_name=filesystem_name,
                                       guid=config['Datasets']['delfin_1h'],
                                       prometheus_client=prometheus_client)

        self.destination_dataset_guid = Dataset(client_auth=client_auth,
                                       account_url=account_url,
                                       filesystem_name=filesystem_name,
                                       guid=config['Datasets']['delfin_1h'],
                                       prometheus_client=prometheus_client)

        """
        :param time_resolution: The time resolution to store the data in the destination dataset with.
        :param max_files: Number of files to process in every pipeline run.
        :param prometheus_client: Prometheus Client to generate metrics
       """


    def transform(self, ingest_time: datetime = None):
        """
        TODO: add appropriate docstring
        """
        start_date = (datetime.utcnow() - timedelta(day = 1)) .replace(hour=0)
        date_range = pd.date_range(self.start_date, (start_date + timedelta(day = 1)),
                                   freq='MS', tz='UTC', closed='left', normalize=True)


        client_auth = ClientAuthorization(tenant_id=self.tenant_id,
                                          client_id=self.client_id,
                                          client_secret=self.client_secret)

        ds_plant_decl = Dataset(client_auth=client_auth.get_local_copy(),
                                 account_url=self.storage_account_url,
                                 filesystem_name=self.filesystem_name,
                                 guid=self.source_dataset_guid,
                                 prometheus_client=self.prometheus_client)

        dataset_destination = Dataset(client_auth=client_auth,
                                      account_url=self.storage_account_url,
                                      filesystem_name=self.filesystem_name,
                                      guid=self.destination_dataset_guid,
                                      prometheus_client=self.prometheus_client)

        while True:

            file_batch_controller = FileBatchController(dataset=dataset_source,
                                                        ingest_time=ingest_time,
                                                        max_files=self.max_files)

            datalake_connector = DatalakeFileSource(dataset=dataset_source,
                                                    file_paths=file_batch_controller.get_batch())

            if datalake_connector.estimate_size() == 0:
                break

            with beam.Pipeline(options=PipelineOptions(['--runner=DirectRunner'])) as pipeline:
                _ = (
                        pipeline  # noqa
                        | 'read from filesystem' >> beam.io.Read(datalake_connector)  # noqa

                        # TODO: Implement rest of the pipeline
                )

            file_batch_controller.save_state()

            if ingest_time:
                break
