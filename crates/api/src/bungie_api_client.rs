//! Generic authenticated Bungie read client.
//!
//! Rather than hand-coding an adapter per endpoint, this exposes the whole
//! Bungie Platform (Destiny 2 *and* the legacy Destiny 1 `/d1/Platform`) as a
//! single guarded GET passthrough. It attaches the API key always and the
//! signed-in Guardian's OAuth token when a membership is supplied, so the Ghost
//! can reach any read endpoint the player is authorized for.
//!
//! Security: this is **read-only** (GET) and path-allowlisted to Platform
//! routes so it can't be used as an open proxy. It rides the same dev auth seam
//! as the other routes (membership id as a parameter) — gate it behind real
//! session validation before production, same TODO as `AppState::ws_dev_token`.

use std::sync::Arc;

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use serde_json::Value;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::voice_ai::tools::{ToolCall, ToolExecutor, ToolSpec};

/// Cap tool-result size so a big Bungie payload can't blow the model's context.
const TOOL_RESULT_BUDGET: usize = 6000;

const BUNGIE_ROOT: &str = "https://www.bungie.net";
/// Path prefixes we permit (keeps this from being a generic open proxy).
const ALLOWED_PREFIXES: &[&str] = &["/Platform/", "/d1/Platform/", "/common/"];

pub struct BungieApiClient {
    http: reqwest::Client,
    api_key: String,
    token_store: Arc<dyn TokenStoragePort>,
}

impl BungieApiClient {
    pub fn new(
        http: reqwest::Client,
        api_key: impl Into<String>,
        token_store: Arc<dyn TokenStoragePort>,
    ) -> Self {
        Self {
            http,
            api_key: api_key.into(),
            token_store,
        }
    }

    /// Performs an authenticated GET against a Bungie Platform `path`
    /// (e.g. `/Platform/Destiny2/3/Profile/123/?components=200`). When
    /// `membership_id` is given, the Guardian's bearer token is attached so
    /// authenticated components are returned. Returns the parsed JSON body.
    pub async fn get(
        &self,
        membership_id: Option<&BungieMembershipId>,
        path: &str,
    ) -> Result<Value, anyhow::Error> {
        let path = normalize_path(path)?;
        let url = format!("{BUNGIE_ROOT}{path}");

        let mut request = self.http.get(&url).header("X-API-Key", &self.api_key);

        if let Some(membership_id) = membership_id {
            if let Some(token) = self.token_store.get_token(membership_id).await? {
                request = request.bearer_auth(token.access_token);
            }
        }

        let body: Value = request
            .send()
            .await
            .with_context(|| format!("GET {url}"))?
            .error_for_status()?
            .json()
            .await
            .context("decoding Bungie response")?;

        // Surface Bungie's own error envelope as an error rather than silent {}.
        if let Some(code) = body.get("ErrorCode").and_then(Value::as_i64) {
            if code != 1 {
                let message = body
                    .get("Message")
                    .and_then(Value::as_str)
                    .unwrap_or("unknown Bungie error");
                return Err(anyhow!("Bungie API error ({code}): {message}"));
            }
        }
        Ok(body)
    }
}

/// Binds a [`BungieApiClient`] to one Guardian and exposes it to the LLM as a
/// `bungie_get` tool, so the Ghost can fetch any game data the player is
/// authorized for, mid-conversation.
pub struct BungieToolExecutor {
    client: Arc<BungieApiClient>,
    membership_id: Option<BungieMembershipId>,
}

impl BungieToolExecutor {
    pub fn new(client: Arc<BungieApiClient>, membership_id: Option<BungieMembershipId>) -> Self {
        Self {
            client,
            membership_id,
        }
    }
}

#[async_trait]
impl ToolExecutor for BungieToolExecutor {
    fn specs(&self) -> Vec<ToolSpec> {
        vec![ToolSpec {
            name: "bungie_get".to_string(),
            description: "Fetch live Destiny data by performing an authenticated GET against a \
                Bungie Platform path. Use this to answer questions about the Guardian's \
                characters, inventory, triumphs, activity history, fireteams, vendors, clan, \
                or any other game data. Destiny 2 paths start with /Platform/Destiny2/... and \
                Destiny 1 paths start with /d1/Platform/Destiny/... . Example: \
                /Platform/Destiny2/{membershipType}/Profile/{destinyMembershipId}/?components=200,900"
                .to_string(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The Bungie Platform path (with query string) to GET."
                    }
                },
                "required": ["path"]
            }),
        }]
    }

    async fn run(&self, call: &ToolCall) -> Result<String, anyhow::Error> {
        if call.name != "bungie_get" {
            return Err(anyhow!("unknown tool: {}", call.name));
        }
        let args: Value = serde_json::from_str(&call.arguments)
            .with_context(|| format!("bad tool arguments: {}", call.arguments))?;
        let path = args
            .get("path")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("bungie_get requires a 'path' string"))?;

        let body = self.client.get(self.membership_id.as_ref(), path).await?;
        let mut text = body.to_string();
        if text.len() > TOOL_RESULT_BUDGET {
            text.truncate(TOOL_RESULT_BUDGET);
            text.push_str("…(truncated)");
        }
        Ok(text)
    }
}

/// Ensures the path is a leading-slash Platform route and rejects anything else
/// (so the client can't be aimed at arbitrary hosts/paths). Returns the
/// canonical path to append to the Bungie root.
fn normalize_path(path: &str) -> Result<String, anyhow::Error> {
    let trimmed = path.trim();
    // Accept a full bungie.net URL by stripping the known root.
    let rel = trimmed
        .strip_prefix(BUNGIE_ROOT)
        .or_else(|| trimmed.strip_prefix("https://www.bungie.net"))
        .or_else(|| trimmed.strip_prefix("http://www.bungie.net"))
        .unwrap_or(trimmed);

    let rel = if rel.starts_with('/') {
        rel.to_string()
    } else {
        format!("/{rel}")
    };

    // Reject traversal and protocol-relative tricks.
    if rel.contains("..") || rel.starts_with("//") {
        return Err(anyhow!("illegal path"));
    }
    if ALLOWED_PREFIXES.iter().any(|p| rel.starts_with(p)) {
        Ok(rel)
    } else {
        Err(anyhow!(
            "path must be a Bungie Platform route (one of {ALLOWED_PREFIXES:?})"
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_platform_paths() {
        assert_eq!(
            normalize_path("/Platform/Destiny2/3/Profile/1/?components=200").unwrap(),
            "/Platform/Destiny2/3/Profile/1/?components=200"
        );
        assert_eq!(
            normalize_path("d1/Platform/Destiny/Manifest/").unwrap(),
            "/d1/Platform/Destiny/Manifest/"
        );
        assert_eq!(
            normalize_path("https://www.bungie.net/Platform/User/").unwrap(),
            "/Platform/User/"
        );
    }

    #[test]
    fn rejects_non_platform_and_traversal() {
        assert!(normalize_path("/evil/endpoint").is_err());
        assert!(normalize_path("/Platform/../secrets").is_err());
        assert!(normalize_path("//attacker.com/Platform/").is_err());
    }
}
