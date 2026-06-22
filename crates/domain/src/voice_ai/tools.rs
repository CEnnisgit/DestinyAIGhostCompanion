//! Tool-calling primitives for the conversational Ghost.
//!
//! These let the LLM decide, mid-conversation, that it needs live game data and
//! *call a tool* to fetch it — then weave the result into its answer. The domain
//! defines the vocabulary (specs, calls, turns) and the [`ToolExecutor`] port;
//! adapters implement the executor (e.g. over the Bungie API) and the wire
//! format (in the `GenerativeAiPort` adapter).

use async_trait::async_trait;
use serde_json::Value;

/// A tool the model may call, described to it as a JSON-schema function.
#[derive(Debug, Clone, PartialEq)]
pub struct ToolSpec {
    pub name: String,
    pub description: String,
    /// JSON Schema for the arguments object.
    pub parameters: Value,
}

/// A request from the model to invoke a tool, with raw JSON `arguments`.
#[derive(Debug, Clone, PartialEq)]
pub struct ToolCall {
    /// Provider-assigned id used to correlate the result back to the call.
    pub id: String,
    pub name: String,
    pub arguments: String,
}

/// The outcome of one model turn: either a final reply or a batch of tool calls.
#[derive(Debug, Clone, PartialEq)]
pub enum AiTurn {
    Reply(String),
    ToolCalls(Vec<ToolCall>),
}

/// One entry of the running conversation the adapter serializes for the model.
#[derive(Debug, Clone, PartialEq)]
pub enum ConversationItem {
    System(String),
    User(String),
    /// A model turn that requested tools (and possibly some prose alongside).
    Assistant {
        content: Option<String>,
        tool_calls: Vec<ToolCall>,
    },
    /// The result of running a tool, fed back to the model.
    ToolResult {
        call_id: String,
        name: String,
        content: String,
    },
}

/// Secondary Port (Driven): runs the tools the Ghost is allowed to call. An
/// adapter binds this to a concrete capability (e.g. authenticated Bungie reads
/// for one Guardian).
#[async_trait]
pub trait ToolExecutor: Send + Sync {
    /// The tools to advertise to the model this turn.
    fn specs(&self) -> Vec<ToolSpec>;
    /// Executes one tool call, returning content to feed back to the model.
    async fn run(&self, call: &ToolCall) -> Result<String, anyhow::Error>;
}
