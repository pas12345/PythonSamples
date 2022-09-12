"""
Module to handle pipeline for timeseries
"""
import logging
import json
from abc import ABC
from datetime import timedelta, datetime
import io

import apache_beam as beam
import apache_beam.transforms.core as beam_core
from apache_beam.options.pipeline_options import PipelineOptions

from osiris.core.enums import TimeResolution
from osiris.pipelines.azure_data_storage import Dataset
from osiris.core.instrumentation import TracerClass, TracerConfig, TracerDoFn
from osiris.pipelines.file_io_connector import DatalakeFileSource, FileBatchController
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.core.io import PrometheusClient


logger = logging.getLogger(__file__)

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

class _UploadEventsToStorage(beam_core.DoFn, ABC):
    def __init__(self, dataset):
        super().__init__()

        self.dataset = dataset

    def process(self, element, *args, **kwargs):
        period, connection, data = element

        path = f'year={period.year}/month={period.month:02d}/{connection}.parquet'

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

class TransformDeclarations:
    """
    TODO: add appropriate docstring
    """

    # pylint: disable=too-many-arguments, too-many-instance-attributes, too-few-public-methods
    def __init__(self, storage_account_url: str, filesystem_name: str, tenant_id: str, client_id: str,
                 client_secret: str, plant_production_guid: str, destination_dataset_guid: str,
                 max_files: int, tracer_config: TracerConfig, prometheus_client: PrometheusClient):
        """
        :param storage_account_url: The URL to Azure storage account.
        :param filesystem_name: The name of the filesystem.
        :param tenant_id: The tenant ID representing the organisation.
        :param client_id: The client ID (a string representing a GUID).
        :param client_secret: The client secret string.
        :param plant_production_guid: The GUID for the plant production dataset.
        :param destination_dataset_guid: The GUID for the destination dataset.
        :param max_files: Number of files to process in every pipeline run.
        :param tracer_config: Configuration of Jaeger Tracer
        :param prometheus_client: Prometheus Client to generate metrics
       """
        if None in [storage_account_url, filesystem_name, tenant_id, client_id, client_secret,
                    plant_production_guid, destination_dataset_guid, max_files]:
            raise TypeError

        self.storage_account_url = storage_account_url
        self.filesystem_name = filesystem_name
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.plant_production_guid = plant_production_guid
        self.destination_dataset_guid = destination_dataset_guid
        self.max_files = max_files
        self.tracer_config = tracer_config
        self.prometheus_client = prometheus_client

    def transform(self):
        """
        TODO: add appropriate docstring
        """
        logger.info('Initializing Declarations.transform')
        tracer = TracerClass(self.tracer_config)

        client_auth = ClientAuthorization(tenant_id=self.tenant_id,
                                          client_id=self.client_id,
                                          client_secret=self.client_secret)

        plant_production_source = Dataset(client_auth=client_auth.get_local_copy(),
                                 account_url=self.storage_account_url,
                                 filesystem_name=self.filesystem_name,
                                 guid=self.plant_production_guid,
                                 prometheus_client=self.prometheus_client)

        dataset_destination = Dataset(client_auth=client_auth,
                                      account_url=self.storage_account_url,
                                      filesystem_name=self.filesystem_name,
                                      guid=self.destination_dataset_guid,
                                      prometheus_client=self.prometheus_client)

        file_batch_controller = FileBatchController(dataset=plant_production_source,
                                                    max_files=self.max_files)

        while file_batch_controller.more_files_to_process():
            logger.info('declarations.transform: start batch')

            with tracer.start_span('Batch') as span:
                carrier_ctx = tracer.get_carrier(span)

                paths = file_batch_controller.get_batch()
                for path in paths:
                    span.set_tag('path', path)

                datalake_connector = DatalakeFileSource(dataset=plant_production_source,
                                                        file_paths=paths)

                with beam.Pipeline(options=PipelineOptions(['--runner=DirectRunner'])) as pipeline:
                    _ = (
                            pipeline  # noqa
                            | beam_core.ParDo(_RetrievePlantdefinitions(self.dataset_monthly, self.dataset_yearly))  # noqa
                            | 'read from filesystem' >> beam.io.Read(datalake_connector)  # noqa

                            # TODO: Implement rest of the pipeline
                            | beam_core.ParDo(_UploadEventsToStorage(self.dataset_destination))  # noqa
                    )

                logger.info('declarations.transform: batch processed and saving state')
                file_batch_controller.save_state()

        tracer.close()
        logger.info('TransformIngestTime2EventTime.transform: Finished')
