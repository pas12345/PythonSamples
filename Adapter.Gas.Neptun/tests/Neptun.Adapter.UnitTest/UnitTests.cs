
using Adapter.Gas.Neptun.Config;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using System.IO;
using Xunit;

namespace Neptun.Adapter.UnitTest
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
                .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
                .AddEnvironmentVariables()
                .Build();
        }
        private static ServiceProvider RegisterServices()
        {
            IConfiguration configuration = SetupConfiguration();
            var services = new ServiceCollection();

            services.AddSingleton(configuration);
            services.AddLogging();

            return services.BuildServiceProvider();
        }
        #endregion

        [Fact]
        public void DatasetKeyTest()
        {
            IConfiguration configuration = _serviceProvider.GetService<IConfiguration>();

            var key = configuration.GetSection("datasetKey");
            Assert.NotNull(key);
        }

        [Fact]
        public void DayInfoTest()
        {
            JobInfo _jobInfo = new JobInfo(); 
            string resolution = "1day";
            IConfiguration configuration = _serviceProvider.GetService<IConfiguration>();

            configuration.GetSection("Job" + resolution).Bind(_jobInfo);
            Assert.NotNull(_jobInfo);
        }
    }
}
