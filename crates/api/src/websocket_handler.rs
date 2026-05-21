use axum::{
    extract::{ws::{Message, WebSocket, WebSocketUpgrade}, State},
    response::IntoResponse,
};
use serde::{Deserialize, Serialize};
use tracing::{error, info, debug};

use domain::voice_ai::intent::VoiceIntent;

use crate::app_state::AppState;
use crate::auth_middleware::AuthUserWs;

// ── Inbound / Outbound JSON ─────────────────────────────────────────────────

#[derive(Deserialize)]
struct VoiceMessageIn {
    text: String,
}

#[derive(Serialize)]
struct VoiceMessageOut {
    response: String,
    intent: VoiceIntent,
}

// ── Handler ─────────────────────────────────────────────────────────────────

/// WebSocket handler for real-time voice command processing.
/// Upgrades the HTTP connection and enters a read/write message loop.
pub async fn websocket_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
    auth: AuthUserWs, // Validates the `?token=...` query param
) -> impl IntoResponse {
    info!("WebSocket connection established for user {}", auth.membership_id.0);
    ws.on_upgrade(move |socket| handle_socket(socket, state, auth))
}

async fn handle_socket(mut socket: WebSocket, state: AppState, auth: AuthUserWs) {
    while let Some(msg) = socket.recv().await {
        let msg = match msg {
            Ok(msg) => msg,
            Err(e) => {
                error!("WebSocket receive error for user {}: {}", auth.membership_id.0, e);
                break;
            }
        };

        if let Message::Text(text_payload) = msg {
            debug!("Received WebSocket payload: {}", text_payload);

            // 1. Parse incoming JSON
            let incoming: Result<VoiceMessageIn, _> = serde_json::from_str(&text_payload);
            let user_text = match incoming {
                Ok(data) => data.text,
                Err(e) => {
                    error!("Failed to parse incoming WS message: {}", e);
                    continue;
                }
            };

            // 2. Route through Domain Saga (includes ADR 008 Automatic Failover)
            match state.voice_saga.process_voice_command(&user_text).await {
                Ok(intent) => {
                    // 3. (Future) Route the intent to the correct domain execution slice
                    // For Phase 4C, we just echo a generic success response based on the intent
                    // because Phase 4D (Inventory) and 4E (Lore) are not built yet.
                    let response_text = match &intent {
                        VoiceIntent::Equip { item_name, .. } => format!("I'll equip {} for you right away.", item_name),
                        VoiceIntent::Transfer { item_name, to_vault: true } => format!("Sending {} to the vault.", item_name),
                        VoiceIntent::Transfer { item_name, to_vault: false } => format!("Pulling {} from the vault.", item_name),
                        VoiceIntent::PullPostmaster { .. } => "Checking the postmaster now.".to_string(),
                        VoiceIntent::QueryInventory { slot, .. } => format!("Let me check your {} slot.", slot.as_deref().unwrap_or("inventory")),
                        VoiceIntent::Lore { topic } => format!("Let me consult the archives regarding {}.", topic),
                        VoiceIntent::Unknown { reason_for_confusion } => format!("I'm sorry, I didn't catch that: {}", reason_for_confusion),
                    };

                    let outbound = VoiceMessageOut {
                        response: response_text,
                        intent,
                    };

                    // 4. Send response back to frontend
                    if let Ok(json_out) = serde_json::to_string(&outbound) 
                        && let Err(e) = socket.send(Message::Text(json_out.into())).await 
                    {
                        error!("Failed to send WS response: {}", e);
                        break;
                    }
                }
                Err(e) => {
                    error!("Voice Command Saga failed for user {}: {}", auth.membership_id.0, e);
                    // Provide a graceful degradation response to the user
                    let outbound = VoiceMessageOut {
                        response: "I'm having trouble connecting to the Vanguard network right now.".to_string(),
                        intent: VoiceIntent::Unknown { reason_for_confusion: "AI Provider failure".to_string() },
                    };
                    if let Ok(json_out) = serde_json::to_string(&outbound) {
                        let _ = socket.send(Message::Text(json_out.into())).await;
                    }
                }
            }
        }
    }

    info!("WebSocket disconnected for user {}", auth.membership_id.0);
}
