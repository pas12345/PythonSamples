"""
Module to handle pipeline for timeseries
"""
import logging
import json
import math
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


class CO2Calculation(beam_core.DoFn, ABC):
    def __init__(self):
        super().__init__()

    def process(self, element, *args, **kwargs):
        process_date = element['process_date']
        hydro_prod = element['hydro']
#        plant_prod = element['plant']
        plant_prod_gsrn = element['plant_gsrn']  # "GSRN", "TimestampUTC", "PriceArea", "Qnt"
        wind_prod = element['wind']
        solar_prod = element['solar']
        declaration = element['declaration']

        # join declaration with plant production on GSRN
        co2_ratio = pd.merge(plant_prod_gsrn, declaration, how="inner", on=["GSRN"])
        co2_ratio["Version"] = ""

        # for testing oply - limit output
        co2_ratio = co2_ratio[(co2_ratio['HourUTC'] >= process_date) & (co2_ratio['HourUTC'] < process_date + pd.Timedelta(hours=1))]

        # set value for normal dist.
        co2_ratio["HeatPowerAllocation"] = "Grid";
        co2_ratio["FuelAllocationMethod"] = "Total";
        co2_ratio["Production_MWh"] = co2_ratio["kWh"] * co2_ratio["AndelEl"] / 1000
        co2_ratio = co2_ratio["PriceArea","HourUTC","Version","GSRN","HeatPowerAllocation","ProductionType",
                              "FuelAllocationMethod","Production_MWh","FuelConsumptionGJ","AndelEl",
                              "CO2","SO2","NOx","Nmvoc","CH4","CO","N2O","Particles","Flyash","Slag","Desulp","Waste"]

        co2_ratio.to_csv("c:\\temp\\ratio.csv", sep=";", decimal=",")


        # CO2 calculations
        kwh = co2_ratio["kWh"]
        co2_ratio["CO2"] = co2_ratio["kWh"] * co2_ratio["CO2KWh"] / 1000
        co2_ratio["CO2125"] = co2_ratio["CO2"] * co2_ratio["Faktor125"]
        co2_ratio["CO2200"] = co2_ratio["CO2"] * co2_ratio["Faktor200"]
        co2_ratio["Ellev"] = co2_ratio["kWh"] * co2_ratio["AndelElProd"] / 1000

        # SO2 calculations
        co2_ratio["SO2125"] = co2_ratio["kWh"] * co2_ratio["SO2KWh"] / 1000 * co2_ratio["Faktor125"]

        # NOxx
        co2_ratio["NOx125"] = co2_ratio["kWh"] * co2_ratio["NOxKWh"] / 1000 * co2_ratio["Faktor125"]

        # NMvox
        co2_ratio["Nmvoc125"] = co2_ratio["kWh"] * co2_ratio["NmvocKWh"] / 1000 * co2_ratio["Faktor125"]

        # CH4
        co2_ratio["CH4125"] = co2_ratio["kWh"] * co2_ratio["CH4KWh"] / 1000 * co2_ratio["Faktor125"]

        # CO
        co2_ratio["CO125"] = co2_ratio["kWh"] * co2_ratio["COKWh"] / 1000 * co2_ratio["Faktor125"]

        # N2O
        co2_ratio["N2O125"] = co2_ratio["kWh"] * co2_ratio["N2OKWh"] / 1000 * co2_ratio["Faktor125"]

        # Partikler
        co2_ratio["Particles125"] = co2_ratio["kWh"] * co2_ratio["PartiklerKWh"] / 1000 * co2_ratio["Faktor125"]

        # Flyveaske
        co2_ratio["Flyash"] = co2_ratio["kWh"] * co2_ratio["FlyveaskeKWh"] / 1000 * co2_ratio["Faktor125"]

        # Slagge
        co2_ratio["Slag125"] = co2_ratio["kWh"] * co2_ratio["SlaggeKWh"] / 1000 * co2_ratio["Faktor125"]

        # Afsvovl
        co2_ratio["Sulfid125"] = co2_ratio["kWh"] * co2_ratio["AfsvovlKWh"] / 1000 * co2_ratio["Faktor125"]

        # Affald
        co2_ratio["Waste125"] = co2_ratio["kWh"] * co2_ratio["AffaldKWh"] / 1000 * co2_ratio["Faktor125"]

        co2_ratio = co2_ratio[
            ["PriceArea", "TimestampUTC", "GSRN", "RapGrp", "Ellev", "AndelElProd", "CO2", "CO2125", "CO2200",
            "SO2125", "NOx125", "Nmvoc125", "CH4125", "CO125", "N2O125", "Particles125", "Flyash", "Slag125",
             "Sulfid125", "Waste125"]]
        co2_ratio.to_csv("c:\\temp\\co2_ratio.csv", sep=";", decimal=",")

        co2_distribution = \
            co2_ratio.groupby(["PriceArea", "TimestampUTC", "RapGrp"],
                              as_index=False, sort=False)[["Ellev", "CO2", "CO2125", "CO2200",
                              "SO2125", "NOx125", "Nmvoc125", "CH4125", "CO125", "N2O125", "Particles125",
                            "Flyash","Slag125","Sulfid125", "Waste125"]].apply(sum)

        co2_distribution.to_csv("c:\\temp\\test_fordeling.csv", sep=";", decimal=",")

        co2_sum = co2_ratio.groupby(["PriceArea", "TimestampUTC"],
                                    as_index=False, sort=False)[["Ellev", "CO2125"]].apply(sum)

        co2_sum.to_csv("c:\\temp\\test_sum.csv", sep=";", decimal=",")

        result = pd.merge(co2_distribution, solar_prod, how="left", on=["TimestampUTC", "PriceArea"])
        # result = pd.merge(co2_distribution, wind_prod, how="left", on=["TimestampUTC", "PriceArea"])
        # result = pd.merge(result, solar_prod, how="left", on=["TimestampUTC", "PriceArea"])
        result = pd.merge(result, hydro_prod, how="left", on=["TimestampUTC", "PriceArea"])
        result.to_csv("c:\\temp\\final.csv", sep=";", decimal=",")

        return
