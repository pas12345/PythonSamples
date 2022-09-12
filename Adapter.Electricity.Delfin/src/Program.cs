using Adapter.Common.Ingress.Interfaces;
using Adapter.Common.Ingress.Services;
using Adapter.Common.Ingress.TaskScheduler;
using Adapter.Electricity.Delfin.Data;
using Adapter.Electricity.Delfin.Interfaces;
using Adapter.Electricity.Delfin.Jobs;
using Adapter.Electricity.Delfin.Services;
using Energinet.DataPlatform.Shared.Logging;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using System;
using System.Threading.Tasks;

namespace Adapter.Electricity.Delfin
{
    public class Program
    {
        public static IConfigurationRoot Config;
        private static string dpEnvironmentVariable = Environment.GetEnvironmentVariable("DPEnvironment");

        public static async Task Main(string[] args)
        {
            // Init logging for start up.
            var exceptionLogger = DataPlatformLogging.CreateLogger(dpEnvironmentVariable);
            try
            {
                exceptionLogger.Information("Starting up!");
                exceptionLogger.Information($"Enviroment: {dpEnvironmentVariable}");

                Config = new ConfigurationBuilder()
                         .SetBasePath(AppContext.BaseDirectory)
                         .AddJsonFile($"appsettings.{dpEnvironmentVariable}.json", optional: false, reloadOnChange: true)
                         .AddEnvironmentVariables()
                         .AddCommandLine(args)
                         .Build();

                await CreateHostBuilder(args).Build().RunAsync();
            }
            catch (Exception ex)
            {
                exceptionLogger.Fatal(ex, "Application start-up failed");
            }
            finally
            {
                exceptionLogger.Information("Shutting down!");
                exceptionLogger.Dispose();
            }
        }

        public static IHostBuilder CreateHostBuilder(string[] args)
        {

            return Host.CreateDefaultBuilder(args)
                .UseDataPlatformLogging(dpEnvironmentVariable)
                .ConfigureServices(s =>
                {
                    s.AddScoped<IDbManager, DbManager>();
                    s.AddScoped<IQueryService, QueryService>();
                    s.AddScoped<ISendFileService, SendFileService>();
                    s.AddScoped<IFileService, FileService>();

                    s.RegisterJob<JobE_ANA_1M>(Config.GetSection("JobE_ANA_1M"));
                    s.RegisterJob<JobE_ANA_1H>(Config.GetSection("JobE_ANA_1H"));
                    s.RegisterJob<JobE_ANA_1D>(Config.GetSection("JobE_ANA_1D"));
                    s.AddSingleton(Config);
                }).UseWindowsService();
        }
    }
}
