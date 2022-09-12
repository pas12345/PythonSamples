Create new ingress:
1) create job class - Job + tablename
2) create data entity
2) create SQL statement in QueryService
4) register job in appsettings
5) register job as service in program.cs
6) create dataset definition in DataCatalog - 
7) add read/write permission for dp-test-ingress-delfin-scadadata

test:
dp-ingress-delfin-scadadata
E_ANA_1M: 
f34163db-72f8-425e-40e4-08d91129db7b

E_ANA_1H: 
db892d90-3e19-4752-40e3-08d91129db7b

E_ANA_1D: 
12a283bc-d551-49bd-ae5c-08d9221a4041

prod:
dp-ingress-delfin-scadadata
E_ANA_1M: 
55b1a30b-06e6-45d1-9be9-08d90a4e650d

E_ANA_1H: 
cb2c7313-58be-460f-9be8-08d90a4e650d

E_ANA_1D: 
bc870e52-f1fe-4df8-1156-08d925bcbaf2

Test:
{
  "appId": "3a5a8f77-06c0-41e8-a4a7-9eb160ec6d48",
  "displayName": "dp-test-ingress-delfin-scadadata",
  "name": "http://dp-test-ingress-delfin-scadadata",
  "password": "897024be-39f9-4888-bf5f-0bac004f431c",
  "tenant": "f7619355-6c67-4100-9a78-1847f30742e2"
}

