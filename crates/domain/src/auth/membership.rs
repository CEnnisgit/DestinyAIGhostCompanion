use serde::{Deserialize, Serialize};

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
