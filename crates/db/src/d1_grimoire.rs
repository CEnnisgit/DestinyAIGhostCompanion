//! Ingests the entire Destiny 1 Grimoire — the game's original lore system,
//! retired from D2 — straight from Bungie's official D1 API. Together with the
//! D2 manifest (`ManifestSync`) and the JSONL importer, this gives the Ghost the
//! full sweep of Destiny's recorded lore.

use anyhow::{anyhow, Context};
use serde_json::Value;
use sqlx::PgPool;

const GRIMOIRE_URL: &str = "https://www.bungie.net/d1/Platform/Destiny/Vanguard/Grimoire/Definition/";
/// Reserved hash range for D1 Grimoire cards (keyed by cardId).
const GRIMOIRE_HASH_BASE: i64 = 7_000_000_000;

struct GrimoireCard {
    id: i64,
    name: String,
    category: String,
    description: String,
}

/// Downloads the D1 Grimoire Definition and upserts every card into the lore
/// corpus. Returns the number of cards ingested. Requires a real Bungie API key.
pub async fn fetch_d1_grimoire(
    pool: &PgPool,
    http: &reqwest::Client,
    api_key: &str,
) -> Result<u64, anyhow::Error> {
    let body: Value = http
        .get(GRIMOIRE_URL)
        .header("X-API-Key", api_key)
        .send()
        .await
        .context("fetching D1 Grimoire definition")?
        .error_for_status()?
        .json()
        .await
        .context("decoding D1 Grimoire definition")?;

    if body.get("ErrorCode").and_then(Value::as_i64) == Some(1) {
        // ok
    } else if body.get("ErrorCode").is_some() {
        return Err(anyhow!(
            "Bungie D1 Grimoire error: {}",
            body.get("Message").and_then(Value::as_str).unwrap_or("unknown")
        ));
    }

    let cards = parse_grimoire(&body);
    let mut count = 0u64;
    for card in &cards {
        sqlx::query(
            "INSERT INTO destiny_lore (hash, name, description, category) VALUES ($1, $2, $3, $4)
             ON CONFLICT (hash) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                category = EXCLUDED.category,
                embedding = CASE WHEN destiny_lore.description <> EXCLUDED.description
                                 THEN NULL ELSE destiny_lore.embedding END",
        )
        .bind(GRIMOIRE_HASH_BASE + card.id)
        .bind(&card.name)
        .bind(&card.description)
        .bind(&card.category)
        .execute(pool)
        .await?;
        count += 1;
    }
    Ok(count)
}

/// Walks `Response.themeCollection[].pageCollection[].cardCollection[]` and flattens
/// every card into a lore entry (intro + description, HTML stripped).
fn parse_grimoire(body: &Value) -> Vec<GrimoireCard> {
    let mut out = Vec::new();
    let Some(themes) = body.pointer("/Response/themeCollection").and_then(Value::as_array) else {
        return out;
    };

    for theme in themes {
        let theme_name = theme.get("themeName").and_then(Value::as_str).unwrap_or("Lore");
        let category = format!("Grimoire · {}", theme_name.trim());
        let Some(pages) = theme.get("pageCollection").and_then(Value::as_array) else { continue };
        for page in pages {
            let Some(cards) = page.get("cardCollection").and_then(Value::as_array) else { continue };
            for card in cards {
                let Some(id) = card.get("cardId").and_then(Value::as_i64) else { continue };
                let name = card.get("cardName").and_then(Value::as_str).unwrap_or("").trim().to_string();
                let intro = card.get("cardIntro").and_then(Value::as_str).unwrap_or("");
                let desc = card.get("cardDescription").and_then(Value::as_str).unwrap_or("");
                let description = strip_html(&[intro, desc].join("\n\n").trim().to_string());
                if name.is_empty() || description.is_empty() {
                    continue;
                }
                out.push(GrimoireCard { id, name, category: category.clone(), description });
            }
        }
    }
    out
}

/// Removes HTML tags and decodes a few common entities.
fn strip_html(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut in_tag = false;
    for c in input.chars() {
        match c {
            '<' => in_tag = true,
            '>' => in_tag = false,
            _ if !in_tag => out.push(c),
            _ => {}
        }
    }
    out.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
        .trim()
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn parses_nested_grimoire_and_strips_html() {
        let body = json!({
            "Response": { "themeCollection": [
                { "themeName": "Enemies", "pageCollection": [
                    { "cardCollection": [
                        { "cardId": 100101, "cardName": "The Darkness",
                          "cardIntro": "Intro line.",
                          "cardDescription": "A <b>great</b> Darkness &amp; its hunger." }
                    ]}
                ]}
            ]}
        });
        let cards = parse_grimoire(&body);
        assert_eq!(cards.len(), 1);
        assert_eq!(cards[0].id, 100101);
        assert_eq!(cards[0].name, "The Darkness");
        assert_eq!(cards[0].category, "Grimoire · Enemies");
        assert!(cards[0].description.contains("A great Darkness & its hunger"));
        assert!(cards[0].description.contains("Intro line."));
    }

    #[test]
    fn skips_cards_without_text() {
        let body = json!({ "Response": { "themeCollection": [
            { "themeName": "X", "pageCollection": [ { "cardCollection": [
                { "cardId": 1, "cardName": "", "cardDescription": "" }
            ]}]}
        ]}});
        assert!(parse_grimoire(&body).is_empty());
    }
}
