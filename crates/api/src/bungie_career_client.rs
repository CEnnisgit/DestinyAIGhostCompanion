//! Phase 5: reqwest adapter for the career domain's `CareerStatsPort`.
//!
//! Reads a Guardian's account stats + profile (records/characters) from Bungie
//! and distills them into a `GuardianProfile` for personalization.

use std::sync::Arc;

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use serde_json::Value;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::career::ports::CareerStatsPort;
use domain::career::profile::GuardianProfile;

const PLATFORM_BASE: &str = "https://www.bungie.net/Platform";

pub struct BungieCareerClient {
    http: reqwest::Client,
    api_key: String,
    token_store: Arc<dyn TokenStoragePort>,
}

impl BungieCareerClient {
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

#[async_trait]
impl CareerStatsPort for BungieCareerClient {
    async fn fetch_profile(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<GuardianProfile, anyhow::Error> {
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

        let stats = self
            .get(
                &token.access_token,
                &format!("{PLATFORM_BASE}/Destiny2/{membership_type}/Account/{}/Stats/", membership_id.0),
            )
            .await?;
        let profile = self
            .get(
                &token.access_token,
                &format!(
                    "{PLATFORM_BASE}/Destiny2/{membership_type}/Profile/{}/?components=100,200,900",
                    membership_id.0
                ),
            )
            .await?;

        Ok(build_profile(&stats, &profile))
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

/// Pulls a nested numeric value, e.g. `["allPvP","allTime","secondsPlayed","basic","value"]`.
fn num_at(root: &Value, path: &[&str]) -> f64 {
    let mut cur = root;
    for key in path {
        match cur.get(key) {
            Some(next) => cur = next,
            None => return 0.0,
        }
    }
    cur.as_f64().unwrap_or(0.0)
}

/// Builds a `GuardianProfile` from the account-stats and profile responses.
fn build_profile(stats: &Value, profile: &Value) -> GuardianProfile {
    let results = stats
        .pointer("/Response/mergedAllCharacters/results")
        .cloned()
        .unwrap_or(Value::Null);

    let pve_secs = num_at(&results, &["allPvE", "allTime", "secondsPlayed", "basic", "value"]);
    let pvp_secs = num_at(&results, &["allPvP", "allTime", "secondsPlayed", "basic", "value"]);
    let total_hours = ((pve_secs + pvp_secs) / 3600.0) as u32;
    let crucible_kd = num_at(&results, &["allPvP", "allTime", "killsDeathsRatio", "basic", "value"]) as f32;

    let triumph_score = profile
        .pointer("/Response/profileRecords/data/activeScore")
        .and_then(Value::as_i64)
        .or_else(|| profile.pointer("/Response/profileRecords/data/score").and_then(Value::as_i64))
        .unwrap_or(0) as u32;

    let mut classes: Vec<String> = Vec::new();
    let mut favorite_class: Option<String> = None;
    let mut latest_played = String::new();
    let mut character_count = 0u32;

    if let Some(map) = profile.pointer("/Response/characters/data").and_then(Value::as_object) {
        character_count = map.len() as u32;
        for character in map.values() {
            let class = class_name(character.get("classType").and_then(Value::as_i64).unwrap_or(3)).to_string();
            if !classes.contains(&class) {
                classes.push(class.clone());
            }
            let played = character.get("dateLastPlayed").and_then(Value::as_str).unwrap_or("").to_string();
            if played > latest_played {
                latest_played = played;
                favorite_class = Some(class);
            }
        }
    }

    GuardianProfile {
        total_hours,
        crucible_kd,
        triumph_score,
        character_count,
        classes,
        favorite_class,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn builds_profile_from_responses() {
        let stats = json!({
            "Response": { "mergedAllCharacters": { "results": {
                "allPvE": { "allTime": { "secondsPlayed": { "basic": { "value": 3_600_000.0 } } } },
                "allPvP": { "allTime": {
                    "secondsPlayed": { "basic": { "value": 864_000.0 } },
                    "killsDeathsRatio": { "basic": { "value": 1.42 } }
                }}
            }}}
        });
        let profile = json!({
            "Response": {
                "profileRecords": { "data": { "activeScore": 142000 } },
                "characters": { "data": {
                    "c1": { "classType": 1, "dateLastPlayed": "2026-06-01T00:00:00Z" },
                    "c2": { "classType": 2, "dateLastPlayed": "2026-06-19T00:00:00Z" }
                }}
            }
        });
        let p = build_profile(&stats, &profile);
        assert_eq!(p.total_hours, (3_600_000.0 + 864_000.0) as u32 / 3600); // 1240
        assert_eq!(p.crucible_kd, 1.42);
        assert_eq!(p.triumph_score, 142000);
        assert_eq!(p.character_count, 2);
        assert_eq!(p.favorite_class.as_deref(), Some("Warlock")); // most recently played
    }
}
