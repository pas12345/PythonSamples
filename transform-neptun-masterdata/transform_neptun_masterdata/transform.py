"""
Module to handle pipeline for timeseries
"""
import logging
from abc import ABC
from datetime import date
from io import BytesIO
from typing import List

import pandas as pd
import apache_beam as beam
import apache_beam.transforms.core as beam_core
from apache_beam.options.pipeline_options import PipelineOptions

from osiris.core.enums import TimeResolution
from osiris.pipelines.azure_data_storage import Dataset
from osiris.core.instrumentation import TracerClass, TracerConfig, TracerDoFn
from osiris.pipelines.file_io_connector import DatalakeFileSource, FileBatchController
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.core.io import PrometheusClient
from osiris.pipelines.transformations import UploadEventsToDestination

logger = logging.getLogger(__file__)


class ConvertToDataFrame(beam_core.DoFn, ABC):
    """
    Takes a list of events and converts them to a list of tuples (datetime, event)
    """

    def process(self, element, *args, **kwargs) -> List:
        """
        Overwrites beam.DoFn process.
        """
        dataframe = pd.read_parquet(BytesIO(element), engine='pyarrow')
        # It would be better to use records.to_dict, but pandas uses narray type which JSONResponse can't handle.
        return [dataframe]


class RenameColumn(beam_core.DoFn, ABC):
    """
    Renames columns in the element (DataFrame)
    """

    def __init__(self, columnnames):
        super().__init__()
        self.columnnames = columnnames

    def process(self, element, *args, **kwargs) -> List:
        """
        Overwrites beam.DoFn process.
        """
        for key in self.columnnames:
            element.rename(columns={key: self.columnnames[key]}, inplace=True)

        return [(date.today(), element)]


class TransformNeptunmasterdata:
    """
    Renaming columns names
    """

    # pylint: disable=too-many-arguments, too-many-instance-attributes, too-few-public-methods
    def __init__(self, storage_account_url: str, filesystem_name: str, tenant_id: str, client_id: str,
                 client_secret: str, source_dataset_guid: str, destination_dataset_guid: str,
                 time_resolution: TimeResolution,
                 max_files: int,
                 tracer_config: TracerConfig,
                 prometheus_client: PrometheusClient):
        """
        :param storage_account_url: The URL to Azure storage account.
        :param filesystem_name: The name of the filesystem.
        :param tenant_id: The tenant ID representing the organisation.
        :param client_id: The client ID (a string representing a GUID).
        :param client_secret: The client secret string.
        :param source_dataset_guid: The GUID for the source dataset.
        :param destination_dataset_guid: The GUID for the destination dataset.
        :param time_resolution: The time resolution to store the data in the destination dataset with.
        :param max_files: Number of files to process in every pipeline run.
        :param tracer_config: Configuration of Jaeger Tracer
        :param prometheus_client: Prometheus Client to generate metrics
       """
        if None in [storage_account_url, filesystem_name, tenant_id, client_id, client_secret,
                    source_dataset_guid, destination_dataset_guid, time_resolution, max_files]:
            raise TypeError

        self.storage_account_url = storage_account_url
        self.filesystem_name = filesystem_name
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.source_dataset_guid = source_dataset_guid
        self.destination_dataset_guid = destination_dataset_guid
        self.time_resolution = time_resolution
        self.max_files = max_files
        self.tracer_config = tracer_config
        self.prometheus_client = prometheus_client

    def transform(self):
        """
        Renaming columns
        """
        logger.info('Initializing Neptunmasterdata.transform')
        tracer = TracerClass(self.tracer_config)

        client_auth = ClientAuthorization(tenant_id=self.tenant_id,
                                          client_id=self.client_id,
                                          client_secret=self.client_secret)

        dataset_source = Dataset(client_auth=client_auth.get_local_copy(),
                                 account_url=self.storage_account_url,
                                 filesystem_name=self.filesystem_name,
                                 guid=self.source_dataset_guid,
                                 prometheus_client=self.prometheus_client)

        dataset_destination = Dataset(client_auth=client_auth,
                                      account_url=self.storage_account_url,
                                      filesystem_name=self.filesystem_name,
                                      guid=self.destination_dataset_guid,
                                      prometheus_client=self.prometheus_client)

        file_batch_controller = FileBatchController(dataset=dataset_source,
                                                    max_files=self.max_files)

        while file_batch_controller.more_files_to_process():
            logger.info('neptun-masterdata.transform: start batch')

            with tracer.start_span('Batch') as span:
                carrier_ctx = tracer.get_carrier(span)

                paths = file_batch_controller.get_batch()
                for path in paths:
                    span.set_tag('path', path)

                datalake_connector = DatalakeFileSource(dataset=dataset_source,
                                                        file_paths=paths)

                with beam.Pipeline(options=PipelineOptions(['--runner=DirectRunner'])) as pipeline:
                    _ = (
                            pipeline  # noqa
                            | 'Read from filesystem' >> beam.io.Read(datalake_connector)
                            | 'Convert to dataframe' >> beam_core.ParDo(ConvertToDataFrame())
                            | 'Rename columns' >> beam_core.ParDo(RenameColumn({'b1T': 'Station',
                                                                        'b2T': 'ComponentType',
                                                                        'b3T': 'ProcessArea',
                                                                        'b4T': 'Component',
                                                                        'b5T': 'Signal',
                                                                        'tw123T': 'Description',
                                                                        'InfoPunkt': 'Tag',
                                                                        'kBereichT': 'Area',
                                                                        'twAKST': 'TagName',
                                                                        'twDimT': 'Unit'}))
                            | 'Write to Storage' >> beam_core.ParDo(UploadEventsToDestination(dataset_destination,
                                                                                              self.time_resolution))
                    )

                logger.info("neptun-masterdata.transform: batch processed and saving state")
                file_batch_controller.save_state()

        tracer.close()
        logger.info('TransformIngestTime2EventTime.transform: Finished')
