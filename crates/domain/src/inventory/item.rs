use serde::{Deserialize, Serialize};

/// Represents the mathematical ID of any item in Destiny 2.
/// Value Object enforces that a Hash cannot be 0.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct DestinyItemHash(pub u32);

impl DestinyItemHash {
    pub fn new(hash: u32) -> Result<Self, String> {
        if hash == 0 {
            Err("Destiny Item Hash cannot be zero.".to_string())
        } else {
            Ok(Self(hash))
        }
    }
}

/// Represents the current physical location of a specific instantiated item
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ItemLocation {
    Vault,
    Postmaster,
    EquippedOnCharacter(String), // Character ID
    InventoryOnCharacter(String), // Character ID
}
