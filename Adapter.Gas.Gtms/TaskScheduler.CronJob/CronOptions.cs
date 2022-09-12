using System;

namespace TaskScheduler.CronJob
{
#pragma warning disable 1591
    public class CronOptions<T> where T : Job
    {
        public string TimeZoneInfo { get; set; } = "Local";
        public string[] CronExpression { get; set; } = new[] { "* * 31 2 *" };
        public bool RunOnce { get; set; }
        public bool RunImmediately { get; set; }

        public TimeZoneInfo GetTimeZoneInfo() =>
            TimeZoneInfo.Equals("Local", StringComparison.InvariantCultureIgnoreCase) ?
            System.TimeZoneInfo.Local : System.TimeZoneInfo.Utc;
    }
#pragma warning restore 1591
}
