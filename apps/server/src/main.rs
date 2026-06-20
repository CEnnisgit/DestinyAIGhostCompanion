//! Ghost Companion backend — composition root (Phase 4B).
//!
//! Wires the domain `OAuthSessionSaga` to its concrete adapters
//! (`PostgresTokenStorageAdapter`, `BungieIdentityClient`) and serves the axum
//! router. This is the only place that knows about all layers at once.

use std::sync::Arc;

use anyhow::Context;
use sqlx::postgres::PgPoolOptions;

use api::{
    build_router, AppState, BungieIdentityClient, BungieInventoryClient, BungieOAuthConfig,
    CharacterClient, OpenAiClient,
};
use db::{
    EmbeddingClient, GrimoireSearch, ManifestItemResolver, ManifestSync,
    PostgresTokenStorageAdapter,
};
use domain::auth::saga::OAuthSessionSaga;
use domain::inventory::saga::EquipItemSaga;
use domain::lore::saga::LoreSaga;
use domain::voice_ai::personalities::GhostPersonality;
use domain::voice_ai::saga::VoiceCommandSaga;

const DEFAULT_PORT: &str = "8080";

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

    let token_storage = Arc::new(PostgresTokenStorageAdapter::new(pool.clone()));
    let identity_provider = Arc::new(BungieIdentityClient::new(
        http.clone(),
        oauth.api_key.clone(),
    ));
    let auth_saga = Arc::new(OAuthSessionSaga::new(token_storage.clone(), identity_provider));

    // --- Inventory (Phase 4D) ---
    // The inventory client shares the token store so it can authenticate Bungie
    // mutations on the user's behalf.
    let inventory_client = Arc::new(BungieInventoryClient::new(
        http.clone(),
        oauth.api_key.clone(),
        token_storage.clone(),
    ));
    let manifest_resolver = Arc::new(ManifestItemResolver::new(pool.clone()));
    let equip_saga = Arc::new(EquipItemSaga::new(inventory_client, manifest_resolver));
    let character_client = Arc::new(CharacterClient::new(
        http.clone(),
        oauth.api_key.clone(),
        token_storage,
    ));

    // --- Lore RAG (Phase 4E) ---
    // Built only when an embeddings provider is configured.
    let lore_saga = match EmbeddingClient::from_env(http.clone()) {
        Some(embeddings) => {
            let grimoire = Arc::new(GrimoireSearch::new(pool.clone(), embeddings));
            tracing::info!("lore RAG enabled");
            Some(Arc::new(LoreSaga::new(grimoire)))
        }
        None => {
            tracing::warn!("lore RAG disabled — set EMBEDDING_API_KEY/OPENAI_API_KEY to enable");
            None
        }
    };

    // --- Voice AI (Phase 4C) ---
    // Built only when an LLM is configured; the server still boots without one
    // (the /ws/voice route then reports the feature as unavailable).
    let voice_saga = match OpenAiClient::from_env(http.clone()) {
        Some(client) => {
            let primary = Arc::new(client);
            // ADR-008 failover: a distinct fallback port can be wired here later.
            let saga =
                VoiceCommandSaga::new(primary, None, personality_from_env());
            tracing::info!("voice AI enabled");
            Some(Arc::new(saga))
        }
        None => {
            tracing::warn!("voice AI disabled — set LLM_API_KEY/OPENAI_API_KEY to enable /ws/voice");
            None
        }
    };
    let ws_dev_token = std::env::var("GHOST_WS_DEV_TOKEN")
        .ok()
        .filter(|s| !s.trim().is_empty());

    // --- Manifest sync (Phase 4E, opt-in) ---
    // Downloads/loads the Bungie manifest + embeds lore in the background. Gated
    // behind GHOST_MANIFEST_SYNC because it needs a real BUNGIE_API_KEY and pulls
    // a large file; failures are logged, never fatal to startup.
    if env_flag("GHOST_MANIFEST_SYNC") {
        let sync = ManifestSync::new(
            pool.clone(),
            http.clone(),
            oauth.api_key.clone(),
            EmbeddingClient::from_env(http.clone()),
        );
        tokio::spawn(async move {
            if let Err(err) = sync.sync_if_changed().await {
                tracing::warn!(error = %err, "manifest sync failed");
            }
        });
    }

    let state = AppState {
        auth_saga,
        oauth,
        http,
        voice_saga,
        equip_saga,
        lore_saga,
        character_client,
        ws_dev_token,
    };

    // --- Serve ---
    // Hosts (Render, Fly, …) inject the port via $PORT; default to 8080 locally.
    let port = std::env::var("PORT").unwrap_or_else(|_| DEFAULT_PORT.to_string());
    let addr = format!("0.0.0.0:{port}");
    let app = build_router(state);
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .with_context(|| format!("binding {addr}"))?;
    tracing::info!("Ghost Companion API listening on http://{addr}");
    axum::serve(listener, app).await.context("axum serve")?;

    Ok(())
}

/// True when an env var is set to a truthy value (`1`/`true`).
fn env_flag(key: &str) -> bool {
    std::env::var(key)
        .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
        .unwrap_or(false)
}

/// Chooses the Ghost personality from `GHOST_PERSONALITY` (default: Warlock).
fn personality_from_env() -> GhostPersonality {
    match std::env::var("GHOST_PERSONALITY")
        .unwrap_or_default()
        .to_ascii_lowercase()
        .as_str()
    {
        "titan" => GhostPersonality::Titan,
        "hunter" => GhostPersonality::Hunter,
        "failsafe" => GhostPersonality::Failsafe,
        _ => GhostPersonality::Warlock,
    }
}
