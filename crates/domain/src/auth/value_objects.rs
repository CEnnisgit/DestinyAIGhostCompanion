use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Represents the raw OAuth tokens provided by Bungie
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BungieOAuthToken {
    pub access_token: String,
    pub refresh_token: String,
    pub expires_at: DateTime<Utc>,
    pub refresh_expires_at: DateTime<Utc>,
}

/// A rigorous wrapper around the primary key we use to identify users locally
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct BungieMembershipId(pub String);

/// Ensures a Bungie ID cannot be instantiated empty
impl BungieMembershipId {
    pub fn new(id: impl Into<String>) -> Result<Self, String> {
        let parsed = id.into();
        if parsed.trim().is_empty() {
            Err("Bungie Membership ID cannot be empty".to_string())
        } else {
            Ok(Self(parsed))
        }
    }
}
