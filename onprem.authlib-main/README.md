# Shared Osiris API/SDK library dotnet core C#
Used to authenticate via client credentials flow and upload files to the Osiris Ingrees API.

See the console application for documentation of usage.

###Hint:
Environment variables stored in appsettings.json or as machine variables in the following format:

´´´
"datasets": 
	[
		{
			"Name": "<dataset name - is used in linq expression to find the datasetvariables(string)>",
			"DataSetId": "<dataset_id(guid as string)>",
			"ClientId": "<client_id(guid as string>",
			"Secret": "<client_secret(string)"
		},
		{
			...
		}
	]

´´´


###Implemented in
 - DMI Weather data.



 ### TODO:
  - Consider implementing state storage in the Osiris API.