# zep-tepi-app-of-apps

This helm chart is used to deploy the applications used by the dataplatform.

It's using the argoCD CRD application.

### Usage
To deploy this follow [This guide](https://dev.azure.com/energinet/DataPlatform/_wiki/wikis/DataPlatform/7535/Add-application-to-ArgoCD) and deploy this repository

### Production environment
The file called production-values.yaml, Is the configuration of our production environment - this means of you want to change some values for production you have to edit the productions-values.yaml file.

The production-values.yaml file works like a [override file](https://stackoverflow.com/a/61608793), which has higher pressence over the values.yaml file.

This means that the values.yaml files still works like the default values, and as the default test config.

## Adding a new transformation

If you want to add a new transformation you want to go to the values.yaml.
Path this snippet.
``` yaml
- transformationfor: Jao
# path: # Overrides the global values.
# targetRevision: # Overrides the global values.

# Values for the transform-ingress2event-time config
  dateformat: "%%Y-%%m-%%dT%%H:%%M:%%S.%%f"
  sourceguid: <source_guid>
  destinationguid: <destination_guid>
  datekeyname: <date_key_name>
```
And past it in the transformingress2eventtime.transformations list
remembering to change to values to fit your needs.

!OBS Do not put the source and destination guids on the values.yaml, but configure those values in ArgoCD 

### Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | The environment is't deployed to | test
| `global.targetRevision` | The branch of the repo | HEAD
| `global.path` | The path to the helm charts | chart
| `global.ingress` | Holds global config for ingress' | [here](https://github.com/Open-Dataplatform/zep-tepi-app-of-apps/blob/4987955c4ac2820e5d291196cadb85cf799ce202/values.yaml#L8-L12)
| `osirisingress` | The configuratoin for the osiris ingress | 
| `osirisingress.namespace` | The deployment namespace for osirisingress | osiris
| `osirisingress.repoURL` | The url to the osiris ingress repository | "https://github.com/Open-Dataplatform/osiris-ingress-api.git"
| `osirisingress.helm.values.image.tag` | The image tag used by the osiris ingress | latest
| `osirisegress` | The configuratoin for the osiris egress | 
| `osirisegress.namespace` | The deployment namespace for osiris egress | osiris
| `osirisegress.repoURL` | The url to the osiris egress repository | "https://github.com/Open-Dataplatform/osiris-egress-api.git"
| `osirisegress.helm.values.image.tag` | The image tag used by the osiris egress | latest
| `transformingress2eventtime` | Holds default configs and a list of transformingress2eventtime configs |
| `transformingress2eventtime.namespace` | The namespace where the transformations should run | argo
| `transformingress2eventtime.repoURL` | The url to the transform-ingress2event-time repo | https://github.com/Open-Dataplatform/transform-ingress2event-time.git
| `transformingress2eventtime.tag` | The image tag to run | latest
| `transformingress2eventtime.transformations` | A list of transformingress2eventtime which contains their own configurations. |
