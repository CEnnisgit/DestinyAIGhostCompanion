//! Ghost Companion backend — composition root (Phase 4B).
//!
//! Wires the domain `OAuthSessionSaga` to its concrete adapters
//! (`PostgresTokenStorageAdapter`, `BungieIdentityClient`) and serves the axum
//! router. This is the only place that knows about all layers at once.

use std::sync::Arc;

use anyhow::Context;
use sqlx::postgres::PgPoolOptions;

use api::{build_router, AppState, BungieIdentityClient, BungieOAuthConfig};
use db::PostgresTokenStorageAdapter;
use domain::auth::saga::OAuthSessionSaga;

const BIND_ADDR: &str = "0.0.0.0:8080";

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load .env (local dev) before reading any configuration.
    let _ = dotenvy::dotenv();
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info".into()),
        )
        .init();

    // --- Database ---
    let database_url =
        std::env::var("DATABASE_URL").context("DATABASE_URL must be set (see .env.example)")?;
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
        .context("connecting to Postgres")?;

    // Apply pending migrations on boot so the schema is always current.
    sqlx::migrate!("../../migrations")
        .run(&pool)
        .await
        .context("running database migrations")?;

    // --- Adapters + domain saga ---
    let oauth = BungieOAuthConfig::from_env()
        .context("BUNGIE_CLIENT_ID / BUNGIE_CLIENT_SECRET / BUNGIE_API_KEY must be set")?;
    let http = reqwest::Client::new();

    let token_storage = Arc::new(PostgresTokenStorageAdapter::new(pool));
    let identity_provider = Arc::new(BungieIdentityClient::new(
        http.clone(),
        oauth.api_key.clone(),
    ));
    let auth_saga = Arc::new(OAuthSessionSaga::new(token_storage, identity_provider));

    let state = AppState {
        auth_saga,
        oauth,
        http,
    };

    // --- Serve ---
    let app = build_router(state);
    let listener = tokio::net::TcpListener::bind(BIND_ADDR)
        .await
        .with_context(|| format!("binding {BIND_ADDR}"))?;
    tracing::info!("Ghost Companion API listening on http://{BIND_ADDR}");
    axum::serve(listener, app).await.context("axum serve")?;

    Ok(())
}
