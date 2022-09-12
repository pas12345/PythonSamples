import datetime

from osiris.core.azure_client_authorization import ClientAuthorization
import requests
import datetime as dt
import pandas as pd

user = {
    "appId": "51d752ca-3571-4742-8d92-b2137b9bd34c",
    "name": "51d752ca-3571-4742-8d92-b2137b9bd34c",  # acctest007
    "password": "IrsBk563qh1BzDbvzGP.aosJ8jDG2y12WG",
    "tenant": "f7619355-6c67-4100-9a78-1847f30742e2"
}
credentials = ClientAuthorization(user["tenant"], user["appId"], user["password"])

# base_url = "https://dp-test.westeurope.cloudapp.azure.com/osiris-egress/v1"
base_url = "https://dp-prod.westeurope.cloudapp.azure.com/osiris-egress/v1"
start_day = dt.datetime(2021, 9, 24)
end_day = start_day + datetime.timedelta(days=1)

# data_ids = ["02480cbc-5361-43ab-e1d8-08d86464f17e", "0e8845e2-317c-42fc-ae5e-08d9221a4041"]

# data_guid = "02480cbc-5361-43ab-e1d8-08d86464f17e"  # GT_ALLOC # data ser ok ud
# bestilt trans hos nasib - REV_DATE

# data_guid = "0f3897d5-0c57-4967-7de4-08d86b849d90"  # GT_BALANCE_SYSTEM_BI
# TRANS -REV_DATE

# data_guid = "b133dd7a-f1e8-48db-fc33-08d8b6fedea4"  # GT_BIOCERTIFICATE_BI - tal passer ikke - REV_DATE
# "data_guid = "7ac81cf9-2ed8-4ae0-348a-08d9616ec5b4" # test
# TRANS

# data_guid = "acfee9a5-fc82-4e4d-af46-08d86c4300e8"  # GT_CONTRACT_CAPACITY_BI- ok

data_guid = "726dd6be-c485-4cf9-eecf-08d9628f61e5"  # GT_DATA_H_BI -  - tal passer ikke - REV_DATE - fejl i view
# TRANS - jeg fjerner SEQ_NR

# data_guid = "2cb9c571-3a5a-4d5c-eed1-08d9628f61e5"  # GT_INVOICE_LINES_BI - tal passer ikke - ingen rev_date
# TRANS kirsten laver REV_DATE

# data_guid = "fecfb55e-4637-4ff6-af49-08d86c4300e8"  # GT_NOM_BI - spørg kirsten REV_DATE
# kører på REV_DATE - trans bestilt hos Nasib

# data_guid = "3ab1b6f7-d0ec-4c16-7de5-08d86b849d90"  # GT_TRADE_BI - tal passer
# Kører 03:30 og henter det hele - Rune tester i TEST

# data_guid = "adc8d96f-8e3d-4e3d-af48-08d86c4300e8"  # GT_PLAYER_BI OK
# data_guid = "b1c9449c-a452-4308-af47-08d86c4300e8"  # GT_POINT_BI - OK
# data_guid = "14e4bf94-afab-44b3-af45-08d86c4300e8"  # GT_TIME_BI - OK

# for data_guid in data_ids:

call_url = f"{base_url}/{data_guid}/json?from_date={start_day.date()}&to_date={end_day.date()}"
# call_url = f"{base_url}{data_guid}/test_json"

res = requests.get(call_url, headers={"Authorization": credentials.get_access_token()})
print(call_url)
if res.ok:
    if res.status_code == 200:
        df = pd.DataFrame(res.json())
        print(len(df.index))
    else:
        print(res.reason)
#    print(df.describe())
else:
    print(res.content)