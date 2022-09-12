using System.Text.Json.Serialization;

namespace onprem.authlib
{
    /// <summary>
    /// 
    /// </summary>
    public class TokenResponse
    {
        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("access_token")]
        public string AccessToken { get; set; }

        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("id_token")]
        public string IdToken { get; set; }

        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("refresh_token")]
        public string RefreshToken { get; set; }

        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("token_type")]
        public string TokenType { get; set; }

        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("expires_in")]
        public string ExpiresIn { get; set; }

        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("scope")]
        public string Scope { get; set; }
    }
}
