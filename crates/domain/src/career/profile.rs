/// A distilled summary of a Guardian's career, built from Bungie career stats.
/// `dossier()` renders it into a short, natural-language line the Ghost can speak.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct GuardianProfile {
    pub total_hours: u32,
    pub crucible_kd: f32,
    pub triumph_score: u32,
    pub character_count: u32,
    pub classes: Vec<String>,
    /// Class of the most recently played character.
    pub favorite_class: Option<String>,
}

impl GuardianProfile {
    /// A short, personalized line. Skips fields we don't have data for.
    pub fn dossier(&self) -> String {
        let mut parts: Vec<String> = Vec::new();

        match (self.total_hours, self.character_count) {
            (h, c) if h > 0 && c > 0 => parts.push(format!(
                "you've logged {h} hours across {c} {}",
                if c == 1 { "Guardian" } else { "Guardians" }
            )),
            (h, _) if h > 0 => parts.push(format!("you've logged {h} hours")),
            _ => {}
        }

        if let Some(class) = &self.favorite_class {
            parts.push(format!("most recently as a {class}"));
        }

        if self.crucible_kd > 0.0 {
            parts.push(format!("a Crucible K/D of {:.2}", self.crucible_kd));
        }

        if self.triumph_score > 0 {
            parts.push(format!("{} Triumph score", self.triumph_score));
        }

        if parts.is_empty() {
            return "Welcome back, Guardian. Your light is ready.".to_string();
        }

        format!("Welcome back, Guardian — {}.", join_human(&parts))
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

    #[test]
    fn dossier_uses_available_fields() {
        let profile = GuardianProfile {
            total_hours: 1240,
            crucible_kd: 1.34,
            triumph_score: 145_000,
            character_count: 3,
            classes: vec!["Hunter".into(), "Warlock".into(), "Titan".into()],
            favorite_class: Some("Hunter".into()),
        };
        let dossier = profile.dossier();
        assert!(dossier.contains("1240 hours across 3 Guardians"));
        assert!(dossier.contains("most recently as a Hunter"));
        assert!(dossier.contains("1.34"));
        assert!(dossier.contains("145000 Triumph"));
    }

    #[test]
    fn dossier_handles_empty_profile() {
        assert_eq!(
            GuardianProfile::default().dossier(),
            "Welcome back, Guardian. Your light is ready."
        );
    }

    #[test]
    fn dossier_singular_guardian() {
        let profile = GuardianProfile { total_hours: 50, character_count: 1, ..Default::default() };
        assert!(profile.dossier().contains("50 hours across 1 Guardian"));
    }
}
