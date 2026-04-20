use std::sync::Arc;
use crate::auth::membership::BungieMembershipId;
use super::item::{DestinyItemHash, ItemLocation};
use super::ports::{BungieInventoryPort, ManifestDatabasePort};

/// The physics engine for Inventory transactions. Enforces strict linear awaiting (ADR 010)
/// and conversational state returns upon failure (ADR 011).
pub struct EquipItemSaga {
    inventory_port: Arc<dyn BungieInventoryPort>,
    manifest_port: Arc<dyn ManifestDatabasePort>,
}

impl EquipItemSaga {
    pub fn new(
        inventory_port: Arc<dyn BungieInventoryPort>,
        manifest_port: Arc<dyn ManifestDatabasePort>,
    ) -> Self {
        Self {
            inventory_port,
            manifest_port,
        }
    }

    /// Takes a parsed Voice Intent for an item and attempts to mathematically force it
    /// onto the target character, navigating the vault and postmaster safely.
    /// Returns either a successful conversational string, or a graceful error string detailing the failure.
    pub async fn process_equip(
        &self,
        membership_id: &BungieMembershipId,
        item_name: &str,
        target_character_id: &str,
    ) -> Result<String, String> {
        
        // 1. String-to-Hash Translation
        let hash = match self.manifest_port.resolve_item_hash(item_name).await {
            Ok(h) => h,
            Err(_) => return Err(format!("I could not find a record for '{}' in the database.", item_name)),
        };

        // 2. Locate the Item physically
        let location = match self.inventory_port.locate_item(membership_id, hash).await {
            Ok(loc) => loc,
            Err(_) => return Err(format!("I couldn't find '{}' anywhere on your account.", item_name)),
        };

        // 3. Serial Physics Execution
        match location {
            ItemLocation::EquippedOnCharacter(ref current_character) if current_character == target_character_id => {
                return Ok(format!("'{}' is already equipped.", item_name));
            }
            
            ItemLocation::InventoryOnCharacter(ref current_character) if current_character == target_character_id => {
                if let Err(_) = self.inventory_port.equip_item(membership_id, hash, target_character_id).await {
                    return Err(format!("Failed to equip '{}'. Your slot might be locked.", item_name));
                }
            }
            
            ItemLocation::Vault => {
                if let Err(_) = self.inventory_port.transfer_item(membership_id, hash, false, target_character_id).await {
                    return Err(format!("Failed to pull '{}' from the vault. Your inventory is full.", item_name));
                }
                if let Err(_) = self.inventory_port.equip_item(membership_id, hash, target_character_id).await {
                    return Err(format!("Pulled '{}' from vault, but failed to equip it.", item_name));
                }
            }
            
            ItemLocation::Postmaster => {
                if let Err(_) = self.inventory_port.pull_postmaster(membership_id, hash, target_character_id).await {
                    return Err(format!("Could not rescue '{}' from postmaster. Ensure you have space.", item_name));
                }
                if let Err(_) = self.inventory_port.equip_item(membership_id, hash, target_character_id).await {
                    return Err(format!("Rescued '{}', but failed to equip it.", item_name));
                }
            }
            
            ItemLocation::EquippedOnCharacter(ref current_character) 
            | ItemLocation::InventoryOnCharacter(ref current_character) => {
                // Cross-Character Transfer Logic: Current Character -> Vault -> Target Character
                if let Err(_) = self.inventory_port.transfer_item(membership_id, hash, true, current_character).await {
                    return Err(format!("Could not vault '{}' from your other character.", item_name));
                }
                if let Err(_) = self.inventory_port.transfer_item(membership_id, hash, false, target_character_id).await {
                    return Err(format!("Added '{}' to Vault, but could not transfer to your target character.", item_name));
                }
                if let Err(_) = self.inventory_port.equip_item(membership_id, hash, target_character_id).await {
                    return Err(format!("Successfully moved '{}' across characters, but failed to equip it.", item_name));
                }
            }
        }

        Ok(format!("Successfully equipped {}.", item_name))
    }
}
