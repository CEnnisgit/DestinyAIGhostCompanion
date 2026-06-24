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
use crate::voice_ai::tools::{AiTurn, ConversationItem, ToolExecutor};

/// Safety bound on tool-call rounds per message (prevents loops / runaway cost).
const MAX_TOOL_ROUNDS: usize = 4;

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
        self.converse_with_tools(message, guardian_context, &[], None)
            .await
    }

    /// Like [`Self::converse`], but with two extra grounding sources:
    /// - `history`: prior turns of this conversation (oldest first), so the Ghost
    ///   has short-term memory and can follow up naturally.
    /// - `tools`: when supplied, the Ghost may call tools (e.g. live Bungie reads)
    ///   mid-answer to fetch whatever game data the question needs.
    pub async fn converse_with_tools(
        &self,
        message: &str,
        guardian_context: Option<&str>,
        history: &[ConversationItem],
        tools: Option<&dyn ToolExecutor>,
    ) -> Result<String, anyhow::Error> {
        let system_prompt = self.build_system_prompt(message, guardian_context).await;
        // The single-shot path is only valid with no history and no tools; any
        // multi-turn or tool conversation must go through the chat_turn loop.
        if history.is_empty() && tools.is_none() {
            return self.ai.converse(&system_prompt, message).await;
        }
        self.run_tool_loop(&system_prompt, history, message, tools).await
    }

    /// Drives the model ↔ tool loop until it produces a final reply (or the round
    /// budget is exhausted, after which we force a tool-free answer). `history`
    /// (prior turns) is replayed before the current message; `tools` is optional.
    async fn run_tool_loop(
        &self,
        system_prompt: &str,
        history: &[ConversationItem],
        message: &str,
        tools: Option<&dyn ToolExecutor>,
    ) -> Result<String, anyhow::Error> {
        let specs = tools.map(|t| t.specs()).unwrap_or_default();

        let mut items = Vec::with_capacity(history.len() + 2);
        items.push(ConversationItem::System(system_prompt.to_string()));
        items.extend(history.iter().cloned());
        items.push(ConversationItem::User(message.to_string()));

        for _ in 0..MAX_TOOL_ROUNDS {
            match self.ai.chat_turn(&items, &specs).await? {
                AiTurn::Reply(text) => return Ok(text),
                AiTurn::ToolCalls(calls) if !calls.is_empty() && tools.is_some() => {
                    let executor = tools.expect("guarded by tools.is_some()");
                    items.push(ConversationItem::Assistant {
                        content: None,
                        tool_calls: calls.clone(),
                    });
                    for call in &calls {
                        let content = executor
                            .run(call)
                            .await
                            .unwrap_or_else(|e| format!("tool error: {e}"));
                        items.push(ConversationItem::ToolResult {
                            call_id: call.id.clone(),
                            name: call.name.clone(),
                            content,
                        });
                    }
                }
                // No tools to run (or an empty batch): break to the final ask.
                AiTurn::ToolCalls(_) => break,
            }
        }

        // Round budget spent (or a degenerate empty batch): ask once more with no
        // tools so the model must commit to a prose answer from what it gathered.
        match self.ai.chat_turn(&items, &[]).await? {
            AiTurn::Reply(text) => Ok(text),
            AiTurn::ToolCalls(_) => {
                Ok("I gathered your records but couldn't compose an answer in time. Ask me again?".to_string())
            }
        }
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

    use crate::voice_ai::tools::{AiTurn, ConversationItem, ToolCall, ToolExecutor, ToolSpec};

    /// First turn requests a tool; once a tool result is in history, replies.
    struct ToolingAi {
        rounds: std::sync::Mutex<u32>,
    }
    #[async_trait]
    impl GenerativeAiPort for ToolingAi {
        async fn interpret_command(&self, _: &str, _: &str) -> Result<VoiceIntent, anyhow::Error> {
            unreachable!()
        }
        async fn chat_turn(
            &self,
            items: &[ConversationItem],
            _tools: &[ToolSpec],
        ) -> Result<AiTurn, anyhow::Error> {
            let saw_tool_result = items
                .iter()
                .any(|i| matches!(i, ConversationItem::ToolResult { .. }));
            if saw_tool_result {
                Ok(AiTurn::Reply("You cleared King's Fall on June 18 with Saint-14.".into()))
            } else {
                *self.rounds.lock().unwrap() += 1;
                Ok(AiTurn::ToolCalls(vec![ToolCall {
                    id: "call_1".into(),
                    name: "bungie_get".into(),
                    arguments: "{\"path\":\"/Platform/Destiny2/3/Account/1/Stats/\"}".into(),
                }]))
            }
        }
    }

    struct SpyExecutor {
        ran: std::sync::Mutex<u32>,
    }
    #[async_trait]
    impl ToolExecutor for SpyExecutor {
        fn specs(&self) -> Vec<ToolSpec> {
            vec![ToolSpec {
                name: "bungie_get".into(),
                description: "read Bungie data".into(),
                parameters: serde_json::json!({"type":"object"}),
            }]
        }
        async fn run(&self, call: &ToolCall) -> Result<String, anyhow::Error> {
            *self.ran.lock().unwrap() += 1;
            assert_eq!(call.name, "bungie_get");
            Ok("{\"raid\":\"King's Fall\"}".into())
        }
    }

    #[tokio::test]
    async fn tool_loop_runs_tool_then_replies() {
        let ai = Arc::new(ToolingAi { rounds: std::sync::Mutex::new(0) });
        let saga = ConversationSaga::new(ai, None, GhostPersonality::Warlock);
        let exec = SpyExecutor { ran: std::sync::Mutex::new(0) };

        let reply = saga
            .converse_with_tools("when did I last clear a raid?", None, &[], Some(&exec))
            .await
            .unwrap();

        assert!(reply.contains("King's Fall"));
        assert_eq!(*exec.ran.lock().unwrap(), 1, "the tool was executed once");
    }

    /// Replays prior turns and echoes back the items it received, so we can
    /// assert history reaches the model.
    struct HistorySpyAi {
        seen_history: std::sync::Mutex<bool>,
    }
    #[async_trait]
    impl GenerativeAiPort for HistorySpyAi {
        async fn interpret_command(&self, _: &str, _: &str) -> Result<VoiceIntent, anyhow::Error> {
            unreachable!()
        }
        async fn chat_turn(
            &self,
            items: &[ConversationItem],
            _tools: &[ToolSpec],
        ) -> Result<AiTurn, anyhow::Error> {
            // The prior user turn ("the Witness") must be present before the new one.
            let mentions_prior = items.iter().any(|i| {
                matches!(i, ConversationItem::User(t) if t.contains("the Witness"))
            });
            *self.seen_history.lock().unwrap() = mentions_prior;
            Ok(AiTurn::Reply("It is the antagonist of the Light and Dark saga.".into()))
        }
    }

    #[tokio::test]
    async fn history_is_replayed_to_the_model() {
        let ai = Arc::new(HistorySpyAi { seen_history: std::sync::Mutex::new(false) });
        let saga = ConversationSaga::new(ai.clone(), None, GhostPersonality::Warlock);
        let history = vec![
            ConversationItem::User("who is the Witness?".into()),
            ConversationItem::Assistant {
                content: Some("The Witness is a paracausal entity.".into()),
                tool_calls: vec![],
            },
        ];

        let reply = saga
            .converse_with_tools("tell me more", None, &history, None)
            .await
            .unwrap();

        assert!(!reply.is_empty());
        assert!(*ai.seen_history.lock().unwrap(), "prior turns reached the model");
    }
}
