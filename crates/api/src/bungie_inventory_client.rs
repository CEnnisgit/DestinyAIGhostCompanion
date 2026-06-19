//! Phase 4D: reqwest adapter for the inventory domain's `BungieInventoryPort`.
//!
//! The domain ports intentionally pass only `membership_id` + item `hash`
//! (+ `character_id`). Bungie's REST API, however, needs the OAuth access token,
//! the platform `membershipType`, and the item *instance* id. This adapter
//! resolves all three internally:
//!   - access token  ← `TokenStoragePort` (keyed by membership id)
//!   - membershipType ← `GetMembershipsForCurrentUser`
//!   - instance id    ← the user's profile components
//!
//! ADR-010: every Bungie mutation is awaited serially — no `join!`/concurrency.

use std::sync::Arc;

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use serde_json::{json, Value};

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::inventory::item::{DestinyItemHash, ItemLocation};
use domain::inventory::ports::BungieInventoryPort;

const PLATFORM_BASE: &str = "https://www.bungie.net/Platform";
/// Bucket hash for a character's Postmaster (lost items) inventory.
const POSTMASTER_BUCKET_HASH: u64 = 215593132;

pub struct BungieInventoryClient {
    http: reqwest::Client,
    api_key: String,
    token_store: Arc<dyn TokenStoragePort>,
}

impl BungieInventoryClient {
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

    /// Resolves `(access_token, membership_type)` for a user. Membership type is
    /// not stored with the token, so we look it up from Bungie.
    async fn auth_context(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<(String, i64), anyhow::Error> {
        let token = self
            .token_store
            .get_token(membership_id)
            .await?
            .ok_or_else(|| anyhow!("no stored Bungie token for this user — please sign in again"))?;

        let memberships: Value = self
            .authed_get(
                &token.access_token,
                &format!("{PLATFORM_BASE}/User/GetMembershipsForCurrentUser/"),
            )
            .await?;

        let membership_type = extract_membership_type(&memberships, &membership_id.0)
            .ok_or_else(|| anyhow!("could not determine Destiny platform for this user"))?;

        Ok((token.access_token, membership_type))
    }

    /// Fetches the profile components needed to locate items.
    async fn fetch_profile(
        &self,
        access_token: &str,
        membership_type: i64,
        membership_id: &BungieMembershipId,
    ) -> Result<Value, anyhow::Error> {
        let url = format!(
            "{PLATFORM_BASE}/Destiny2/{membership_type}/Profile/{}/?components=102,201,205,300",
            membership_id.0
        );
        self.authed_get(access_token, &url).await
    }

    async fn authed_get(&self, access_token: &str, url: &str) -> Result<Value, anyhow::Error> {
        let value: Value = self
            .http
            .get(url)
            .bearer_auth(access_token)
            .header("X-API-Key", &self.api_key)
            .send()
            .await
            .with_context(|| format!("GET {url}"))?
            .error_for_status()?
            .json()
            .await
            .context("decoding Bungie response")?;
        check_bungie_ok(&value)?;
        Ok(value)
    }

    async fn authed_post(
        &self,
        access_token: &str,
        url: &str,
        body: &Value,
    ) -> Result<(), anyhow::Error> {
        let value: Value = self
            .http
            .post(url)
            .bearer_auth(access_token)
            .header("X-API-Key", &self.api_key)
            .json(body)
            .send()
            .await
            .with_context(|| format!("POST {url}"))?
            .error_for_status()?
            .json()
            .await
            .context("decoding Bungie response")?;
        check_bungie_ok(&value)
    }

    /// Finds the item's `(location, instance_id)` in the profile, fetching context as needed.
    async fn locate_with_instance(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<(String, i64, Value), anyhow::Error> {
        let (access_token, membership_type) = self.auth_context(membership_id).await?;
        let profile = self
            .fetch_profile(&access_token, membership_type, membership_id)
            .await?;
        Ok((access_token, membership_type, profile))
    }
}

#[async_trait]
impl BungieInventoryPort for BungieInventoryClient {
    async fn locate_item(
        &self,
        membership_id: &BungieMembershipId,
        hash: DestinyItemHash,
    ) -> Result<ItemLocation, anyhow::Error> {
        let (_, _, profile) = self.locate_with_instance(membership_id).await?;
        find_item(&profile, hash.0)
            .map(|found| found.location)
            .ok_or_else(|| anyhow!("item {} is not on this account", hash.0))
    }

    async fn transfer_item(
        &self,
        membership_id: &BungieMembershipId,
        hash: DestinyItemHash,
        to_vault: bool,
        character_id: &str,
    ) -> Result<(), anyhow::Error> {
        let (access_token, membership_type, profile) =
            self.locate_with_instance(membership_id).await?;
        let found = find_item(&profile, hash.0)
            .ok_or_else(|| anyhow!("item {} is not on this account", hash.0))?;

        let body = json!({
            "itemReferenceHash": hash.0,
            "stackSize": 1,
            "transferToVault": to_vault,
            "itemId": found.instance_id,
            "characterId": character_id,
            "membershipType": membership_type,
        });
        self.authed_post(
            &access_token,
            &format!("{PLATFORM_BASE}/Destiny2/Actions/Items/TransferItem/"),
            &body,
        )
        .await
    }

    async fn equip_item(
        &self,
        membership_id: &BungieMembershipId,
        hash: DestinyItemHash,
        character_id: &str,
    ) -> Result<(), anyhow::Error> {
        let (access_token, membership_type, profile) =
            self.locate_with_instance(membership_id).await?;
        let found = find_item(&profile, hash.0)
            .ok_or_else(|| anyhow!("item {} is not on this account", hash.0))?;

        let body = json!({
            "itemId": found.instance_id,
            "characterId": character_id,
            "membershipType": membership_type,
        });
        self.authed_post(
            &access_token,
            &format!("{PLATFORM_BASE}/Destiny2/Actions/Items/EquipItem/"),
            &body,
        )
        .await
    }

    async fn pull_postmaster(
        &self,
        membership_id: &BungieMembershipId,
        hash: DestinyItemHash,
        character_id: &str,
    ) -> Result<(), anyhow::Error> {
        let (access_token, membership_type, profile) =
            self.locate_with_instance(membership_id).await?;
        let found = find_item(&profile, hash.0)
            .ok_or_else(|| anyhow!("item {} is not on this account", hash.0))?;

        let body = json!({
            "itemReferenceHash": hash.0,
            "stackSize": 1,
            "itemId": found.instance_id,
            "characterId": character_id,
            "membershipType": membership_type,
        });
        self.authed_post(
            &access_token,
            &format!("{PLATFORM_BASE}/Destiny2/Actions/Items/PullFromPostmaster/"),
            &body,
        )
        .await
    }
}

/// Bungie wraps every payload as `{ "ErrorCode": 1, "Response": ... }`; anything
/// other than 1 is an application-level failure.
fn check_bungie_ok(value: &Value) -> Result<(), anyhow::Error> {
    match value.get("ErrorCode").and_then(Value::as_i64) {
        Some(1) => Ok(()),
        other => {
            let status = value
                .get("ErrorStatus")
                .and_then(Value::as_str)
                .unwrap_or("Unknown");
            let message = value
                .get("Message")
                .and_then(Value::as_str)
                .unwrap_or("Bungie API error");
            Err(anyhow!(
                "Bungie error ({status}, code {}): {message}",
                other.unwrap_or(-1)
            ))
        }
    }
}

/// Reads the platform `membershipType` for the matching destiny membership.
fn extract_membership_type(memberships: &Value, membership_id: &str) -> Option<i64> {
    let destiny = memberships
        .pointer("/Response/destinyMemberships")?
        .as_array()?;
    // Prefer the membership whose id matches; fall back to the first.
    destiny
        .iter()
        .find(|m| m.get("membershipId").and_then(Value::as_str) == Some(membership_id))
        .or_else(|| destiny.first())
        .and_then(|m| m.get("membershipType").and_then(Value::as_i64))
}

struct FoundItem {
    location: ItemLocation,
    instance_id: String,
}

/// Scans the profile components (equipment, character inventories, vault) for an
/// instanced item by hash, returning its location and instance id.
fn find_item(profile: &Value, hash: u32) -> Option<FoundItem> {
    let hash = hash as u64;

    // 1. Equipped on a character (component 205).
    if let Some(map) = profile.pointer("/Response/characterEquipment/data").and_then(Value::as_object) {
        for (character_id, data) in map {
            if let Some(item) = items_of(data).into_iter().find(|i| item_hash(i) == Some(hash)) {
                if let Some(instance_id) = instance_id(item) {
                    return Some(FoundItem {
                        location: ItemLocation::EquippedOnCharacter(character_id.clone()),
                        instance_id,
                    });
                }
            }
        }
    }

    // 2. In a character inventory (component 201) — Postmaster bucket is special.
    if let Some(map) = profile.pointer("/Response/characterInventories/data").and_then(Value::as_object) {
        for (character_id, data) in map {
            if let Some(item) = items_of(data).into_iter().find(|i| item_hash(i) == Some(hash)) {
                if let Some(instance_id) = instance_id(item) {
                    let location = if bucket_hash(item) == Some(POSTMASTER_BUCKET_HASH) {
                        ItemLocation::Postmaster
                    } else {
                        ItemLocation::InventoryOnCharacter(character_id.clone())
                    };
                    return Some(FoundItem { location, instance_id });
                }
            }
        }
    }

    // 3. In the shared vault (component 102 / profileInventory).
    if let Some(items) = profile.pointer("/Response/profileInventory/data/items").and_then(Value::as_array) {
        if let Some(item) = items.iter().find(|i| item_hash(i) == Some(hash)) {
            if let Some(instance_id) = instance_id(item) {
                return Some(FoundItem {
                    location: ItemLocation::Vault,
                    instance_id,
                });
            }
        }
    }

    None
}

fn items_of(data: &Value) -> Vec<&Value> {
    data.get("items")
        .and_then(Value::as_array)
        .map(|a| a.iter().collect())
        .unwrap_or_default()
}

fn item_hash(item: &Value) -> Option<u64> {
    item.get("itemHash").and_then(Value::as_u64)
}

fn bucket_hash(item: &Value) -> Option<u64> {
    item.get("bucketHash").and_then(Value::as_u64)
}

fn instance_id(item: &Value) -> Option<String> {
    item.get("itemInstanceId")
        .and_then(Value::as_str)
        .map(str::to_owned)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_profile() -> Value {
        json!({
            "Response": {
                "characterEquipment": { "data": {
                    "char_equip": { "items": [
                        { "itemHash": 111, "itemInstanceId": "inst-equipped", "bucketHash": 1498876634 }
                    ]}
                }},
                "characterInventories": { "data": {
                    "char_inv": { "items": [
                        { "itemHash": 222, "itemInstanceId": "inst-inv", "bucketHash": 1498876634 },
                        { "itemHash": 333, "itemInstanceId": "inst-post", "bucketHash": 215593132 }
                    ]}
                }},
                "profileInventory": { "data": { "items": [
                    { "itemHash": 444, "itemInstanceId": "inst-vault", "bucketHash": 138197802 }
                ]}}
            }
        })
    }

    #[test]
    fn finds_equipped_item() {
        let found = find_item(&sample_profile(), 111).unwrap();
        assert_eq!(found.instance_id, "inst-equipped");
        assert_eq!(found.location, ItemLocation::EquippedOnCharacter("char_equip".into()));
    }

    #[test]
    fn finds_inventory_item() {
        let found = find_item(&sample_profile(), 222).unwrap();
        assert_eq!(found.location, ItemLocation::InventoryOnCharacter("char_inv".into()));
    }

    #[test]
    fn postmaster_bucket_classifies_as_postmaster() {
        let found = find_item(&sample_profile(), 333).unwrap();
        assert_eq!(found.location, ItemLocation::Postmaster);
        assert_eq!(found.instance_id, "inst-post");
    }

    #[test]
    fn finds_vault_item() {
        let found = find_item(&sample_profile(), 444).unwrap();
        assert_eq!(found.location, ItemLocation::Vault);
    }

    #[test]
    fn missing_item_returns_none() {
        assert!(find_item(&sample_profile(), 999).is_none());
    }

    #[test]
    fn extract_membership_type_prefers_matching_id() {
        let memberships = json!({ "Response": { "destinyMemberships": [
            { "membershipId": "aaa", "membershipType": 1 },
            { "membershipId": "bbb", "membershipType": 3 }
        ]}});
        assert_eq!(extract_membership_type(&memberships, "bbb"), Some(3));
        assert_eq!(extract_membership_type(&memberships, "zzz"), Some(1)); // fallback to first
    }
}
