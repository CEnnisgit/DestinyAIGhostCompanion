//! `api` crate — inbound (axum) + outbound (reqwest) adapters for the Ghost
//! Companion domain. The runnable composition root lives in `apps/server`.

pub mod bungie_activity_client;
pub mod bungie_api_client;
pub mod bungie_career_client;
pub mod bungie_character_client;
pub mod bungie_identity_client;
pub mod bungie_inventory_client;
pub mod bungie_oauth_routes;
pub mod openai_client;
pub mod session_auth;
pub mod websocket_handler;

pub use bungie_activity_client::BungieActivityClient;
pub use bungie_api_client::{BungieApiClient, BungieToolExecutor};
pub use bungie_character_client::CharacterClient;
pub use bungie_career_client::BungieCareerClient;
pub use bungie_identity_client::BungieIdentityClient;
pub use bungie_inventory_client::BungieInventoryClient;
pub use bungie_oauth_routes::{auth_router, AppState, BungieOAuthConfig};
pub use openai_client::OpenAiClient;
pub use session_auth::HmacSessionAuthority;

use axum::{routing::get, Router};
use tower_http::cors::CorsLayer;

/// Builds the full router: health check, Bungie auth routes, and the voice WebSocket.
/// A permissive CORS layer lets the browser web client (a different origin) call the API.
pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(|| async { "ok" }))
        .merge(auth_router(state.clone()))
        .merge(websocket_handler::voice_ws_router(state))
        .layer(CorsLayer::permissive())
}
