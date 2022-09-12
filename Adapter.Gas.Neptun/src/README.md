# Introduction 

Data is read based on the non-decreasing identity column ID

Client id and secret are retrived from the environment var. defined in appsettings

"datasetKey": "neptun-datasets",

# Remarks
System.Data.Odbc is downgraded to 4.7 from 5.0 to match the Xunit test.

# Setup
setup tenantId in appsettings
"tenantId": "f7619355-6c67-4100-9a78-1847f30742e2",

Test
dp-test-ingress-neptun-scadadata
f9801088-a806-40d5-9e6f-e08c53d1eab6
1D: 
Dataset Id: 5bdc0cda-dd28-406f-40de-08d91129db7b

1H:
Dataset Id: ae25466b-f9ea-4f0b-40e0-08d91129db7b

3M:
Dataset Id: 3ee1b3df-fbe5-4705-40e2-08d91129db7b

prod
dp-ingress-neptun-scadadata

3M
3f0d123a-377f-49c7-115b-08d925bcbaf2
5cb6c857-1c15-4cfd-1151-08d925bcbaf2

1H
5bcbaade-8c9f-41fe-115a-08d925bcbaf2
0d80b6fc-fcfb-4848-1153-08d925bcbaf2

1D
939ac086-65c1-492b-9be1-08d90a4e650d
5466d7cc-77cb-4cd1-1155-08d925bcbaf2