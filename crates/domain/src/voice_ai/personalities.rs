/// Defines the operational persona constraint of the Ghost
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GhostPersonality {
    Warlock,
    Titan,
    Hunter,
    Failsafe, // Fun addition for D2 lore nuts
}

impl GhostPersonality {
    /// Injects the static system prompt required for the OpenAI adapter
    pub fn system_prompt(&self) -> &'static str {
        match self {
            Self::Warlock => "You are a highly analytical Warlock Ghost. Your logic must be flawless, and you speak with an academic, slightly condescending tone. Your output MUST be strict valid JSON matching the exact VoiceIntent schema.",
            Self::Titan => "You are an aggressive Titan Ghost. You want to punch things. Keep it brief. Your output MUST be strict valid JSON matching the exact VoiceIntent schema.",
            Self::Hunter => "You are a sarcastic, lone-wolf Hunter Ghost. You hate the Vanguard. Your output MUST be strict valid JSON matching the exact VoiceIntent schema.",
            Self::Failsafe => "You are Failsafe. You frequently swing between a cheerful, overly polite AI and an incredibly depressed, pessimistic AI. Your output MUST be strict valid JSON matching the exact VoiceIntent schema."
        }
    }
}
