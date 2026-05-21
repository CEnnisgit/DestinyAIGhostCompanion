use std::sync::Arc;
use async_trait::async_trait;
use reqwest::Client;
use serde_json::Value;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::inventory::item::{DestinyItemHash, ItemLocation};
use domain::inventory::ports::BungieInventoryPort;

pub struct BungieInventoryClient {
    http_client: Client,
    api_key: String,
    token_storage: Arc<dyn TokenStoragePort>,
}

impl BungieInventoryClient {
    pub fn new(http_client: Client, api_key: String, token_storage: Arc<dyn TokenStoragePort>) -> Self {
        Self { http_client, api_key, token_storage }
    }

    async fn get_access_token(&self, membership_id: &BungieMembershipId) -> Result<String, anyhow::Error> {
        let token_data = self.token_storage.get_token(membership_id).await?
            .ok_or_else(|| anyhow::anyhow!("No Bungie token found for this user."))?;
        Ok(token_data.access_token)
    }

    async fn post_action(&self, access_token: &str, path: &str, body: Value) -> Result<(), anyhow::Error> {
        let url = format!("https://www.bungie.net/Platform/Destiny2/Actions/Items/{}/", path);
        let res = self.http_client.post(&url)
            .header("X-API-Key", &self.api_key)
            .header("Authorization", format!("Bearer {}", access_token))
            .json(&body)
            .send()
            .await?;

        let status = res.status();
        let text = res.text().await.unwrap_or_default();
        
        if !status.is_success() {
            return Err(anyhow::anyhow!("Bungie API Error: {} - {}", status, text));
        }

        let json: Value = serde_json::from_str(&text)?;
        if json["ErrorCode"].as_i64() != Some(1) {
            let msg = json["Message"].as_str().unwrap_or("Unknown error");
            return Err(anyhow::anyhow!("Bungie Error: {}", msg));
        }

        Ok(())
    }

    /// Internal helper that hits the GET Profile endpoint to resolve a Hash into its ItemLocation and dynamic instanceId.
    /// This ensures we never pollute the domain layer with Bungie's dynamic ID requirements.
    async fn locate_and_resolve_instance(
        &self, 
        membership_id: &BungieMembershipId, 
        hash: DestinyItemHash,
        access_token: &str
    ) -> Result<(ItemLocation, String), anyhow::Error> {
        // 3 is all Destiny memberships
        let url = format!("https://www.bungie.net/Platform/Destiny2/3/Profile/{}/?components=102,201,205,300", membership_id.0);
        let res = self.http_client.get(&url)
            .header("X-API-Key", &self.api_key)
            .header("Authorization", format!("Bearer {}", access_token))
            .send()
            .await?;

        let status = res.status();
        let text = res.text().await.unwrap_or_default();
        if !status.is_success() {
            return Err(anyhow::anyhow!("Bungie Profile Error: {} - {}", status, text));
        }

        let json: Value = serde_json::from_str(&text)?;
        let response = &json["Response"];
        let hash_u32 = hash.0;

        // Look in Vault (102)
        if let Some(vault_items) = response["profileInventory"]["data"]["items"].as_array() {
            for item in vault_items {
                if item["itemHash"].as_u64() == Some(hash_u32 as u64) 
                    && let Some(instance_id) = item["itemInstanceId"].as_str() 
                {
                    return Ok((ItemLocation::Vault, instance_id.to_string()));
                }
            }
        }

        // Look in Characters (201, 205)
        if let Some(char_eq) = response["characterEquipment"]["data"].as_object() {
            for (char_id, char_data) in char_eq {
                if let Some(items) = char_data["items"].as_array() {
                    for item in items {
                        if item["itemHash"].as_u64() == Some(hash_u32 as u64) 
                            && let Some(instance_id) = item["itemInstanceId"].as_str() 
                        {
                            return Ok((ItemLocation::EquippedOnCharacter(char_id.clone()), instance_id.to_string()));
                        }
                    }
                }
            }
        }
        
        if let Some(char_inv) = response["characterInventories"]["data"].as_object() {
            for (char_id, char_data) in char_inv {
                if let Some(items) = char_data["items"].as_array() {
                    for item in items {
                        if item["itemHash"].as_u64() == Some(hash_u32 as u64) 
                            && let Some(instance_id) = item["itemInstanceId"].as_str() 
                        {
                            return Ok((ItemLocation::InventoryOnCharacter(char_id.clone()), instance_id.to_string()));
                        }
                    }
                }
            }
        }

        Err(anyhow::anyhow!("Item not found on account"))
    }
}

#[async_trait]
impl BungieInventoryPort for BungieInventoryClient {
    async fn locate_item(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash) -> Result<ItemLocation, anyhow::Error> {
        let access_token = self.get_access_token(membership_id).await?;
        let (location, _) = self.locate_and_resolve_instance(membership_id, hash, &access_token).await?;
        Ok(location)
    }
    
    async fn transfer_item(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash, to_vault: bool, character_id: &str) -> Result<(), anyhow::Error> {
        let access_token = self.get_access_token(membership_id).await?;
        let (_, instance_id) = self.locate_and_resolve_instance(membership_id, hash, &access_token).await?;
        
        let body = serde_json::json!({
            "itemReferenceHash": hash.0,
            "stackSize": 1,
            "transferToVault": to_vault,
            "itemId": instance_id,
            "characterId": character_id,
            "membershipType": 3
        });
        
        self.post_action(&access_token, "TransferItem", body).await
    }
    
    async fn equip_item(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash, character_id: &str) -> Result<(), anyhow::Error> {
        let access_token = self.get_access_token(membership_id).await?;
        let (_, instance_id) = self.locate_and_resolve_instance(membership_id, hash, &access_token).await?;
        
        let body = serde_json::json!({
            "itemId": instance_id,
            "characterId": character_id,
            "membershipType": 3
        });
        
        self.post_action(&access_token, "EquipItem", body).await
    }
    
    async fn pull_postmaster(&self, membership_id: &BungieMembershipId, hash: DestinyItemHash, character_id: &str) -> Result<(), anyhow::Error> {
        let access_token = self.get_access_token(membership_id).await?;
        let (_, instance_id) = self.locate_and_resolve_instance(membership_id, hash, &access_token).await?;
        
        let body = serde_json::json!({
            "itemReferenceHash": hash.0,
            "stackSize": 1,
            "itemId": instance_id,
            "characterId": character_id,
            "membershipType": 3
        });
        
        self.post_action(&access_token, "PullFromPostmaster", body).await
    }
}
