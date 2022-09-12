from datetime import datetime, timedelta

import pandas as pd
from osiris.apis.egress import Egress


def main():
    egress_url = "https://dp-test.westeurope.cloudapp.azure.com/osiris-egress"
    tenant_id = 'f7619355-6c67-4100-9a78-1847f30742e2'
    client_id = "1e17cb33-2718-45dd-8ee4-04fcaeb01ed9"
    client_secret = "Du--Jkhy~I8ncAmInXAUJzi_0.GTeNY.Ag"
    dataset_guid = "f559a14a-b4c1-4395-40e6-08d91129db7b"

    start = datetime(2021, 5, 6)
    end = start + timedelta(days=1)

    print(f"{start:%Y-%m-%d}T00")

    egress = Egress(egress_url=egress_url,
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                    dataset_guid=dataset_guid)
    try:
        content = egress.download_json_file(f"{start:%Y-%m-%d}T00", f"{end:%Y-%m-%d}T00")
    except Exception as error:
        print(error)

    df = pd.DataFrame(content)
    if df.empty:
        print('No data found')
        return

    df.to_json(f"e:\\temp\\neptun{start:%Y-%m-%d}.json", orient="records", date_format="iso")
    df_dup = df[df.duplicated(['Timestamp', 'Tag'])].sort_values(by=['Tag', 'Timestamp', 'Inserted'])
    print("Duplicate Rows based on 2 columns are:", df_dup[['Timestamp', 'Tag', 'ID', 'Value']].head(25), sep='\n')
    df_dup[['Timestamp', 'Tag', 'ID', 'Value']].to_json(f"e:\\temp\\neptun_sort.json",
                                                        orient="records",
                                                        date_format="iso")


if __name__ == '__main__':
    main()
