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
}
