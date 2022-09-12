using Adapter.Common.Ingress.Interfaces;
using Adapter.Common.Ingress.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.IO;
using Xunit;

namespace TestAdapter
{
    public class UnitTests
    {

        private static ServiceProvider _serviceProvider;
        #region Setup
        public UnitTests()
        {
            _serviceProvider = RegisterServices();
        }

        private static IConfiguration SetupConfiguration()
        {
            System.Console.WriteLine(Directory.GetCurrentDirectory());
            return new ConfigurationBuilder()
                .SetBasePath(Directory.GetCurrentDirectory())
                //.AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
                .AddEnvironmentVariables()
                .Build();
        }
        private static ServiceProvider RegisterServices()
        {
            IConfiguration configuration = SetupConfiguration();
            var services = new ServiceCollection();

            services.AddSingleton(configuration);
            services.AddLogging();

            services.AddTransient<IFileService, FileService>();
            return services.BuildServiceProvider();
        }
        #endregion


        [Fact]
        public void SaveAndRetriveDateTime()
        {
            DateTime dt = new DateTime(2021, 1, 2, 10, 12, 0);

            string resolution = "1day";
            IFileService svc = _serviceProvider.GetService<IFileService>();
            svc.WriteEndValueToFile<DateTime>(dt, resolution);

            DateTime dt2 = svc.GetStartValueFromFile<DateTime>(resolution).Result;

            Assert.Equal(dt, dt2);
        }


        [Fact]
        public void SaveAndRetriveInt64()
        {
            Int64 val = 1234342166;

            string resolution = "1day";
            IFileService svc = _serviceProvider.GetService<IFileService>();
            svc.WriteEndValueToFile<Int64>(val, resolution);

            Int64 val2 = svc.GetStartValueFromFile<Int64>(resolution).Result;

            Assert.Equal(val, val2);
        }
    }
}
