import logging.config
from datetime import datetime, timedelta
import pandas as pd

from osiris.apis.ingress import Ingress

from SAPService import SAPService


def set_category(row):
    if row['CAT'] == '> 40 kW':
        return "GE40"
    elif row['CAT'] == '10-40 kW':
        return "GE10LT40"
    else:
        return 'LT10'


# "http://10.178.4.36:8002/eds_service/production.xsodata/SOLAR" \
# "(IP_FROM_TIME='2021.05.17 22:00:00',IP_TO_TIME='2021.05.18 22:00:00', AGGREGATION_LEVEL='QUARTER')
# /Execute?$format=json&$select=UTC_HOUR_TEXT_FULL,PROD_EFF_CAT_0_10_40,READING_VALUE,PRICE_AREA_CODE"
def main():
    today = datetime.today().date()
    start = datetime(today.year, today.month, today.day) - timedelta(days=8)

    service = SAPService()
    select = "UTC_HOUR_TEXT_FULL,PROD_EFF_CAT_0_10_40,READING_VALUE,CURRENT_MERGE_MUNICIPALITY_CODE"
    df = service.get_data(start, "production", "SOLAR", "QUARTER", select)

    if df.empty:
        return

    df['TimestampUTC'] = pd.to_datetime(df['UTC_HOUR_TEXT_FULL'], format='%Y.%m.%d %H:%M')
    df.drop('UTC_HOUR_TEXT_FULL', axis=1, inplace=True)
    df["READING_VALUE"] = df["READING_VALUE"].astype(float)

    df = df.rename(columns={"PROD_EFF_CAT_0_10_40": "CAT"})
    df = df.rename(columns={"CURRENT_MERGE_MUNICIPALITY_CODE": "MunicipalityNo"})
    df = df.rename(columns={"READING_VALUE": "Qnt"})
    df["CAT"] = df.apply(lambda row: set_category(row), axis=1)
    df = pd.pivot_table(df, values='Qnt', index=['TimestampUTC', 'MunicipalityNo'], columns='CAT').reset_index()

    filename = f"e:\\temp\\municipalitySolarProduction{start:%Y-%m-%d}.json"
    df.to_json(filename, orient="records", date_format="iso")

    ingress_url = "https://dp-test.westeurope.cloudapp.azure.com/osiris-ingress"
    tenant_id = 'f7619355-6c67-4100-9a78-1847f30742e2'
    client_id = '20818bbb-5eb0-47d9-8058-e66f20a2da0c'
    client_secret = 'KYFi.axlTG3uLCw7oOoWStG063D2mHOOy8'
    dataset_guid = '03984d88-c337-4eda-ae54-08d9221a4041'

    ingress = Ingress(ingress_url=ingress_url,
                      tenant_id=tenant_id,
                      client_id=client_id,
                      client_secret=client_secret,
                      dataset_guid=dataset_guid)

    try:
        with open(filename, "r") as file:
            ingress.upload_json_file(file, schema_validate=False)
    except Exception as error:
        print(error)


if __name__ == '__main__':
    main()
