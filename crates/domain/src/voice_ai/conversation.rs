//! Free-form conversational Ghost.
//!
//! Where [`crate::voice_ai::saga::VoiceCommandSaga`] parses strict command
//! intents (equip, transfer, …), this saga lets the Guardian simply *talk* with
//! their Ghost. Replies are grounded in two ways so the Ghost stays both
//! accurate and personal:
//!   - **Lore RAG** — relevant lore is retrieved and injected so factual claims
//!     are anchored in canon, never hallucinated.
//!   - **Guardian dossier** — the player's career + activity context is injected
//!     so the Ghost speaks to *their* journey and knows to reference what they
//!     have actually done in-game.

use std::sync::Arc;

use crate::lore::ports::GrimoireDatabasePort;
use crate::voice_ai::personalities::GhostPersonality;
use crate::voice_ai::ports::GenerativeAiPort;

/// Orchestrates an open conversation between the Guardian and their Ghost.
pub struct ConversationSaga {
    ai: Arc<dyn GenerativeAiPort>,
    /// Optional lore retrieval for grounding; `None` falls back to ungrounded chat.
    lore: Option<Arc<dyn GrimoireDatabasePort>>,
    personality: GhostPersonality,
}

impl ConversationSaga {
    pub fn new(
        ai: Arc<dyn GenerativeAiPort>,
        lore: Option<Arc<dyn GrimoireDatabasePort>>,
        personality: GhostPersonality,
    ) -> Self {
        Self {
            ai,
            lore,
            personality,
        }
    }

    /// Holds a turn of conversation. `guardian_context` is the player's career +
    /// activity dossier (already rendered to text); pass `None` for a signed-out
    /// or anonymous chat. Returns the Ghost's natural-language reply, or a
    /// graceful message if generation fails.
    pub async fn converse(
        &self,
        message: &str,
        guardian_context: Option<&str>,
    ) -> Result<String, anyhow::Error> {
        let system_prompt = self.build_system_prompt(message, guardian_context).await;
        self.ai.converse(&system_prompt, message).await
    }

    /// Assembles the grounded system prompt: persona + Guardian dossier + retrieved lore.
    async fn build_system_prompt(&self, message: &str, guardian_context: Option<&str>) -> String {
        let mut system = String::from(self.personality.conversation_prompt());

        if let Some(ctx) = guardian_context.filter(|c| !c.trim().is_empty()) {
            system.push_str(
                "\n\n--- What you know about this Guardian (reference it naturally; never read it back as a list) ---\n",
            );
            system.push_str(ctx.trim());
        }

        // Best-effort lore grounding; failures (e.g. no DB) simply skip grounding.
        if let Some(lore) = &self.lore {
            if let Ok(context) = lore.fetch_semantic_lore_context(message).await {
                let context = context.trim();
                if !context.is_empty() {
                    system.push_str(
                        "\n\n--- Relevant lore from the archives (ground your answer in this; quote it faithfully, never contradict it) ---\n",
                    );
                    system.push_str(context);
                }
            }
        }

        system
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::voice_ai::intent::VoiceIntent;
    use async_trait::async_trait;

    /// Captures the system prompt it was given and echoes a canned reply.
    struct SpyAi {
        captured: std::sync::Mutex<String>,
    }

    #[async_trait]
    impl GenerativeAiPort for SpyAi {
        async fn interpret_command(&self, _: &str, _: &str) -> Result<VoiceIntent, anyhow::Error> {
            unreachable!("conversation saga uses converse, not interpret_command")
        }
        async fn converse(&self, system: &str, _user: &str) -> Result<String, anyhow::Error> {
            *self.captured.lock().unwrap() = system.to_string();
            Ok("The Traveler is the great paracausal sphere that gave us the Light.".into())
        }
    }

    /// A lore port that returns a fixed excerpt.
    struct StubLore;
    #[async_trait]
    impl GrimoireDatabasePort for StubLore {
        async fn fetch_semantic_lore_context(&self, _: &str) -> Result<String, anyhow::Error> {
            Ok("The Traveler: a paracausal entity, source of the Light.".into())
        }
    }

    #[tokio::test]
    async fn grounds_prompt_with_dossier_and_lore() {
        let ai = Arc::new(SpyAi {
            captured: std::sync::Mutex::new(String::new()),
        });
        let saga = ConversationSaga::new(
            ai.clone(),
            Some(Arc::new(StubLore)),
            GhostPersonality::Warlock,
        );

        let reply = saga
            .converse("who is the Traveler?", Some("you've logged 1240 hours"))
            .await
            .unwrap();

        assert!(reply.contains("Traveler"));
        let prompt = ai.captured.lock().unwrap().clone();
        assert!(prompt.contains("1240 hours"), "dossier injected: {prompt}");
        assert!(prompt.contains("paracausal entity"), "lore injected: {prompt}");
    }

    #[tokio::test]
    async fn works_without_lore_or_dossier() {
        let ai = Arc::new(SpyAi {
            captured: std::sync::Mutex::new(String::new()),
        });
        let saga = ConversationSaga::new(ai, None, GhostPersonality::Hunter);
        let reply = saga.converse("hey Ghost", None).await.unwrap();
        assert!(!reply.is_empty());
    }
}
