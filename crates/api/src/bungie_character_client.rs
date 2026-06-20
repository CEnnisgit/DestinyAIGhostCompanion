//! Phase 5: lists a signed-in user's Destiny characters so the app can pick an
//! equip target. Read-only query adapter (not a domain port) used by `/characters`.

use std::sync::Arc;

use anyhow::{anyhow, Context};
use serde::Serialize;
use serde_json::Value;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;

const PLATFORM_BASE: &str = "https://www.bungie.net/Platform";

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CharacterSummary {
    pub character_id: String,
    pub class_type: i64,
    pub class_name: String,
    pub light: i64,
}

pub struct CharacterClient {
    http: reqwest::Client,
    api_key: String,
    token_store: Arc<dyn TokenStoragePort>,
}

impl CharacterClient {
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

    /// Returns the user's characters (component 200), brightest first.
    pub async fn list_characters(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<Vec<CharacterSummary>, anyhow::Error> {
        let token = self
            .token_store
            .get_token(membership_id)
            .await?
            .ok_or_else(|| anyhow!("no stored Bungie token — please sign in again"))?;

        let memberships = self
            .get(&token.access_token, &format!("{PLATFORM_BASE}/User/GetMembershipsForCurrentUser/"))
            .await?;
        let membership_type = memberships
            .pointer("/Response/destinyMemberships")
            .and_then(Value::as_array)
            .and_then(|list| {
                list.iter()
                    .find(|m| m.get("membershipId").and_then(Value::as_str) == Some(&membership_id.0))
                    .or_else(|| list.first())
            })
            .and_then(|m| m.get("membershipType").and_then(Value::as_i64))
            .ok_or_else(|| anyhow!("could not determine Destiny platform"))?;

        let profile = self
            .get(
                &token.access_token,
                &format!(
                    "{PLATFORM_BASE}/Destiny2/{membership_type}/Profile/{}/?components=200",
                    membership_id.0
                ),
            )
            .await?;

        let mut characters = parse_characters(&profile);
        characters.sort_by(|a, b| b.light.cmp(&a.light));
        Ok(characters)
    }

    async fn get(&self, access_token: &str, url: &str) -> Result<Value, anyhow::Error> {
        self.http
            .get(url)
            .bearer_auth(access_token)
            .header("X-API-Key", &self.api_key)
            .send()
            .await
            .with_context(|| format!("GET {url}"))?
            .error_for_status()?
            .json()
            .await
            .context("decoding Bungie response")
    }
}

fn class_name(class_type: i64) -> &'static str {
    match class_type {
        0 => "Titan",
        1 => "Hunter",
        2 => "Warlock",
        _ => "Guardian",
    }
}

fn parse_characters(profile: &Value) -> Vec<CharacterSummary> {
    let Some(map) = profile
        .pointer("/Response/characters/data")
        .and_then(Value::as_object)
    else {
        return Vec::new();
    };

    map.iter()
        .map(|(character_id, data)| {
            let class_type = data.get("classType").and_then(Value::as_i64).unwrap_or(3);
            let light = data.get("light").and_then(Value::as_i64).unwrap_or(0);
            CharacterSummary {
                character_id: character_id.clone(),
                class_type,
                class_name: class_name(class_type).to_string(),
                light,
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn parses_characters_with_class_names() {
        let profile = json!({
            "Response": { "characters": { "data": {
                "char-a": { "classType": 1, "light": 1804 },
                "char-b": { "classType": 2, "light": 1810 }
            }}}
        });
        let mut chars = parse_characters(&profile);
        chars.sort_by_key(|c| c.character_id.clone());
        assert_eq!(chars.len(), 2);
        assert_eq!(chars[0].class_name, "Hunter");
        assert_eq!(chars[1].class_name, "Warlock");
    }
}
