use std::sync::Arc;

use domain::auth::ports::TokenStoragePort;
use domain::auth::saga::OAuthSessionSaga;
use domain::voice_ai::saga::VoiceCommandSaga;
use domain::inventory::saga::EquipItemSaga;

use crate::config::AppConfig;

/// Shared state that every axum handler can extract via `State<AppState>`.
///
/// All interior fields are cheaply cloneable (`Arc` / `reqwest::Client`).
#[derive(Clone)]
pub struct AppState {
    pub auth_saga: Arc<OAuthSessionSaga>,
    pub voice_saga: Arc<VoiceCommandSaga>,
    pub equip_saga: Arc<EquipItemSaga>,
    pub token_storage: Arc<dyn TokenStoragePort>,
    pub http_client: reqwest::Client,
    pub config: Arc<AppConfig>,
}
