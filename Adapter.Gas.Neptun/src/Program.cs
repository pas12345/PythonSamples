using Adapter.Common.Ingress.Interfaces;
using Adapter.Common.Ingress.Services;
using Adapter.Common.Ingress.TaskScheduler;
using Adapter.Gas.Neptun.Data;
using Adapter.Gas.Neptun.Interfaces;
using Adapter.Gas.Neptun.Jobs;
using Adapter.Gas.Neptun.Services;
using Energinet.DataPlatform.Shared.Logging;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using System;
using System.Threading.Tasks;

namespace Adapter.Gas.Neptun
{
    public class Program
    {
        public static IConfiguration Config;
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
                Console.WriteLine($"dpEnvironmentVariable: {dpEnvironmentVariable}");
                Console.WriteLine(ex.ToString());
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
                    s.AddScoped<IFileService, FileService>();
                    s.AddScoped<ISendFileService, SendFileService>();

                    s.RegisterJob<Job1day>(Config.GetSection("Job1day"));
                    s.RegisterJob<Job1hour>(Config.GetSection("Job1hour"));
                    s.RegisterJob<Job3min>(Config.GetSection("Job3min"));
                    s.RegisterJob<JobDefinition>(Config.GetSection("JobDefinition"));
                }
                ).UseWindowsService();
        }
    }
}
