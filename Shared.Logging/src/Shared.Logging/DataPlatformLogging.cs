using Energinet.DataPlatform.Shared.Logging.Enrichers;
using Energinet.DataPlatform.Shared.Logging.Sinks;
using Microsoft.Extensions.Configuration;
using Serilog;
using Serilog.Core;
using Serilog.Events;
using Serilog.Formatting.Compact;
using Serilog.Formatting.Elasticsearch;
using Serilog.Sinks.Elasticsearch;
using System;
using System.Diagnostics;
using System.Reflection;

namespace Energinet.DataPlatform.Shared.Logging
{
    /// <summary>
    /// Static methods for creating DataPlatform loggers
    /// </summary>
    public static class DataPlatformLogging
    {
        /// <summary>
        /// Creates a DataPlatform logger in the specified environment, with default configuration.
        /// </summary>
        /// <param name="environmentName">The hosting environment</param>
        /// <returns>The created logger</returns>
        public static Logger CreateLogger(string environmentName)
        {
            var callingAssembly = Assembly.GetCallingAssembly();
            var conf = CreateLoggerConfiguration(environmentName, null, callingAssembly);
            return conf.CreateLogger();
        }

        /// <summary>
        /// Creates a DataPlatform logger in the specified environment, with overriding configuration values from the provided config.
        /// </summary>
        /// <param name="environmentName">The hosting environment</param>
        /// <param name="config">Appwide config with overriding configuration values</param>
        /// <returns>The created logger</returns>
        public static Logger CreateLogger(string environmentName, IConfiguration config)
        {
            var callingAssembly = Assembly.GetCallingAssembly();
            var conf = CreateLoggerConfiguration(environmentName, config, callingAssembly);
            return conf.CreateLogger();
        }

        internal static Logger CreateLogger(string environmentName, IConfiguration config, Assembly callingAssembly)
        {
            var conf = CreateLoggerConfiguration(environmentName, config, callingAssembly);
            return conf.CreateLogger();
        }
        

        internal static LoggerConfiguration CreateLoggerConfiguration(string environmentName, IConfiguration config, Assembly callingAssembly, LoggerConfiguration inputConfiguration = null)
        {
            Activity.DefaultIdFormat = ActivityIdFormat.W3C;
            Activity.ForceDefaultIdFormat = true;

            var configuration = inputConfiguration ?? new LoggerConfiguration();
            var appName = callingAssembly.GetName().Name;
            var appVersion = callingAssembly.GetName().Version;
            var settings = config?.GetSection("LoggingSettings")?.Get<LoggingSettings>() ?? new LoggingSettings();

            configuration = configuration
                .MinimumLevel.Is(settings.MinimumLogLevel)
                .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Warning)
                .Enrich.WithProperty("ApplicationContext", appName)
                .Enrich.WithProperty("ApplicationVersion", appVersion)
                .Enrich.FromLogContext()                        
                .Enrich.WithProperty("Environment", environmentName)
                .Enrich.With(new CorrelationEnricher());

            if (settings.LogToElk)
            {
                string uriString = $"http://dptelemetry-{environmentName}.dp.priv:9200/"; //Azure private dns url
                if(!WebAppContext.Default.IsRunningInAzureWebApp)
                    uriString = $"http://dptelemetry-{environmentName}.westeurope.cloudapp.azure.com:9200/"; //public dns
                
                configuration = configuration.WriteTo.Elasticsearch(
                    new ElasticsearchSinkOptions(new Uri(uriString))
                    {
                        CustomFormatter = new ExceptionAsObjectJsonFormatter(renderMessage: true),
                        AutoRegisterTemplate = true,
                        AutoRegisterTemplateVersion = AutoRegisterTemplateVersion.ESv7,

                        EmitEventFailure = EmitEventFailureHandling.WriteToSelfLog | EmitEventFailureHandling.WriteToFailureSink,
                        FailureSink = new AzureAppSink(),
                    });
            }

            if (settings.LogToFile)
                configuration = configuration.WriteTo.File(new RenderedCompactJsonFormatter(), $"{AppContext.BaseDirectory}/logs/logfile.txt", settings.MinimumLogLevel, rollingInterval: RollingInterval.Day );

            if (settings.LogToConsole)
                configuration = configuration.WriteTo.Console();

            return configuration;
        }
    }
}