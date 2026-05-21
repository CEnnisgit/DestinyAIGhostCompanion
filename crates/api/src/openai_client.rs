use anyhow::{anyhow, Context};
use async_trait::async_trait;
use serde::{Deserialize, Serialize};

use domain::voice_ai::intent::VoiceIntent;
use domain::voice_ai::ports::GenerativeAiPort;

/// Universal LLM Adapter that strictly adheres to the standard OpenAI REST specification
/// (`POST /v1/chat/completions`). Per ADR 007, this single adapter supports any compliant
/// provider (OpenAI, Grok, local Ollama) by just swapping the `base_url`.
pub struct OpenAiClient {
    http_client: reqwest::Client,
    base_url: String,
    api_key: String,
    model: String,
}

impl OpenAiClient {
    pub fn new(http_client: reqwest::Client, base_url: String, api_key: String, model: String) -> Self {
        Self {
            http_client,
            base_url,
            api_key,
            model,
        }
    }
}

// ── OpenAI API Shapes ───────────────────────────────────────────────────────

#[derive(Serialize)]
struct ChatMessage {
    role: &'static str,
    content: String,
}

#[derive(Serialize)]
struct ResponseFormat {
    #[serde(rename = "type")]
    format_type: &'static str,
}

#[derive(Serialize)]
struct ChatCompletionRequest {
    model: String,
    messages: Vec<ChatMessage>,
    response_format: ResponseFormat,
}

#[derive(Deserialize)]
struct ChatCompletionChoice {
    message: ChatCompletionMessage,
}

#[derive(Deserialize)]
struct ChatCompletionMessage {
    content: Option<String>,
}

#[derive(Deserialize)]
struct ChatCompletionResponse {
    choices: Vec<ChatCompletionChoice>,
}

// ── Port Implementation ─────────────────────────────────────────────────────

#[async_trait]
impl GenerativeAiPort for OpenAiClient {
    async fn interpret_command(
        &self,
        system_prompt: &str,
        user_input: &str,
    ) -> Result<VoiceIntent, anyhow::Error> {
        let request = ChatCompletionRequest {
            model: self.model.clone(),
            messages: vec![
                ChatMessage {
                    role: "system",
                    content: system_prompt.to_string(),
                },
                ChatMessage {
                    role: "user",
                    content: user_input.to_string(),
                },
            ],
            // Force the LLM to output raw JSON (ensuring we can parse it into VoiceIntent)
            response_format: ResponseFormat {
                format_type: "json_object",
            },
        };

        // Note: URL formatting ensures we don't end up with double slashes if the
        // base_url ends in a slash (e.g. https://api.openai.com/v1 vs https://api.openai.com/v1/)
        let url = format!("{}/chat/completions", self.base_url.trim_end_matches('/'));

        let response = self
            .http_client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&request)
            .send()
            .await
            .context("failed to send request to LLM provider")?
            .error_for_status()
            .context("LLM provider returned an HTTP error")?;

        let response_body: ChatCompletionResponse = response
            .json()
            .await
            .context("failed to parse LLM provider response")?;

        let raw_content = response_body
            .choices
            .first()
            .and_then(|c| c.message.content.as_ref())
            .ok_or_else(|| anyhow!("LLM provider returned empty content"))?;

        let intent: VoiceIntent = serde_json::from_str(raw_content)
            .context("failed to parse LLM output into a valid VoiceIntent")?;

        Ok(intent)
    }
}
