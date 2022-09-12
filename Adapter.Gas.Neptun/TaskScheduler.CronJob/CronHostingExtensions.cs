using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using System;

namespace TaskScheduler.CronJob
{
#pragma warning disable 1591

    public static class CronHostingExtensions
    {
        public static void RegisterJob<TJob>(this IServiceCollection self, Action<CronOptions<TJob>> configuration) where TJob : Job
        {
            self.AddTransient<TJob>();
            self.Configure(configuration);
            self.AddHostedService<CronJob<TJob>>();
        }

        public static void RegisterJob<TJob>(this IServiceCollection self, IConfigurationSection configuration) where TJob : Job
        {
            self.AddTransient<TJob>();
            self.Configure<CronOptions<TJob>>(configuration);
            self.AddHostedService<CronJob<TJob>>();
        }

    }
#pragma warning restore 1591
}
