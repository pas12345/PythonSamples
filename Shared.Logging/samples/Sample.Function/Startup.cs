using Energinet.DataPlatform.Shared.Logging;
using Microsoft.Azure.Functions.Extensions.DependencyInjection;
using Sample.Function;
using System;

[assembly: FunctionsStartup(typeof(Startup))]

namespace Sample.Function
{
    public class Startup : FunctionsStartup
    {
        public override void Configure(IFunctionsHostBuilder builder)
        {
            var environmentName = Environment.GetEnvironmentVariable("DPEnvironment");
            var logger = builder.Services.AddDataPlatformLogging(environmentName);
            try
            {
                //Add services

                logger.Information("Startup completed");
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
                logger.Error(ex, "Error in startup");
            }
        }
    }
}
