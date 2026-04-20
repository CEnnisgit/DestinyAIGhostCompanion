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
