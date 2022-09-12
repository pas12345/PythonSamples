using System.Threading;
using System.Threading.Tasks;
// https://codeburst.io/schedule-cron-jobs-using-hostedservice-in-asp-net-core-e17c47ba06

namespace TaskScheduler.CronJob
{
#pragma warning disable 1591

    public abstract class Job
    {
        public virtual Task Startup(CancellationToken cancellationToken = default) => Task.CompletedTask;
        public virtual Task Shutdown(CancellationToken cancellationToken = default) => Task.CompletedTask;

        public abstract Task Execute(CancellationToken cancellationToken = default);

    }
#pragma warning restore 1591
}
