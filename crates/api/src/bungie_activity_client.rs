//! reqwest adapter for the career domain's `ActivityHistoryPort`.
//!
//! Reads what the Guardian has actually *done* in-game:
//!   - `GetActivityHistory` → recent activities, when, and whether completed.
//!   - `GetPostGameCarnageReport` (PGCR) → the fireteam roster for a run.
//!   - `DestinyActivityDefinition` (manifest entity endpoint) → activity names.
//! Covers Destiny 2 and, best-effort, Destiny 1 via the legacy `/d1/Platform/`
//! endpoints. Network/parse hiccups degrade gracefully (an empty or partial
//! summary) rather than failing the whole conversation.

use std::collections::HashMap;
use std::sync::Arc;

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use serde_json::Value;

use db::ManifestActivityResolver;
use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::career::activity::{ActivityRecord, ActivitySummary, Game};
use domain::career::ports::ActivityHistoryPort;

const PLATFORM_BASE: &str = "https://www.bungie.net/Platform";
const D1_BASE: &str = "https://www.bungie.net/d1/Platform";
/// How many recent activities (per game) to surface to the Ghost.
const RECENT_LIMIT: usize = 8;
/// Cap PGCR fireteam lookups (one HTTP call each) to the most recent few.
const FIRETEAM_LOOKUPS: usize = 4;

pub struct BungieActivityClient {
    http: reqwest::Client,
    api_key: String,
    token_store: Arc<dyn TokenStoragePort>,
    /// Local manifest mirror for offline activity-name resolution (preferred).
    activity_resolver: Option<Arc<ManifestActivityResolver>>,
}

/// An activity parsed from a history response, before name resolution / fireteam.
#[derive(Debug, Clone, PartialEq)]
struct RawActivity {
    instance_id: String,
    reference_hash: i64,
    mode: String,
    period: String,
    completed: bool,
    game: Game,
    /// Name resolved inline (e.g. from a D1 `definitions` block); `None` means
    /// the caller must resolve it (D2, via the manifest entity endpoint).
    name: Option<String>,
}

impl BungieActivityClient {
    pub fn new(
        http: reqwest::Client,
        api_key: impl Into<String>,
        token_store: Arc<dyn TokenStoragePort>,
    ) -> Self {
        Self {
            http,
            api_key: api_key.into(),
            token_store,
            activity_resolver: None,
        }
    }

    /// Adds a local manifest mirror so D2 activity names resolve from the database
    /// first (offline, no rate limit), falling back to the API only on a miss.
    pub fn with_activity_resolver(mut self, resolver: Arc<ManifestActivityResolver>) -> Self {
        self.activity_resolver = Some(resolver);
        self
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

    /// Resolves a Destiny 2 activity hash to its display name. Prefers the local
    /// manifest mirror (offline, no rate limit); falls back to the manifest
    /// entity endpoint, then `None` so the caller can use the mode label.
    async fn activity_name(&self, access_token: &str, hash: i64) -> Option<String> {
        if let Some(resolver) = &self.activity_resolver {
            if let Some(name) = resolver.name(hash).await {
                return Some(name);
            }
        }
        let url =
            format!("{PLATFORM_BASE}/Destiny2/Manifest/DestinyActivityDefinition/{hash}/");
        let body = self.get(access_token, &url).await.ok()?;
        body.pointer("/Response/displayProperties/name")
            .and_then(Value::as_str)
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
    }

    /// Pulls the fireteam (other players' display names) from a PGCR.
    async fn fireteam(
        &self,
        access_token: &str,
        instance_id: &str,
        self_membership: &str,
    ) -> Vec<String> {
        let url =
            format!("{PLATFORM_BASE}/Destiny2/Stats/PostGameCarnageReport/{instance_id}/");
        match self.get(access_token, &url).await {
            Ok(body) => parse_pgcr_fireteam(&body, self_membership),
            Err(_) => Vec::new(),
        }
    }
}

#[async_trait]
impl ActivityHistoryPort for BungieActivityClient {
    async fn fetch_recent_activities(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<ActivitySummary, anyhow::Error> {
        let token = self
            .token_store
            .get_token(membership_id)
            .await?
            .ok_or_else(|| anyhow!("no stored Bungie token — please sign in again"))?;
        let access = &token.access_token;

        // Resolve the Destiny platform (membershipType) for this account.
        let memberships = self
            .get(access, &format!("{PLATFORM_BASE}/User/GetMembershipsForCurrentUser/"))
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

        // Character ids (component 200), most-recently-played first.
        let profile = self
            .get(
                access,
                &format!(
                    "{PLATFORM_BASE}/Destiny2/{membership_type}/Profile/{}/?components=200",
                    membership_id.0
                ),
            )
            .await?;
        let character_ids = parse_character_ids(&profile);

        // Gather recent D2 activities across characters.
        let mut raw: Vec<RawActivity> = Vec::new();
        for character_id in character_ids.iter().take(3) {
            let url = format!(
                "{PLATFORM_BASE}/Destiny2/{membership_type}/Account/{}/Character/{character_id}/Stats/Activities/?count=10&mode=0",
                membership_id.0
            );
            if let Ok(body) = self.get(access, &url).await {
                raw.extend(parse_activity_history(&body, Game::Destiny2));
            }
        }

        // Best-effort Destiny 1 history (legacy endpoints).
        if let Ok(d1) = self.fetch_d1(access, membership_type, &membership_id.0).await {
            raw.extend(d1);
        }

        // Most-recent-first, de-duplicated by instance, capped.
        raw.sort_by(|a, b| b.period.cmp(&a.period));
        raw.dedup_by(|a, b| a.instance_id == b.instance_id && a.instance_id != "0");
        raw.truncate(RECENT_LIMIT);

        // Resolve names (cached by hash) and fireteams (only the most recent few).
        let mut name_cache: HashMap<i64, Option<String>> = HashMap::new();
        let mut records: Vec<ActivityRecord> = Vec::new();
        for (idx, item) in raw.into_iter().enumerate() {
            // Prefer a name already inlined by the response (D1 definitions);
            // otherwise resolve D2 hashes via the manifest entity endpoint.
            let resolved = if let Some(name) = &item.name {
                Some(name.clone())
            } else if item.game == Game::Destiny2 {
                if !name_cache.contains_key(&item.reference_hash) {
                    let looked_up = self.activity_name(access, item.reference_hash).await;
                    name_cache.insert(item.reference_hash, looked_up);
                }
                name_cache.get(&item.reference_hash).cloned().flatten()
            } else {
                None
            };
            let name = resolved.unwrap_or_else(|| item.mode.clone());

            let fireteam = if idx < FIRETEAM_LOOKUPS && item.game == Game::Destiny2 {
                self.fireteam(access, &item.instance_id, &membership_id.0).await
            } else {
                Vec::new()
            };

            records.push(ActivityRecord {
                name,
                mode: item.mode,
                period: item.period,
                completed: item.completed,
                fireteam,
                game: item.game,
            });
        }

        Ok(ActivitySummary::new(records))
    }
}

impl BungieActivityClient {
    /// Best-effort Destiny 1 history. D1 activity names need the D1 manifest, so
    /// records fall back to the mode label; dates, completion, and game tag are
    /// reliable. Errors are swallowed by the caller.
    async fn fetch_d1(
        &self,
        access: &str,
        membership_type: i64,
        membership_id: &str,
    ) -> Result<Vec<RawActivity>, anyhow::Error> {
        let accounts = self
            .get(
                access,
                &format!("{D1_BASE}/Destiny/{membership_type}/Account/{membership_id}/"),
            )
            .await?;
        let mut out = Vec::new();
        if let Some(chars) = accounts
            .pointer("/Response/data/characters")
            .and_then(Value::as_array)
        {
            for ch in chars.iter().take(3) {
                let Some(char_id) = ch
                    .pointer("/characterBase/characterId")
                    .and_then(Value::as_str)
                else {
                    continue;
                };
                // `definitions=true` inlines activity names so D1 records read
                // "King's Fall" rather than just the mode label.
                let url = format!(
                    "{D1_BASE}/Destiny/Stats/ActivityHistory/{membership_type}/{membership_id}/{char_id}/?count=10&mode=0&definitions=true"
                );
                if let Ok(body) = self.get(access, &url).await {
                    out.extend(parse_activity_history(&body, Game::Destiny1));
                }
            }
        }
        Ok(out)
    }
}

/// Maps Bungie `activityMode` codes to a readable label.
fn mode_label(mode: i64) -> &'static str {
    match mode {
        2 => "Story",
        3 => "Strike",
        4 => "Raid",
        5 => "Crucible",
        6 => "Patrol",
        7 => "Activity",
        16 => "Nightfall",
        18 => "Strike", // All Strikes
        37 => "Gambit",
        46 | 47 => "Nightfall",
        63 => "Gambit",
        82 => "Dungeon",
        _ => "Activity",
    }
}

/// Parses an activity-history `Response.activities[]` array into raw records.
fn parse_activity_history(body: &Value, game: Game) -> Vec<RawActivity> {
    let Some(activities) = body
        .pointer("/Response/activities")
        .and_then(Value::as_array)
    else {
        return Vec::new();
    };

    let mut out = Vec::new();
    for activity in activities {
        let period = activity
            .get("period")
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string();
        let details = activity.get("activityDetails");
        let instance_id = details
            .and_then(|d| d.get("instanceId"))
            .and_then(Value::as_str)
            .unwrap_or("0")
            .to_string();
        let reference_hash = details
            .and_then(|d| d.get("directorActivityHash").or_else(|| d.get("referenceId")))
            .and_then(Value::as_i64)
            .unwrap_or(0);
        let mode = details
            .and_then(|d| d.get("mode"))
            .and_then(Value::as_i64)
            .unwrap_or(0);
        // `completed` lives under values.completed.basic.value (1.0 = completed).
        let completed = activity
            .pointer("/values/completed/basic/value")
            .and_then(Value::as_f64)
            .map(|v| v >= 1.0)
            .unwrap_or(false);

        if period.is_empty() {
            continue;
        }
        // D1 responses can inline activity names under Response.definitions.
        let name = body
            .pointer("/Response/definitions/activities")
            .and_then(Value::as_object)
            .and_then(|defs| defs.get(&reference_hash.to_string()))
            .and_then(|d| d.get("activityName"))
            .and_then(Value::as_str)
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty());

        out.push(RawActivity {
            instance_id,
            reference_hash,
            mode: mode_label(mode).to_string(),
            period,
            completed,
            game,
            name,
        });
    }
    out
}

/// Extracts the fireteam display names from a PGCR, excluding the Guardian.
fn parse_pgcr_fireteam(body: &Value, self_membership: &str) -> Vec<String> {
    let Some(entries) = body.pointer("/Response/entries").and_then(Value::as_array) else {
        return Vec::new();
    };
    let mut names = Vec::new();
    for entry in entries {
        let info = entry.pointer("/player/destinyUserInfo");
        let id = info
            .and_then(|i| i.get("membershipId"))
            .and_then(Value::as_str)
            .unwrap_or("");
        if id == self_membership {
            continue;
        }
        // Prefer the global Bungie name; fall back to platform display name.
        let name = info
            .and_then(|i| i.get("bungieGlobalDisplayName"))
            .and_then(Value::as_str)
            .filter(|s| !s.is_empty())
            .or_else(|| {
                info.and_then(|i| i.get("displayName")).and_then(Value::as_str)
            })
            .unwrap_or("")
            .trim()
            .to_string();
        if !name.is_empty() && !names.contains(&name) {
            names.push(name);
        }
    }
    names
}

/// Reads character ids from a profile component-200 response, most recently
/// played first.
fn parse_character_ids(profile: &Value) -> Vec<String> {
    let Some(map) = profile
        .pointer("/Response/characters/data")
        .and_then(Value::as_object)
    else {
        return Vec::new();
    };
    let mut chars: Vec<(String, String)> = map
        .values()
        .filter_map(|c| {
            let id = c.get("characterId").and_then(Value::as_str)?.to_string();
            let played = c
                .get("dateLastPlayed")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_string();
            Some((played, id))
        })
        .collect();
    chars.sort_by(|a, b| b.0.cmp(&a.0));
    chars.into_iter().map(|(_, id)| id).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn parses_activity_history() {
        let body = json!({ "Response": { "activities": [
            {
                "period": "2026-06-18T20:00:00Z",
                "activityDetails": {
                    "instanceId": "12345",
                    "directorActivityHash": 99887766,
                    "mode": 4
                },
                "values": { "completed": { "basic": { "value": 1.0 } } }
            },
            {
                "period": "2026-06-10T19:00:00Z",
                "activityDetails": { "instanceId": "0", "referenceId": 555, "mode": 5 },
                "values": { "completed": { "basic": { "value": 0.0 } } }
            }
        ]}});
        let raw = parse_activity_history(&body, Game::Destiny2);
        assert_eq!(raw.len(), 2);
        assert_eq!(raw[0].instance_id, "12345");
        assert_eq!(raw[0].reference_hash, 99887766);
        assert_eq!(raw[0].mode, "Raid");
        assert!(raw[0].completed);
        assert_eq!(raw[0].name, None); // D2 resolves names later via the manifest
        assert_eq!(raw[1].mode, "Crucible");
        assert!(!raw[1].completed);
    }

    #[test]
    fn parses_d1_inlined_activity_names() {
        // D1 with definitions=true inlines names under Response.definitions.activities.
        let body = json!({ "Response": {
            "activities": [
                {
                    "period": "2016-05-01T12:00:00Z",
                    "activityDetails": { "instanceId": "777", "referenceId": 1733556769, "mode": 4 },
                    "values": { "completed": { "basic": { "value": 1.0 } } }
                }
            ],
            "definitions": { "activities": {
                "1733556769": { "activityName": "King's Fall", "activityDescription": "Reach the Dreadnaught's core." }
            }}
        }});
        let raw = parse_activity_history(&body, Game::Destiny1);
        assert_eq!(raw.len(), 1);
        assert_eq!(raw[0].name.as_deref(), Some("King's Fall"));
        assert_eq!(raw[0].game, Game::Destiny1);
    }

    #[test]
    fn parses_pgcr_fireteam_excluding_self() {
        let body = json!({ "Response": { "entries": [
            { "player": { "destinyUserInfo": { "membershipId": "self", "bungieGlobalDisplayName": "Me" } } },
            { "player": { "destinyUserInfo": { "membershipId": "a", "bungieGlobalDisplayName": "Cayde" } } },
            { "player": { "destinyUserInfo": { "membershipId": "b", "displayName": "Saint-14" } } },
            { "player": { "destinyUserInfo": { "membershipId": "a", "bungieGlobalDisplayName": "Cayde" } } }
        ]}});
        let team = parse_pgcr_fireteam(&body, "self");
        assert_eq!(team, vec!["Cayde".to_string(), "Saint-14".to_string()]);
    }

    #[test]
    fn parses_character_ids_recent_first() {
        let profile = json!({ "Response": { "characters": { "data": {
            "x": { "characterId": "old", "dateLastPlayed": "2026-01-01T00:00:00Z" },
            "y": { "characterId": "new", "dateLastPlayed": "2026-06-19T00:00:00Z" }
        }}}});
        assert_eq!(parse_character_ids(&profile), vec!["new", "old"]);
    }
}
