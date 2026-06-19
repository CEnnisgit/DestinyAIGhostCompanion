//! `api` crate — inbound (axum) + outbound (reqwest) adapters for the Ghost
//! Companion domain. The runnable composition root lives in `apps/server`.

pub mod bungie_identity_client;
pub mod bungie_oauth_routes;
pub mod openai_client;
pub mod websocket_handler;

pub use bungie_identity_client::BungieIdentityClient;
pub use bungie_oauth_routes::{auth_router, AppState, BungieOAuthConfig};
pub use openai_client::OpenAiClient;

use axum::{routing::get, Router};

/// Builds the full router: health check, Bungie auth routes, and the voice WebSocket.
pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(|| async { "ok" }))
        .merge(auth_router(state.clone()))
        .merge(websocket_handler::voice_ws_router(state))
}
