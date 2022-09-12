"""
The transformation.
"""
import json
from abc import ABC
from datetime import timedelta, datetime
import io

import pandas as pd
import apache_beam as beam
import apache_beam.transforms.core as beam_core
from apache_beam.options.pipeline_options import PipelineOptions
from dateutil.relativedelta import relativedelta

from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.core.configuration import ConfigurationWithCredentials
from osiris.core.io import PrometheusClient
from osiris.pipelines.azure_data_storage import Dataset

configuration = ConfigurationWithCredentials(__file__)
config = configuration.get_config()
credentials_config = configuration.get_credentials_config()
logger = configuration.get_logger()


class _RetrieveJaoData(beam_core.DoFn, ABC):
    def __init__(self,
                 dataset_monthly: Dataset,
                 dataset_yearly: Dataset):
        super().__init__()

        self.dataset_monthly = dataset_monthly
        self.dataset_yearly = dataset_yearly

    @staticmethod
    def __load_content(content):
        records = pd.read_parquet(io.BytesIO(content), engine='pyarrow')  # type: ignore
        # JSONResponse cannot handle NaN values
        records = records.fillna('null')

        # It would be better to use records.to_dict, but pandas uses narray type which JSONResponse can't handle.
        return json.loads(records.to_json(orient='records'))

    def process(self, element, *args, **kwargs):
        last_month = (element.replace(day=1) - timedelta(days=1)).replace(day=1)
        year = last_month.year
        month = last_month.month

        path = f'year={year}/month={month:02d}/data.parquet'
        content_month = self.dataset_monthly.read_file(path)
        content_month = self.__load_content(content_month)

        path = f'year={element.year - 1}/data.parquet'
        content_year = self.dataset_yearly.read_file(path)
        content_year = self.__load_content(content_year)

        return [(element, content_month, content_year)]


class _RetrieveNBData(beam_core.DoFn, ABC):
    def __init__(self, dataset):
        super().__init__()

        self.dataset = dataset

    def __get_exchange_rates(self, year):
        path = f'year={year}/data.parquet'
        content = self.dataset.read_file(path)

        content = pd.read_parquet(io.BytesIO(content), engine='pyarrow')  # type: ignore
        # JSONResponse cannot handle NaN values
        content = content.fillna('null')
        content['Date'] = pd.to_datetime(content['Date'], format='%Y-%m-%d')
        content = content.set_index('Date').sort_index()

        return content

    def process(self, element, *args, **kwargs):
        period, content_month, content_year = element

        year = period.year

        exchange_current = self.__get_exchange_rates(year)
        exchange_last = self.__get_exchange_rates(year - 1)

        # exchange_rate_0101 = 743.93
        exchange_rate_0101 = exchange_last.iloc[-1]['EUR']
        # exchange_rate_mean = 743.68
        exchange_rate_mean = round(exchange_current.loc[f'{period.year}-{period.month:02d}', 'EUR'].mean(), 2)

        return [(period, content_month, content_year, (exchange_rate_0101, exchange_rate_mean))]


class _MakeCalculations(beam_core.DoFn, ABC):
    def __init__(self, borders):
        super().__init__()

        self.borders = borders

    @staticmethod
    def __update_values(rep_df, horizon, idx, column_sold, column_price):
        for item in horizon:
            if item['corridor'] == idx:
                response = item['response'][0]
                if len(response['results']) == 0:
                    continue
                rep_df[column_sold] = response['results'][0]['offeredCapacity']
                rep_df[column_price] = response['results'][0]['auctionPrice']
                if len(response['maintenances']) > 0:
                    start = response['maintenances'][0]['periodStart']
                    stop = response['maintenances'][0]['periodStop']
                    rep_df.loc[start:stop, column_sold] = response['maintenances'][0]['reducedOfferedCap']
                return rep_df
        return rep_df

    # pylint: disable=too-many-locals
    def process(self, element, *args, **kwargs):
        period = element[0]
        monthly = element[1]
        yearly = element[2]
        exchange_rate_0101 = element[3][0]
        exchange_rate_mean = element[3][1]

        results = []

        for idx_export, idx_import in self.borders:
            index = pd.period_range(start=period, end=period + relativedelta(months=1), freq='H')
            rep_df = pd.DataFrame({}, index=index[:-1])

            rep_df = self.__update_values(rep_df, monthly, idx_export, 'MonthExpCapSold', 'MonthPriceExp')
            rep_df = self.__update_values(rep_df, monthly, idx_import, 'MonthImpCapSold', 'MonthPriceImp')
            rep_df = self.__update_values(rep_df, yearly, idx_export, 'YearExpCapSold', 'YearPriceExp')
            rep_df = self.__update_values(rep_df, yearly, idx_import, 'YearImpCapSold', 'YearPriceImp')

            rep_df[f'Export Capacity sold {idx_export}'] = - rep_df['MonthExpCapSold'] - rep_df['YearExpCapSold']
            rep_df[f'Import Capacity sold {idx_import}'] = rep_df['MonthImpCapSold'] + rep_df['YearImpCapSold']

            rep_df['Valuta0101'] = exchange_rate_0101
            rep_df['ValutaMiddel'] = exchange_rate_mean

            col_monthly_eur = 'Monthly auction congestion rent (EUR)'
            col_yearly_eur = 'Year auction congestion rent (EUR)'
            col_monthly_dkk = 'Monthly auction congestion rent (DKK)'
            col_yearly_dkk = 'Year auction congestion rent (DKK)'

            rep_df[col_monthly_eur] = rep_df['MonthExpCapSold'] * rep_df['MonthPriceExp'] + \
                rep_df['MonthImpCapSold'] * rep_df['MonthPriceImp']
            rep_df[col_yearly_eur] = rep_df['YearExpCapSold'] * rep_df['YearPriceExp'] + \
                rep_df['YearImpCapSold'] * rep_df['YearPriceImp']

            rep_df[col_monthly_dkk] = (rep_df[col_monthly_eur] * rep_df['ValutaMiddel'] / 100).round(2)
            rep_df[col_yearly_dkk] = (rep_df[col_yearly_eur] * rep_df['Valuta0101'] / 100).round(2)

            results.append((period, idx_export, rep_df))
        return results


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


# pylint: disable=too-few-public-methods
class TransformJao2Eds:
    """
    The transformation of JAO (and Nationalbanken) data to EDS.
    """
    def __init__(self):
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

        self.dataset_monthly = Dataset(client_auth=client_auth,
                                       account_url=account_url,
                                       filesystem_name=filesystem_name,
                                       guid=config['JAO']['monthly_guid'],
                                       prometheus_client=prometheus_client)

        self.dataset_yearly = Dataset(client_auth=client_auth,
                                      account_url=account_url,
                                      filesystem_name=filesystem_name,
                                      guid=config['JAO']['yearly_guid'],
                                      prometheus_client=prometheus_client)

        self.dataset_nb = Dataset(client_auth=client_auth,
                                  account_url=account_url,
                                  filesystem_name=filesystem_name,
                                  guid=config['Nationalbanken']['guid'],
                                  prometheus_client=prometheus_client)

        self.borders = config['JAO EDS']['borders'].splitlines()
        self.borders = [item.split('-') for item in self.borders if '-' in item]
        self.borders = [(f'{item[0]}-{item[1]}', f'{item[1]}-{item[0]}') for item in self.borders]

        self.start_date = config['JAO EDS']['start_date']

        self.dataset = Dataset(client_auth=client_auth,
                               account_url=account_url,
                               filesystem_name=filesystem_name,
                               guid=config['JAO EDS']['guid'],
                               prometheus_client=prometheus_client)

    def transform(self):
        """
        The actual beam pipeline for the transformation
        :return:
        """
        # We need all months from start date to now (excluding the current month, as it is not finalized).
        date_range = pd.date_range(self.start_date, datetime.utcnow().replace(day=1),
                                   freq='MS', tz='UTC', closed='left', normalize=True)

        with beam.Pipeline(options=PipelineOptions(['--runner=DirectRunner'])) as pipeline:
            _ = (pipeline
                 | beam_core.Create(date_range.tolist())  # noqa
                 | beam_core.ParDo(_RetrieveJaoData(self.dataset_monthly, self.dataset_yearly))  # noqa
                 | beam_core.ParDo(_RetrieveNBData(self.dataset_nb))  # noqa
                 | beam_core.ParDo(_MakeCalculations(self.borders))  # noqa
                 | beam_core.ParDo(_UploadEventsToStorage(self.dataset))  # noqa
                 )
