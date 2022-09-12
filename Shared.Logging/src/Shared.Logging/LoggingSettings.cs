using Serilog.Events;

namespace Energinet.DataPlatform.Shared.Logging
{
    internal class LoggingSettings
    {
        public LoggingSettings()
        {
            MinimumLogLevel = LogEventLevel.Information;
            LogToFile = false;
            LogToConsole = false;
            LogToElk = true;
        }
        public bool LogToFile { get; set; }
        public bool LogToConsole { get; set; }
        public bool LogToElk { get; set; }
        public LogEventLevel MinimumLogLevel { get; set; }
    }
}