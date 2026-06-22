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
use serde_json::Value;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;

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
