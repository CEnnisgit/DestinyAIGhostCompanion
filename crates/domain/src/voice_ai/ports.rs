use async_trait::async_trait;
use super::intent::VoiceIntent;

/// Secondary Port (Driven): Represents a generic OpenAI-compatible text generation interface.
/// Due to ADR 007, this abstracts away whether we are using Grok, Ollama, or OpenAI natively.
#[async_trait]
pub trait GenerativeAiPort: Send + Sync {
    /// Submits the prompt to the provider and attempts to deserialize the output into a VoiceIntent
    async fn interpret_command(
        &self,
        system_prompt: &str,
        user_input: &str
    ) -> Result<VoiceIntent, anyhow::Error>;

    /// Free-form conversation: returns the model's natural-language reply verbatim
    /// (no JSON, no schema). Powers the Ghost's open chat about lore and the
    /// Guardian's own journey. The default errors so existing single-purpose
    /// adapters need not implement it.
    async fn converse(
        &self,
        _system_prompt: &str,
        _user_message: &str,
    ) -> Result<String, anyhow::Error> {
        Err(anyhow::anyhow!(
            "this AI adapter does not support free-form conversation"
        ))
    }
}
