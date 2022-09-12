using Cronos;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace TaskScheduler.CronJob
{

    /// <summary>
    /// 
    /// </summary>
    /// <typeparam name="TJob"></typeparam>
    public class CronJob<TJob> : BackgroundService where TJob : Job
    {
        private readonly CronExpression[] _expressions;
        private readonly TimeZoneInfo _timeZoneInfo;
        private readonly bool _runOnce;
        private readonly bool _runImmediately;
        private readonly ILogger<CronJob<TJob>> _logger;
        private readonly TJob _job;

        /// <summary>
        /// 
        /// </summary>
        /// <param name="logger"></param>
        /// <param name="options"></param>
        /// <param name="job"></param>
        public CronJob(ILogger<CronJob<TJob>> logger, IOptions<CronOptions<TJob>> options, TJob job)
        {
            try
            {
                _logger = logger;
                _job = job;

                _expressions = options.Value.CronExpression.Select(CronExpression.Parse).ToArray();
                _timeZoneInfo = options.Value.GetTimeZoneInfo();
                _runOnce = options.Value.RunOnce;
                _runImmediately = options.Value.RunImmediately;
            }
            catch (Exception e)
            {
                Console.WriteLine("CronJob ctor failed");
                throw new ApplicationException($"Failed to create job {job} - {e}");
            }
        }

        private IEnumerable<DateTimeOffset?> GetNextOccurence()
        {
            if (_runImmediately) yield return DateTimeOffset.Now;

            DateTimeOffset? _getNextOccurrence(DateTimeOffset now) => _expressions.Min(e => e.GetNextOccurrence(now, _timeZoneInfo));

            DateTimeOffset? next = _getNextOccurrence(DateTimeOffset.Now);
            while (next.HasValue)
            {
                yield return next;
                next = _getNextOccurrence(next.Value);
            }
        }

        private async Task ScheduleJob(CancellationToken cancellationToken)
        {
            foreach (var next in GetNextOccurence())
            {
                if (!next.HasValue) break;

                TimeSpan delay = new[] { next.Value - DateTimeOffset.Now, TimeSpan.FromSeconds(0) }.Max();
                Int64 intervalInt = (Int64)((delay.TotalMilliseconds > Int32.MaxValue) ? Int32.MaxValue : delay.TotalMilliseconds);

                // If interval greater than Int32.MaxValue, set the boolean to skip the next run. The interval will be topped at Int32.MaxValue.
                // The TimerElapsed function will call this function again anyway, so no need to store any information on how much is left.
                // It'll just repeat until the overflow status is 'false'.
                bool _overflow = intervalInt >= Int32.MaxValue;
                if (_overflow) delay = TimeSpan.FromMilliseconds(Int32.MaxValue);

                try
                {
                    await Task.Delay(delay, cancellationToken);

                    await _job.Startup(cancellationToken);
                    if (!_overflow) await _job.Execute(cancellationToken);
                    await _job.Shutdown(cancellationToken);

                }
                catch (TaskCanceledException)
                {
                    _logger.LogWarning("Job {jobName} was cancelled", typeof(TJob).Name);
                    break;
                }
#pragma warning disable CA1031 // In case of an exception - the job should still continue
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Unhandled exception occured - {exceptionMessage}", ex.Message);
                }
#pragma warning restore CA1031 // Do not catch general exception types


                if (_runOnce) break;
            }
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="stoppingToken"></param>
        /// <returns></returns>
        protected override Task ExecuteAsync(CancellationToken stoppingToken) => ScheduleJob(stoppingToken);

    }
}
