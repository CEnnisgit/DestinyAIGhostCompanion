use std::sync::Arc;

use domain::auth::ports::TokenStoragePort;
use domain::auth::saga::OAuthSessionSaga;

use crate::config::AppConfig;

/// Shared state that every axum handler can extract via `State<AppState>`.
///
/// All interior fields are cheaply cloneable (`Arc` / `reqwest::Client`).
#[derive(Clone)]
pub struct AppState {
    pub auth_saga: Arc<OAuthSessionSaga>,
    pub token_storage: Arc<dyn TokenStoragePort>,
    pub http_client: reqwest::Client,
    pub config: Arc<AppConfig>,
}
