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


class PlantDeclaration(beam_core.DoFn, ABC):

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
    def __extract_content(content):
        df = pd.DataFrame(content)

        df.rename(columns={'RapGrp': 'ProductionType'
            , 'VrkGsrn': 'GSRN'
            , 'AndelElProd': 'AndelEl'
            , 'CO2KWh': 'CO2'
            , 'SO2KWh': 'SO2'
            , 'NmvocKWh': 'Nmvoc'
            , 'NOxKWh': 'NOx'
            , 'CH4KWh': 'CH4'
            , 'COKWh': 'CO'
            , 'N2OKWh': 'N2O'
            , 'PartiklerKWh': 'Particles'
            , 'FlyveaskeKWh': 'Flyash'
            , 'SlaggeKWh': 'Slag'
            , 'AfsvovlKWh': 'Desulp'
            , 'AffaldKWh': 'Waste'
            , 'GJialtPerMWh': 'FuelConsumptionGJ'}
                  , inplace=True)

        # GSRN number is in the following format: GSRNXXXX where X is the number we want.
        # The letters are removed in the following code
        df["GSRN"] = df["GSRN"].str[4:]

        df["GSRN"] = df["GSRN"].astype(str)
        df['CO2'] = pd.to_numeric(df['CO2'], errors='coerce')
        df['Faktor125'] = pd.to_numeric(df['Faktor125'], errors='coerce')
        df['Faktor200'] = pd.to_numeric(df['Faktor200'], errors='coerce')
        df['AndelEl'] = pd.to_numeric(df['AndelEl'], errors='coerce')
        df['ElBrMWhLev'] = pd.to_numeric(df['ElBrMWhLev'], errors='coerce')
        df['ElBrMWh'] = pd.to_numeric(df['ElBrMWh'], errors='coerce')
        df['FuelConsumptionGJ'] = pd.to_numeric(df['FuelConsumptionGJ'], errors='coerce')
        df["SO2"] = pd.to_numeric(df['SO2'], errors='coerce')
        df["NOx"] = pd.to_numeric(df['NOx'], errors='coerce')
        df["Nmvoc"] = pd.to_numeric(df['Nmvoc'], errors='coerce')
        df["CH4"] = pd.to_numeric(df['CH4'], errors='coerce')
        df["CO2oprKWh"] = pd.to_numeric(df['CO2oprKWh'], errors='coerce')
        df["CO"] = pd.to_numeric(df['CO'], errors='coerce')
        df["N2O"] = pd.to_numeric(df['N2O'], errors='coerce')
        df["Particles"] = pd.to_numeric(df['Particles'], errors='coerce')
        df["Flyash"] = pd.to_numeric(df['Flyash'], errors='coerce')
        df["Slag"] = pd.to_numeric(df['Slag'], errors='coerce')
        df["Desulp"] = pd.to_numeric(df['Desulp'], errors='coerce')
        df["Waste"] = pd.to_numeric(df['Waste'], errors='coerce')

        # Remove obsolete columns
        df.drop('Kilde', axis=1, inplace=True)
        df.drop('vrk_ID', axis=1, inplace=True)
        df.drop('Vrkkortnavn', axis=1, inplace=True)
        df.drop('Vaerkstype', axis=1, inplace=True)
        df.drop('SNAP', axis=1, inplace=True)
        df.drop('Bkode', axis=1, inplace=True)

        # Change the name of fueltype to english
        df["ProductionType"].replace(
            {
                "Tr�_mm": "Wood",
                "Affald": "Waste",
                "Halm": "Straw",
                "Olie": "Oil",
                "Naturgas": "NaturalGas",
                "Biogas": "BioGas",
                "Kul": "Coal",
            },
            inplace=True,
        )

        return df

    def process(self, element, *args, **kwargs):
        year_stop = datetime.utcnow().year - 5
        year = element.year
        # find latest decl.
        while year > year_stop:
            path = f'year={year}/data.parquet'
            try:
                content = self.dataset.read_file(path)
                content = self.__load_content(content)
                if content is not None:
                    df = self.__extract_content(content)
                    df.to_csv("c:\\temp\\plantdeclaration.csv", sep=";", decimal=",")

                    element = {'process_date': element, 'declaration': df}
                    return [element]
            except Exception as e:
                pass

            year = year - 1
        return None
