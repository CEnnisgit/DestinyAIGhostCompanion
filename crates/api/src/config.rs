/// Application-wide configuration, read once from environment variables at startup.
///
/// `encryption_key` is a raw passphrase — key derivation happens downstream in `crates/db`.
pub struct AppConfig {
    pub database_url: String,
    pub bungie_api_key: String,
    pub bungie_client_id: String,
    pub bungie_client_secret: String,
    pub jwt_secret: String,
    pub encryption_key: String,
    pub port: u16,
}

impl AppConfig {
    /// Build config from environment variables.
    ///
    /// Panics with a descriptive message when a required variable is missing.
    pub fn from_env() -> Self {
        Self {
            database_url: required_var("DATABASE_URL"),
            bungie_api_key: required_var("BUNGIE_API_KEY"),
            bungie_client_id: required_var("BUNGIE_CLIENT_ID"),
            bungie_client_secret: required_var("BUNGIE_CLIENT_SECRET"),
            jwt_secret: required_var("JWT_SECRET"),
            encryption_key: required_var("ENCRYPTION_KEY"),
            port: std::env::var("PORT")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(8080),
        }
    }
}

fn required_var(name: &str) -> String {
    std::env::var(name).unwrap_or_else(|_| panic!("missing required env var: {name}"))
}
