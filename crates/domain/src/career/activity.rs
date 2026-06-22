//! Activity history — what the Guardian has *done*, and with whom.
//!
//! Built from Bungie's `GetActivityHistory` (when + what + completion) and
//! `GetPostGameCarnageReport` (the fireteam roster). Spans Destiny 2 and, via
//! the legacy `/d1/Platform/` endpoints, Destiny 1. The `narrative()` renderer
//! turns it into a short, natural paragraph the Ghost can weave into a reply or
//! greeting, so it always knows what the Guardian has been up to.

use serde::{Deserialize, Serialize};

/// One played activity instance.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ActivityRecord {
    /// Human-readable activity name, e.g. "King's Fall" or "The Whisper".
    pub name: String,
    /// Mode/category, e.g. "Raid", "Strike", "Crucible", "Dungeon".
    pub mode: String,
    /// ISO-8601 UTC timestamp the activity occurred (`period` from Bungie).
    pub period: String,
    /// Whether the Guardian completed the activity.
    pub completed: bool,
    /// Other players in the fireteam (display names), if a PGCR was resolved.
    pub fireteam: Vec<String>,
    /// Which game this came from.
    pub game: Game,
}

/// Distinguishes Destiny 1 from Destiny 2 history.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Game {
    Destiny1,
    Destiny2,
}

impl Game {
    pub fn label(self) -> &'static str {
        match self {
            Game::Destiny1 => "Destiny 1",
            Game::Destiny2 => "Destiny 2",
        }
    }
}

/// A distilled view of the Guardian's recent activity, across both games.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct ActivitySummary {
    /// Most-recent-first list of activities.
    pub recent: Vec<ActivityRecord>,
}

impl ActivitySummary {
    pub fn new(recent: Vec<ActivityRecord>) -> Self {
        Self { recent }
    }

    pub fn is_empty(&self) -> bool {
        self.recent.is_empty()
    }

    /// The most recent raid/dungeon completion, if any — handy for "when did I
    /// last clear a raid, and who with?" questions.
    pub fn last_endgame_clear(&self) -> Option<&ActivityRecord> {
        self.recent
            .iter()
            .find(|r| r.completed && matches!(r.mode.as_str(), "Raid" | "Dungeon"))
    }

    /// A short natural-language paragraph for the Ghost's context. Empty string
    /// when there's nothing to report (caller can then omit it).
    pub fn narrative(&self) -> String {
        if self.recent.is_empty() {
            return String::new();
        }

        let mut lines: Vec<String> = Vec::new();
        for record in self.recent.iter().take(6) {
            let date = record.period.split('T').next().unwrap_or(&record.period);
            let status = if record.completed { "completed" } else { "played" };
            let mut line = format!(
                "{} {} on {} ({})",
                status,
                record.name,
                date,
                record.game.label()
            );
            if !record.fireteam.is_empty() {
                line.push_str(&format!(" with {}", join_human(&record.fireteam)));
            }
            lines.push(line);
        }

        format!("Recent activity — {}.", join_human(&lines))
    }
}

/// Joins phrases as "a, b, and c".
fn join_human(parts: &[String]) -> String {
    match parts.len() {
        0 => String::new(),
        1 => parts[0].clone(),
        2 => format!("{} and {}", parts[0], parts[1]),
        _ => {
            let (last, head) = parts.split_last().unwrap();
            format!("{}, and {}", head.join(", "), last)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn raid(name: &str, date: &str, mates: &[&str]) -> ActivityRecord {
        ActivityRecord {
            name: name.into(),
            mode: "Raid".into(),
            period: date.into(),
            completed: true,
            fireteam: mates.iter().map(|s| s.to_string()).collect(),
            game: Game::Destiny2,
        }
    }

    #[test]
    fn narrative_lists_recent_with_fireteam_and_dates() {
        let summary = ActivitySummary::new(vec![
            raid("King's Fall", "2026-06-18T20:00:00Z", &["Cayde-7", "Saint-14"]),
            raid("Vow of the Disciple", "2026-06-10T19:00:00Z", &[]),
        ]);
        let n = summary.narrative();
        assert!(n.contains("completed King's Fall on 2026-06-18"));
        assert!(n.contains("with Cayde-7 and Saint-14"));
        assert!(n.contains("Vow of the Disciple on 2026-06-10"));
    }

    #[test]
    fn last_endgame_clear_finds_first_completed_raid() {
        let summary = ActivitySummary::new(vec![
            ActivityRecord {
                name: "Trials".into(),
                mode: "Crucible".into(),
                period: "2026-06-19T00:00:00Z".into(),
                completed: false,
                fireteam: vec![],
                game: Game::Destiny2,
            },
            raid("Last Wish", "2026-06-15T00:00:00Z", &["Mara"]),
        ]);
        assert_eq!(summary.last_endgame_clear().unwrap().name, "Last Wish");
    }

    #[test]
    fn empty_summary_has_no_narrative() {
        assert!(ActivitySummary::default().narrative().is_empty());
    }
}
