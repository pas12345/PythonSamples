using System;
using System.Collections.Generic;
using System.Data;
using System.Data.Odbc;
using Adapter.Electricity.Delfin.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace Adapter.Electricity.Delfin.Data
{
    public class DbManager : IDbManager
    {
        private readonly IConfigurationRoot _config;
        private readonly ILogger<DbManager> _logger;

        public DbManager(IConfigurationRoot config, ILogger<DbManager> logger)
        {
            _config = config;
            _logger = logger;
        }

        public DataTable GetData(string viewName, string cmdText)
        {
            using (var con = new OdbcConnection(_config.GetConnectionString("DefaultConnection")))
            {
                using (var cmd = con.CreateCommand())
                {
                    cmd.CommandType = CommandType.Text;
                    cmd.CommandText = cmdText;
                    cmd.CommandTimeout = 240;

                    var dtData = new DataSet();
                    using (var dataAdapter = new OdbcDataAdapter())
                    {
                        dataAdapter.SelectCommand = cmd;
                        try
                        {
                            con.Open();
                            dataAdapter.Fill(dtData, $"dbo.{viewName}");
                        }
                        finally
                        {
                            con.Close();
                        }
                    }

                    if (dtData.Tables.Count == 0) return null;
                    return dtData.Tables[0];
                }
            }
        }
    }
}
