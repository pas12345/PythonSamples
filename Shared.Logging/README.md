# Introduction 
This is the shared logging nuget package. This contains methods for easy setup of our standard logging with Serilog to Elasticsearch.
This also sets up some diagnostic listeners and activity tracing for tracking dependencies and how they interact, using the W3C trace standard.
Currently dependencies from http(azure storage included) and servicebus are supported.

# Getting Started
Currently two project types are supported, regular ASP.NET Core and Azure Functions. A sample project exist for each for an easy getting started, and here is outlined the basic steps.
One basic configuration part is that an environment name is required to start up. This name is used to figure out which elasticsearch server to send logs.

# Settings
Currently some configuration settings available to be set using environment variables or appsettings.
Find them in the ´loggingsettings.cs´. Current options are minimun loglevel, and which sinks to enable.

# Azure Functions

1.	Add a startup file
2.	Call 
        "builder.Services.AddDataPlatformLogging(environmentName);" 
    in startup
3.	Maybe create a try-catch around the rest of the startup file, and log an error using the returned logger to catch other startup errors.
4.	Use the local.settings.json to configure logging settings like this: 
        "LoggingSettings:LogToConsole": true

# ASP.NET Core
1.	In program.cs, add 
        .UseDataPlatformLogging(environmentName)
    in the CreateHostBuilder method.    
2.	Maybe create a try-catch around the rest of the main method file, and log an error using the returned logger to catch other startup errors.
3.	Use the appsettings.json to configure logging settings like this:
        "LoggingSettings": {
         "LogToElk": false,
         "LogToFile": true,
         "LogToConsole": true
        }
4.  In startup.cs, add "app.UseSerilogRequestLogging();" in the beginning of the Configure method.