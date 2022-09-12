using System.Text.Json.Serialization;

namespace onprem.authlib
{
    /// <summary>
    /// 
    /// </summary>
    public class TokenErrorResponse
    {
        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("error")]
        public string Error { get; set; }

        /// <summary>
        /// 
        /// </summary>
        [JsonPropertyName("error_description")]
        public string ErrorDescription { get; set; }
    }
}
