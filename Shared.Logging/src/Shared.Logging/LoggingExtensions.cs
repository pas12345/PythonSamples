using Energinet.DataPlatform.Shared.Logging.Diagnostics;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Serilog;
using Serilog.Core;
using System;
using System.Diagnostics;
using System.Reflection;

namespace Energinet.DataPlatform.Shared.Logging
{
    /// <summary>
    /// Extensions for adding logging to a ServiceCollection (e.g. Azure functions) or a HostBuilder (e.g. Asp.Net CORE)
    /// </summary>
    public static class LoggingExtensions
    {
        /// <summary>
        /// Add logging to the DI container. Builds a serviceprovider from the incoming servicecollection to retrieve overriding configuration values. Returns the added logger
        /// </summary>
        /// <param name="services">The servicecollection to add logging to </param>
        /// <param name="environmentName">The hosting environment</param>
        /// <returns>The created logger</returns>
        public static Logger AddDataPlatformLogging(this IServiceCollection services, string environmentName)
        {
            var callingAssembly = Assembly.GetCallingAssembly();
            var sp = services.BuildServiceProvider();
            var config = sp.GetService<IConfiguration>();

            return services.AddDataPlatformLogging(environmentName, config, callingAssembly);
        }

        /// <summary>
        /// Add logging to the DI container. Uses the provided config to retrive overriding configuration values. Returns the added logger
        /// </summary>
        /// <param name="services">The servicecollection to add logging to </param>
        /// <param name="environmentName">The hosting environment</param>
        /// <param name="config">Appwide config with overriding configuration values</param>
        /// <returns>The created logger</returns>
        public static Logger AddDataPlatformLogging(this IServiceCollection services, string environmentName, IConfiguration config)
        {
            var callingAssembly = Assembly.GetCallingAssembly();
            return services.AddDataPlatformLogging(environmentName, config, callingAssembly);
        }

        private static Logger AddDataPlatformLogging(this IServiceCollection services, string environmentName, IConfiguration config, Assembly callingAssembly)
        {            
            var logger = DataPlatformLogging.CreateLogger(environmentName, config, callingAssembly);
            services.AddLogging(x =>
            {
                x.AddSerilog(logger, true);                
            });
            services.AddSingleton<ILogger>(logger);
            
            var outerSubscription = DiagnosticListener.AllListeners.Subscribe(new MainDiagnosticListener(logger));
            services.Add(new ServiceDescriptor(typeof(SubscriptionHolder), new SubscriptionHolder(outerSubscription)));
            return logger;
        }

        /// <summary>
        /// Add logging to the hostbuilder in the specified environment.
        /// </summary>
        /// <param name="builder">The host to add logging to</param>
        /// <param name="environmentName">The hosting environment</param>
        /// <returns>The provided hostbuilder for chaining</returns>
        public static IHostBuilder UseDataPlatformLogging(this IHostBuilder builder, string environmentName)
        {
            Activity.DefaultIdFormat = ActivityIdFormat.W3C;
            Activity.ForceDefaultIdFormat = true;
            var callingAssembly = Assembly.GetCallingAssembly();
            return builder.UseSerilog((hostingContext, loggerconfiguration) =>
            {
                DataPlatformLogging.CreateLoggerConfiguration(environmentName, hostingContext.Configuration, callingAssembly, loggerconfiguration);

            }).ConfigureServices((ctx, services) =>
            {
                //Use static logger as we dont have access to serviceprovider... should be setup since UseSerilogCall is before.
                var outerSubscription = DiagnosticListener.AllListeners.Subscribe(new MainDiagnosticListener(Log.Logger));
                services.Add(new ServiceDescriptor(typeof(SubscriptionHolder), new SubscriptionHolder(outerSubscription)));
            });
        }
    }
}