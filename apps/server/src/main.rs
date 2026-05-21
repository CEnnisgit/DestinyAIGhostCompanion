use std::sync::Arc;

use axum::{routing::{get, post}, Router};
use tower_http::cors::{CorsLayer, Any};


use api::app_state::AppState;
use api::config::AppConfig;
use api::bungie_identity_client::BungieIdentityClient;
use api::bungie_oauth_routes::{auth_login, auth_callback, auth_refresh, auth_me};
use api::openai_client::OpenAiClient;
use api::websocket_handler::websocket_handler;
use db::crypto;
use db::postgres_token_storage::PostgresTokenStorageAdapter;
use domain::auth::saga::OAuthSessionSaga;
use domain::voice_ai::personalities::GhostPersonality;
use domain::voice_ai::saga::VoiceCommandSaga;

#[tokio::main]
async fn main() {
    // 1. Load environment
    dotenvy::dotenv().ok();
    tracing_subscriber::fmt::init();

    // 2. Read configuration
    let config = AppConfig::from_env();
    tracing::info!("Configuration loaded, starting on port {}", config.port);

    // 3. Connect to Postgres
    let pool = sqlx::PgPool::connect(&config.database_url)
        .await
        .expect("Failed to connect to Postgres");
    tracing::info!("Connected to Postgres");

    // 4. Run pending migrations
    sqlx::migrate!("../../migrations")
        .run(&pool)
        .await
        .expect("Failed to run database migrations");
    tracing::info!("Migrations applied");

    // 5. Derive encryption key via HKDF
    let encryption_key = crypto::derive_key(
        config.encryption_key.as_bytes(),
        crypto::APP_SALT,
    );

    // 6. Construct adapters
    let token_storage = Arc::new(PostgresTokenStorageAdapter::new(
        pool.clone(),
        encryption_key,
    ));

    let http_client = reqwest::Client::new();
    let identity_client = Arc::new(BungieIdentityClient::new(
        http_client.clone(),
        config.bungie_api_key.clone(),
    ));

    let auth_saga = Arc::new(OAuthSessionSaga::new(
        token_storage.clone(),
        identity_client,
    ));

    // Construct Universal LLM Adapters
    let primary_llm = Arc::new(OpenAiClient::new(
        http_client.clone(),
        config.llm_base_url.clone(),
        config.llm_api_key.clone(),
        config.llm_model.clone(),
    ));

    let fallback_llm = config.fallback_llm_base_url.as_ref().map(|base_url| {
        Arc::new(OpenAiClient::new(
            http_client.clone(),
            base_url.clone(),
            config.fallback_llm_api_key.clone().unwrap_or_default(),
            config.fallback_llm_model.clone().unwrap_or_default(),
        )) as Arc<dyn domain::voice_ai::ports::GenerativeAiPort>
    });

    let voice_saga = Arc::new(VoiceCommandSaga::new(
        primary_llm,
        fallback_llm,
        GhostPersonality::Warlock, // Configurable later
    ));

    // 7. Build application state
    let state = AppState {
        auth_saga,
        voice_saga,
        token_storage,
        http_client,
        config: Arc::new(config),
    };

    // 8. Build router
    let addr = format!("0.0.0.0:{}", state.config.port);
    let app = Router::new()
        .route("/auth/login", get(auth_login))
        .route("/auth/callback", get(auth_callback))
        .route("/auth/refresh", post(auth_refresh))
        .route("/auth/me", get(auth_me))
        .route("/ws/voice", get(websocket_handler))
        .layer(CorsLayer::new().allow_origin(Any).allow_headers(Any).allow_methods(Any))
        .with_state(state);

    // 9. Serve
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("Failed to bind to address");
    tracing::info!("Ghost Companion server listening on {}", addr);
    axum::serve(listener, app).await.expect("Server error");
}
