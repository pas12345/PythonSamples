using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Authentication;
using System.Text.Json;
using System.Threading.Tasks;


namespace onprem.authlib
{
    /// <summary>
    /// 
    /// </summary>
    public class OsirisApi
    {
        private readonly string _ingressUrl;
        private readonly Guid _tenantId;
        private readonly string _clientId;
        private readonly string _clientSecret;
        private readonly string _dataSetId;

        /// <summary>
        /// 
        /// </summary>
        public OsirisApi(string ingressUrl, Guid tenantId, string clientId, string clientSecret, string dataSetId)
        {
            _ingressUrl = ingressUrl;
            _tenantId = tenantId;
            _clientId = clientId;
            _clientSecret = clientSecret;
            _dataSetId = dataSetId;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="file"></param>
        public async Task<HttpResponseMessage> UploadFileAsync(string file)
        {
            var reqUrl = $"/osiris-ingress/{_dataSetId}";
            return await UploadAsync(reqUrl, file);
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="file"></param>
        /// <param name="eventTime">To stored data on event time - in the format yyyy-MM-ddTHH-tt</param>
        public async Task<HttpResponseMessage> UploadFileAsync(string file, string eventTime)
        {
            var reqUrl = $"/osiris-ingress/{_dataSetId}/event_time?event_time={eventTime}";
            return await UploadAsync(reqUrl, file);
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="file"></param>
        /// <param name="schemaValidate"></param>
        public async Task<HttpResponseMessage> UploadJsonFileAsync(string file, bool schemaValidate)
        {
            var reqUrl = $"/osiris-ingress/{_dataSetId}/json?schema_validate={schemaValidate}";
            return await UploadAsync(reqUrl, file);
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="file"></param>
        /// <param name="eventTime">To stored data on event time - in the format yyyy-MM-ddTHH-tt</param>
        /// <param name="schemaValidate"></param>
        /// <returns></returns>
        public async Task<HttpResponseMessage> UploadJsonFileAsync(string file, string eventTime, bool schemaValidate)
        {
            var reqUrl = $"/osiris-ingress/{_dataSetId}/event_time/json?event_time={eventTime}&schema_validate={schemaValidate}";
            return await UploadAsync(reqUrl, file);
        }

        private async Task<HttpResponseMessage> UploadAsync(string reqUrl, string file)
        {
            try
            {
                var token = await GetTokenAsync();
                Console.WriteLine(reqUrl);

                var handler = new HttpClientHandler
                {
                    ClientCertificateOptions = ClientCertificateOption.Automatic,
                    SslProtocols = SslProtocols.Tls12
                };

                using var client = new HttpClient(handler) { BaseAddress = new Uri(_ingressUrl) };
                using var form = new MultipartFormDataContent();
                using var fileContent = new ByteArrayContent(await File.ReadAllBytesAsync(file));
                fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("multipart/form-data");
                form.Add(fileContent, "file", Path.GetFileName(file));
                client.DefaultRequestHeaders.Add("Authorization", token.AccessToken);

                return await client.PostAsync(reqUrl, form);
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
                throw;
            }
        }


        /// <summary>
        /// 
        /// </summary>
        /// <param name="file"></param>
        /// <returns></returns>
        public async Task<HttpResponseMessage> UpladeStateFileAsync(string file)
        {
            var token = await GetTokenAsync();
            var reqUrl = "/osiris-ingress/" + _dataSetId + "/save_state";

            var handler = new HttpClientHandler
            {
                ClientCertificateOptions = ClientCertificateOption.Automatic,
                SslProtocols = SslProtocols.Tls12
            };

            using var client = new HttpClient(handler) { BaseAddress = new Uri(_ingressUrl) };
            using var form = new MultipartFormDataContent();
            using var fileContent = new ByteArrayContent(await File.ReadAllBytesAsync(file));
            fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("multipart/form-data");
            form.Add(fileContent, "file", Path.GetFileName(file));
            client.DefaultRequestHeaders.Add("Authorization", token.AccessToken);

            return await client.PostAsync(reqUrl, form);
        }

        /// <summary>
        /// 
        /// </summary>
        /// <returns></returns>
        public async Task<Stream> GetStateFileAsync()
        {
            var token = await GetTokenAsync();
            var reqUrl = "/osiris-ingress/" + _dataSetId + "/retrieve_state";

            var handler = new HttpClientHandler
            {
                ClientCertificateOptions = ClientCertificateOption.Automatic,
                SslProtocols = SslProtocols.Tls12
            };

            using var client = new HttpClient(handler) { BaseAddress = new Uri(_ingressUrl) };
            using var form = new MultipartFormDataContent();
            client.DefaultRequestHeaders.Add("Authorization", token.AccessToken);

            var res = await client.GetAsync(reqUrl);
            return await res.Content.ReadAsStreamAsync();
        }

        /// <summary>
        /// Retrieve token.
        /// </summary>
        /// <returns></returns>
        private async Task<TokenResponse> GetTokenAsync()
        {
            var authority = $"https://login.microsoftonline.com/" + _tenantId + "/oauth2/token";
            var content = new Dictionary<string, string>();
            content.Add("grant_type", "client_credentials");
            content.Add("client_id", _clientId);
            content.Add("client_secret", _clientSecret);

            content.Add("resource", "https://storage.azure.com/");

            HttpRequestMessage msg = new HttpRequestMessage(HttpMethod.Get, authority);
            msg.Content = new FormUrlEncodedContent(content);

            using var client = new HttpClient();
            var response = await client.SendAsync(msg);

            var json = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                return JsonSerializer.Deserialize<TokenResponse>(json);
            }
            else
            {
                var errorResponse = JsonSerializer.Deserialize<TokenErrorResponse>(json);
                switch (errorResponse.Error)
                {
                    case "authorization_pending":
                        // Not complete yet, wait and try again later
                        break;
                    default:
                        // Some other error, nothing we can do but throw
                        throw new Exception(
                            $"Authorization failed: {errorResponse.Error} - {errorResponse.ErrorDescription}");
                }
                return null;
            }
        }
    }
}
