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
logger = logging.getLogger(__file__)

class WindProduction(beam_core.DoFn, ABC):
    def __init__(self, dataset: Dataset):
        super().__init__()
        self.dataset = dataset

    @staticmethod
    def __load_content(content):
        records = pd.read_parquet(io.BytesIO(content), engine='pyarrow')  # type: ignore
        # JSONResponse cannot handle NaN values
        records = records.fillna('null')

        # It would be better to use records.to_dict, but pandas uses narray type which JSONResponse can't handle.
        return json.loads(records.to_json(orient='records'))

    @staticmethod
    def __transform_content(content):
        df = pd.DataFrame(content)
        df.rename(columns={'TimestampUTC': 'HourUTC', 'Qnt': 'Wind'}, inplace=True)
        df['HourUTC'] = pd.to_datetime(df['HourUTC'])

        df.loc[(df['Offshore'] == True), 'Cat'] = 'Offshore'
        df.loc[(df['Offshore'] == False), 'Cat'] = 'Onshore'
        df = df[["HourUTC", "PriceArea", "Cat", "Wind"]]

        df = df.groupby(["HourUTC", "PriceArea", "Cat"]).sum()
        return pd.pivot_table(df, values='Wind', index=['HourUTC', 'PriceArea'], columns='Cat').reset_index()

    def process(self, element, *args, **kwargs):
        process_date = element['process_date']
        path = f'year={process_date.year}/month={process_date.month:02d}/data.parquet'
        try:
            content = self.dataset.read_file(path)
            content = self.__load_content(content)
            if content is not None:
                element['wind'] = self.__transform_content(content)
                element['wind'].to_csv("c:\\temp\\wind.csv", sep=";", decimal=",")
                return [element]

        except Exception as e:
            pass
        return None
