use async_trait::async_trait;
use crate::auth::membership::BungieMembershipId;
use super::item::{DestinyItemHash, ItemLocation};

/// Secondary Port (Driven): Represents the physical connection to Bungie's REST API.
/// Implementations of this port MUST execute exactly ONE action per await.
#[async_trait]
pub trait BungieInventoryPort: Send + Sync {
    /// Discovers where an item currently sits in the user's account
    async fn locate_item(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash) -> Result<ItemLocation, anyhow::Error>;
    
    /// Translates an NLP string (like "Warlock" or "primary") to the user's 64-bit character ID
    async fn resolve_character_id(&self, membership_id: &BungieMembershipId, character_class: &str) -> Result<String, anyhow::Error>;
    
    /// Physically moves an item (e.g. Vault -> Character)
    async fn transfer_item(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash, to_vault: bool, character_id: &str) -> Result<(), anyhow::Error>;
    
    /// Physically equips an item
    async fn equip_item(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash, character_id: &str) -> Result<(), anyhow::Error>;
    
    /// Physically pulls an item from the Postmaster
    async fn pull_postmaster(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash, character_id: &str) -> Result<(), anyhow::Error>;
}

/// Secondary Port (Driven): Represents the in-memory SQLite Manifest cache.
#[async_trait]
pub trait ManifestDatabasePort: Send + Sync {
    /// Attempts to cleanly or fuzzy-match a transcribed string (e.g., "Sun Shot") to an actual Item Hash
    async fn resolve_item_hash(&self, transcribed_name: &str) -> Result<DestinyItemHash, anyhow::Error>;
}
