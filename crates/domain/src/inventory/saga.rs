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

    /// Moves a named item to the vault (`to_vault = true`) or pulls it from the
    /// vault onto the given character (`to_vault = false`). Returns a
    /// conversational success or graceful error string.
    pub async fn process_transfer(
        &self,
        membership_id: &BungieMembershipId,
        item_name: &str,
        to_vault: bool,
        character_id: &str,
    ) -> Result<String, String> {
        let hash = self
            .manifest_port
            .resolve_item_hash(item_name)
            .await
            .map_err(|_| format!("I could not find a record for '{}' in the database.", item_name))?;

        match self
            .inventory_port
            .transfer_item(membership_id, hash, to_vault, character_id)
            .await
        {
            Ok(()) if to_vault => Ok(format!("Sent {} to the vault.", item_name)),
            Ok(()) => Ok(format!("Pulled {} from the vault to your character.", item_name)),
            Err(_) if to_vault => Err(format!("I couldn't vault '{}'. It may already be there, or your vault is full.", item_name)),
            Err(_) => Err(format!("I couldn't pull '{}' from the vault. Your inventory may be full.", item_name)),
        }
    }

    /// Pulls a named item out of the Postmaster onto the given character.
    pub async fn process_pull_postmaster(
        &self,
        membership_id: &BungieMembershipId,
        item_name: &str,
        character_id: &str,
    ) -> Result<String, String> {
        let hash = self
            .manifest_port
            .resolve_item_hash(item_name)
            .await
            .map_err(|_| format!("I could not find a record for '{}' in the database.", item_name))?;

        self.inventory_port
            .pull_postmaster(membership_id, hash, character_id)
            .await
            .map(|()| format!("Rescued {} from the Postmaster.", item_name))
            .map_err(|_| format!("Could not pull '{}' from the Postmaster — make sure you have space.", item_name))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use async_trait::async_trait;
    use std::sync::Mutex;

    /// Records the inventory calls made, so we can assert the saga drives the port.
    #[derive(Default)]
    struct SpyInventory {
        calls: Mutex<Vec<String>>,
    }
    #[async_trait]
    impl BungieInventoryPort for SpyInventory {
        async fn locate_item(&self, _: &BungieMembershipId, _: DestinyItemHash) -> Result<ItemLocation, anyhow::Error> {
            Ok(ItemLocation::Vault)
        }
        async fn transfer_item(&self, _: &BungieMembershipId, _: DestinyItemHash, to_vault: bool, character_id: &str) -> Result<(), anyhow::Error> {
            self.calls.lock().unwrap().push(format!("transfer to_vault={to_vault} char={character_id}"));
            Ok(())
        }
        async fn equip_item(&self, _: &BungieMembershipId, _: DestinyItemHash, _: &str) -> Result<(), anyhow::Error> {
            Ok(())
        }
        async fn pull_postmaster(&self, _: &BungieMembershipId, _: DestinyItemHash, character_id: &str) -> Result<(), anyhow::Error> {
            self.calls.lock().unwrap().push(format!("postmaster char={character_id}"));
            Ok(())
        }
    }

    struct StubManifest;
    #[async_trait]
    impl ManifestDatabasePort for StubManifest {
        async fn resolve_item_hash(&self, _: &str) -> Result<DestinyItemHash, anyhow::Error> {
            DestinyItemHash::new(3000).map_err(|e| anyhow::anyhow!(e))
        }
    }

    fn member() -> BungieMembershipId {
        BungieMembershipId::new("alice").unwrap()
    }

    #[tokio::test]
    async fn transfer_to_vault_drives_the_port() {
        let inv = Arc::new(SpyInventory::default());
        let saga = EquipItemSaga::new(inv.clone(), Arc::new(StubManifest));
        let msg = saga.process_transfer(&member(), "Sunshot", true, "char-1").await.unwrap();
        assert!(msg.contains("vault"));
        assert_eq!(inv.calls.lock().unwrap()[0], "transfer to_vault=true char=char-1");
    }

    #[tokio::test]
    async fn pull_postmaster_drives_the_port() {
        let inv = Arc::new(SpyInventory::default());
        let saga = EquipItemSaga::new(inv.clone(), Arc::new(StubManifest));
        let msg = saga.process_pull_postmaster(&member(), "Gjallarhorn", "char-2").await.unwrap();
        assert!(msg.contains("Postmaster"));
        assert_eq!(inv.calls.lock().unwrap()[0], "postmaster char=char-2");
    }
}
