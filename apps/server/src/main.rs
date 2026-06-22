//! Ghost Companion backend — composition root (Phase 4B).
//!
//! Wires the domain `OAuthSessionSaga` to its concrete adapters
//! (`PostgresTokenStorageAdapter`, `BungieIdentityClient`) and serves the axum
//! router. This is the only place that knows about all layers at once.

use std::sync::Arc;

use anyhow::Context;
use sqlx::postgres::PgPoolOptions;

use api::{
    build_router, AppState, BungieActivityClient, BungieCareerClient, BungieIdentityClient,
    BungieInventoryClient, BungieOAuthConfig, CharacterClient, OpenAiClient,
};
use db::{
    EmbeddingClient, GrimoireSearch, ManifestItemResolver, ManifestSync,
    PostgresTokenStorageAdapter,
};
use domain::auth::saga::OAuthSessionSaga;
use domain::career::saga::GuardianProfileSaga;
use domain::inventory::saga::EquipItemSaga;
use domain::lore::saga::LoreSaga;
use domain::voice_ai::conversation::ConversationSaga;
use domain::voice_ai::personalities::GhostPersonality;
use domain::voice_ai::ports::GenerativeAiPort;
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

    // Seed curated foundational lore so the Ghost knows the essentials out of the box.
    match db::seed_lore(&pool).await {
        Ok(entries) => tracing::info!(entries, "seeded curated lore"),
        Err(err) => tracing::warn!(error = %err, "lore seed failed"),
    }

    // Import any external lore datasets (D1 Grimoire dumps, transcripts, etc.).
    let import_dir = std::env::var("GHOST_LORE_IMPORT_DIR").unwrap_or_else(|_| "lore_import".into());
    match db::import_lore_dir(&pool, &import_dir).await {
        Ok(0) => {}
        Ok(entries) => tracing::info!(entries, dir = %import_dir, "imported external lore"),
        Err(err) => tracing::warn!(error = %err, "external lore import failed"),
    }

    // Load the full Destiny 1 Grimoire from a local JSON dump, if present (no key needed).
    let d1_file = std::env::var("GHOST_D1_GRIMOIRE_FILE")
        .unwrap_or_else(|_| "lore_import/d1_grimoire.json".into());
    match db::load_d1_grimoire_file(&pool, &d1_file).await {
        Ok(0) => {}
        Ok(cards) => tracing::info!(cards, file = %d1_file, "loaded D1 Grimoire from file"),
        Err(err) => tracing::warn!(error = %err, "D1 Grimoire file load failed"),
    }

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
        token_storage.clone(),
    ));

    // --- Career personalization (Phase 5) ---
    let career_client = Arc::new(BungieCareerClient::new(
        http.clone(),
        oauth.api_key.clone(),
        token_storage.clone(),
    ));
    // Activity history: what the Guardian has done in-game (raid dates, fireteams),
    // across Destiny 2 and Destiny 1. Folded into the personalization dossier.
    let activity_client = Arc::new(BungieActivityClient::new(
        http.clone(),
        oauth.api_key.clone(),
        token_storage,
    ));
    let profile_saga = Arc::new(
        GuardianProfileSaga::new(career_client).with_activity(activity_client),
    );

    // --- Lore RAG (Phase 4E) ---
    // Always available: semantic search when embeddings are configured, keyword
    // search otherwise. Backed by the curated seed and/or the manifest lore.
    let embeddings = EmbeddingClient::from_env(http.clone());
    if embeddings.is_some() {
        tracing::info!("lore RAG: semantic (pgvector) search enabled");
    } else {
        tracing::info!("lore RAG: keyword search (set EMBEDDING_API_KEY for semantic search)");
    }
    let grimoire = Arc::new(GrimoireSearch::new(pool.clone(), embeddings));
    // Shared as a lore-grounding source for the conversational Ghost too.
    let lore_port: Arc<dyn domain::lore::ports::GrimoireDatabasePort> = grimoire.clone();
    let lore_saga = Some(Arc::new(LoreSaga::new(grimoire)));
    let lore_library = Arc::new(db::LoreLibrary::new(pool.clone()));

    // --- Voice AI (Phase 4C) ---
    // Built only when an LLM is configured; the server still boots without one
    // (the /ws/voice route then reports the feature as unavailable).
    let personality = personality_from_env();
    let (voice_saga, conversation_saga) = match OpenAiClient::from_env(http.clone()) {
        Some(client) => {
            let ai: Arc<dyn GenerativeAiPort> = Arc::new(client);
            // ADR-008 failover: a distinct fallback port can be wired here later.
            let voice = VoiceCommandSaga::new(ai.clone(), None, personality);
            // Free-form conversation, grounded in lore RAG + the Guardian dossier.
            let conversation =
                ConversationSaga::new(ai, Some(lore_port), personality);
            tracing::info!("voice AI + conversational Ghost enabled");
            (Some(Arc::new(voice)), Some(Arc::new(conversation)))
        }
        None => {
            tracing::warn!("voice AI disabled — set LLM_API_KEY/OPENAI_API_KEY to enable /ws/voice");
            (None, None)
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
        let grimoire_pool = pool.clone();
        let grimoire_http = http.clone();
        let grimoire_key = oauth.api_key.clone();
        tokio::spawn(async move {
            if let Err(err) = sync.sync_if_changed().await {
                tracing::warn!(error = %err, "manifest sync failed");
            }
            // Also ingest the full Destiny 1 Grimoire from Bungie's D1 API.
            match db::fetch_d1_grimoire(&grimoire_pool, &grimoire_http, &grimoire_key).await {
                Ok(0) => {}
                Ok(cards) => tracing::info!(cards, "ingested D1 Grimoire"),
                Err(err) => tracing::warn!(error = %err, "D1 Grimoire ingest failed"),
            }
        });
    }

    let state = AppState {
        auth_saga,
        oauth,
        http,
        voice_saga,
        conversation_saga,
        equip_saga,
        lore_saga,
        character_client,
        profile_saga,
        lore_library,
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
