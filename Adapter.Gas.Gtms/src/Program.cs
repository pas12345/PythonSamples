using Adapter.Common.Ingress.Interfaces;
using Adapter.Common.Ingress.Services;
using Adapter.Common.Ingress.TaskScheduler;
using Adapter.Gas.Gtms.Data;
using Adapter.Gas.Gtms.Interfaces;
using Adapter.Gas.Gtms.Services;
using Adapter.Gas.GtmsJobs;
using Energinet.DataPlatform.Shared.Logging;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using System;
using System.IO;
using System.Threading.Tasks;

namespace Adapter.Gas.Gtms
{
    public class Program
    {
        public static IConfigurationRoot Config;
        private static string dpEnvironmentVariable = Environment.GetEnvironmentVariable("DPEnvironment");

        public static async Task Main(string[] args)
        {
            var exceptionLogger = DataPlatformLogging.CreateLogger(dpEnvironmentVariable);

            try
            {
                exceptionLogger.Information("Starting here it is up!");
                exceptionLogger.Information($"Enviroment: {dpEnvironmentVariable}");

            Config = new ConfigurationBuilder()
                .SetBasePath(AppContext.BaseDirectory)
                .AddJsonFile($"appsettings.{dpEnvironmentVariable}.json", optional: false)
                .AddEnvironmentVariables()
                .AddCommandLine(args)
                .Build();

                await CreateHostBuilder(args).Build().RunAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex);
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
                    s.AddSingleton(Config);
                    s.AddScoped<IDbManager, DbManager>();
                    s.AddScoped<IQueryService, QueryService>();
                    s.AddScoped<ISendFileService, SendFileService>();
                    s.AddScoped<IFileService, FileService>();

                    s.RegisterJob<JobGT_ALLOC_BI>(Config.GetSection("JobGT_ALLOC_BI"));
                    s.RegisterJob<JobGT_BALANCE_SYSTEM_BI>(Config.GetSection("JobGT_BALANCE_SYSTEM_BI"));
                    s.RegisterJob<JobGT_BIOCERTIFICATE_BI>(Config.GetSection("JobGT_BIOCERTIFICATE_BI"));
                    s.RegisterJob<JobGT_CONTRACT_CAPACITY_BI>(Config.GetSection("JobGT_CONTRACT_CAPACITY_BI"));
                    s.RegisterJob<JobGT_DATA_H_BI>(Config.GetSection("JobGT_DATA_H_BI"));
                    s.RegisterJob<JobGT_INVOICE_LINES_BI>(Config.GetSection("JobGT_INVOICE_LINES_BI"));
                    s.RegisterJob<JobGT_NOM_BI>(Config.GetSection("JobGT_NOM_BI"));
                    s.RegisterJob<JobGT_PLAYER_BI>(Config.GetSection("JobGT_PLAYER_BI"));
                    s.RegisterJob<JobGT_POINT_BI>(Config.GetSection("JobGT_POINT_BI"));
                    s.RegisterJob<JobGT_TIME_BI>(Config.GetSection("JobGT_TIME_BI"));
                    s.RegisterJob<JobGT_TRADE_BI>(Config.GetSection("JobGT_TRADE_BI"));
                }).UseWindowsService();
        }
    }
}
