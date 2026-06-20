use std::sync::Arc;
use crate::voice_ai::intent::VoiceIntent;
use crate::voice_ai::personalities::GhostPersonality;
use crate::voice_ai::ports::GenerativeAiPort;

/// The orchestrator that takes user voice strings, applies exactly the right personality,
/// and executes the GenAI JSON interpretation logic. Implements Automatic Failover (ADR 008).
pub struct VoiceCommandSaga {
    primary_ai: Arc<dyn GenerativeAiPort>,
    fallback_ai: Option<Arc<dyn GenerativeAiPort>>,
    personality: GhostPersonality,
}

impl VoiceCommandSaga {
    pub fn new(
        primary_ai: Arc<dyn GenerativeAiPort>,
        fallback_ai: Option<Arc<dyn GenerativeAiPort>>,
        personality: GhostPersonality,
    ) -> Self {
        Self {
            primary_ai,
            fallback_ai,
            personality,
        }
    }

    /// Takes the raw transcribed text from the user's microphone.
    /// Safely attempts cloud translation, then falls back to local translation on failure.
    pub async fn process_voice_command(&self, raw_text: &str) -> Result<VoiceIntent, anyhow::Error> {
        self.process_voice_command_with_context(raw_text, None).await
    }

    /// Like `process_voice_command`, but injects an optional Guardian career
    /// dossier into the system prompt so the Ghost personalizes to the player.
    pub async fn process_voice_command_with_context(
        &self,
        raw_text: &str,
        guardian_context: Option<&str>,
    ) -> Result<VoiceIntent, anyhow::Error> {
        let base = self.personality.system_prompt();
        let system_prompt = match guardian_context {
            Some(ctx) if !ctx.trim().is_empty() => {
                format!("{base}\n\nGuardian context (use to personalize your tone): {ctx}")
            }
            _ => base.to_string(),
        };

        // 1. Attempt the primary LLM
        match self.primary_ai.interpret_command(&system_prompt, raw_text).await {
            Ok(intent) => Ok(intent),
            Err(primary_err) => {
                // 2. Automatic Failover Circuit (ADR 008)
                if let Some(ref fallback) = self.fallback_ai {
                    match fallback.interpret_command(&system_prompt, raw_text).await {
                        Ok(intent) => Ok(intent),
                        Err(fallback_err) => {
                            Err(anyhow::anyhow!("CRITICAL: Both primary ({}) and fallback ({}) AI ports failed.", primary_err, fallback_err))
                        }
                    }
                } else {
                    Err(anyhow::anyhow!("Primary AI failed ({}) and no fallback AI was configured.", primary_err))
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use async_trait::async_trait;

    /// A dummy port that always instantly fails
    struct FailingAiPort;
    #[async_trait]
    impl GenerativeAiPort for FailingAiPort {
        async fn interpret_command(&self, _: &str, _: &str) -> Result<VoiceIntent, anyhow::Error> {
            Err(anyhow::anyhow!("Cloud Provider 500 Outage"))
        }
    }

    /// A dummy port that always succeeds with a Lore query
    struct SucceedingAiPort;
    #[async_trait]
    impl GenerativeAiPort for SucceedingAiPort {
        async fn interpret_command(&self, _: &str, _: &str) -> Result<VoiceIntent, anyhow::Error> {
            Ok(VoiceIntent::Lore { topic: "The Traveler".to_string() })
        }
    }

    #[tokio::test]
    async fn test_automatic_failover_circuit() {
        let primary = Arc::new(FailingAiPort);
        let fallback = Arc::new(SucceedingAiPort);

        let saga = VoiceCommandSaga::new(
            primary,
            Some(fallback),
            GhostPersonality::Warlock,
        );

        // The primary crashes, but the saga should yield the fallback's "Lore" success silently!
        let result = saga.process_voice_command("tell me about the traveler").await.unwrap();
        
        match result {
            VoiceIntent::Lore { topic } => assert_eq!(topic, "The Traveler"),
            _ => panic!("Expected Lore intent"),
        }
    }
}
