using System;
using System.Collections.Generic;
using System.Text;

namespace Energinet.DataPlatform.Shared.Logging
{
    //Stolen from https://github.com/dotnet/aspnetcore/blob/master/src/Logging.AzureAppServices/src/WebAppContext.cs
    /// <summary>
    /// Represents the default implementation of <see cref="IWebAppContext"/>.
    /// </summary>
    internal class WebAppContext
    {
        /// <summary>
        /// Gets the default instance of the WebApp context.
        /// </summary>
        public static WebAppContext Default { get; } = new WebAppContext();

        private WebAppContext() { }

        /// <inheritdoc />
        public string HomeFolder { get; } = Environment.GetEnvironmentVariable("HOME");

        /// <inheritdoc />
        public string SiteName { get; } = Environment.GetEnvironmentVariable("WEBSITE_SITE_NAME");

        /// <inheritdoc />
        public string SiteInstanceId { get; } = Environment.GetEnvironmentVariable("WEBSITE_INSTANCE_ID");

        /// <inheritdoc />
        public bool IsRunningInAzureWebApp => !string.IsNullOrEmpty(HomeFolder) &&
                                              !string.IsNullOrEmpty(SiteName);
    }
}
