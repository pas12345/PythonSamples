# Introduction 
Delfin data adapter

#Deployment
No automation has been added, as this is a onprem running application and the build of a pipeline is dependent on third party inside energinet.

Ergo to deploy:
build release in VS.
copy files to the enviroment
stop the running service on that in enviroment
replace the files in the folder of the service on the enviroment (Don't delete app settings, logs and index files)
restart the service

