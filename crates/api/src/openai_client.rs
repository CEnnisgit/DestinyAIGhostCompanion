//! Phase 4C: OpenAI-compatible adapter for the voice_ai domain's `GenerativeAiPort`.
//!
//! ADR-007: works against any OpenAI-compatible Chat Completions API (OpenAI,
//! Grok, a local Ollama, …) by making the base URL configurable. The model is
//! asked for a strict JSON object that deserializes into a `VoiceIntent`.

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use serde::Deserialize;
use serde_json::json;

use domain::voice_ai::intent::VoiceIntent;
use domain::voice_ai::ports::GenerativeAiPort;

const DEFAULT_BASE_URL: &str = "https://api.openai.com/v1";
const DEFAULT_MODEL: &str = "gpt-4o-mini";

/// Appended to the domain personality prompt so any OpenAI-compatible model
/// emits exactly the internally-tagged `VoiceIntent` shape. Kept in the adapter
/// so the domain personality prompts stay provider-agnostic.
const SCHEMA_HINT: &str = r#"
You MUST respond with a single JSON object and nothing else. The object MUST
have an "action" field that is exactly one of:
- {"action":"Equip","item_name":"<string>","character_class":<string|null>}
- {"action":"Transfer","item_name":"<string>","to_vault":<bool>}
- {"action":"PullPostmaster","character_class":<string|null>}
- {"action":"QueryInventory","slot":<string|null>,"character_class":<string|null>}
- {"action":"Lore","topic":"<string>"}
- {"action":"Unknown","reason_for_confusion":"<string>"}
If you are unsure, use the Unknown action with a brief reason."#;

/// Concrete `GenerativeAiPort` for any OpenAI-compatible Chat Completions API.
pub struct OpenAiClient {
    http: reqwest::Client,
    base_url: String,
    api_key: String,
    model: String,
}

impl OpenAiClient {
    pub fn new(
        http: reqwest::Client,
        base_url: impl Into<String>,
        api_key: impl Into<String>,
        model: impl Into<String>,
    ) -> Self {
        Self {
            http,
            base_url: base_url.into(),
            api_key: api_key.into(),
            model: model.into(),
        }
    }

    /// Builds from `LLM_BASE_URL` / `LLM_MODEL` and `LLM_API_KEY` (falling back to
    /// `OPENAI_API_KEY`). Returns `None` if no API key is configured.
    pub fn from_env(http: reqwest::Client) -> Option<Self> {
        let api_key = std::env::var("LLM_API_KEY")
            .or_else(|_| std::env::var("OPENAI_API_KEY"))
            .ok()
            .filter(|k| !k.trim().is_empty())?;
        let base_url = std::env::var("LLM_BASE_URL").unwrap_or_else(|_| DEFAULT_BASE_URL.into());
        let model = std::env::var("LLM_MODEL").unwrap_or_else(|_| DEFAULT_MODEL.into());
        Some(Self::new(http, base_url, api_key, model))
    }
}

#[derive(Debug, Deserialize)]
struct ChatCompletionResponse {
    choices: Vec<ChatChoice>,
}

#[derive(Debug, Deserialize)]
struct ChatChoice {
    message: ChatMessage,
}

#[derive(Debug, Deserialize)]
struct ChatMessage {
    content: String,
}

#[async_trait]
impl GenerativeAiPort for OpenAiClient {
    async fn interpret_command(
        &self,
        system_prompt: &str,
        user_input: &str,
    ) -> Result<VoiceIntent, anyhow::Error> {
        let body = json!({
            "model": self.model,
            "messages": [
                { "role": "system", "content": format!("{system_prompt}\n{SCHEMA_HINT}") },
                { "role": "user", "content": user_input },
            ],
            "response_format": { "type": "json_object" },
        });

        let url = format!("{}/chat/completions", self.base_url.trim_end_matches('/'));
        let completion: ChatCompletionResponse = self
            .http
            .post(&url)
            .bearer_auth(&self.api_key)
            .json(&body)
            .send()
            .await
            .context("calling chat/completions")?
            .error_for_status()
            .context("chat/completions returned an error status")?
            .json()
            .await
            .context("decoding chat/completions response")?;

        let content = completion
            .choices
            .into_iter()
            .next()
            .map(|c| c.message.content)
            .ok_or_else(|| anyhow!("LLM returned no choices"))?;

        serde_json::from_str::<VoiceIntent>(content.trim())
            .with_context(|| format!("LLM output was not a valid VoiceIntent: {content}"))
    }

    async fn converse(
        &self,
        system_prompt: &str,
        user_message: &str,
    ) -> Result<String, anyhow::Error> {
        // Free-form: no response_format constraint — we want flowing prose back.
        let body = json!({
            "model": self.model,
            "messages": [
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": user_message },
            ],
        });

        let url = format!("{}/chat/completions", self.base_url.trim_end_matches('/'));
        let completion: ChatCompletionResponse = self
            .http
            .post(&url)
            .bearer_auth(&self.api_key)
            .json(&body)
            .send()
            .await
            .context("calling chat/completions")?
            .error_for_status()
            .context("chat/completions returned an error status")?
            .json()
            .await
            .context("decoding chat/completions response")?;

        completion
            .choices
            .into_iter()
            .next()
            .map(|c| c.message.content.trim().to_string())
            .filter(|s| !s.is_empty())
            .ok_or_else(|| anyhow!("LLM returned no conversational reply"))
    }
}
