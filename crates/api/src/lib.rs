//! `api` crate — inbound (axum) + outbound (reqwest) adapters for the Ghost
//! Companion domain. The runnable composition root lives in `apps/server`.

pub mod bungie_identity_client;
pub mod bungie_oauth_routes;

pub use bungie_identity_client::BungieIdentityClient;
pub use bungie_oauth_routes::{auth_router, AppState, BungieOAuthConfig};

use axum::{routing::get, Router};

/// Builds the full HTTP router: health check plus the Bungie auth routes.
pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(|| async { "ok" }))
        .merge(auth_router(state))
}
