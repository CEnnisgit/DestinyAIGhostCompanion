use serde::{Deserialize, Serialize};

/// Strongly typed NLP commands generated exclusively by the GenerativeAiPort
/// By using an Internally Tagged Enum, `serde` will strictly validate the JSON payload.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "action")] // e.g., { "action": "Equip", "item_name": "Sunshot", "character_class": "Warlock" }
pub enum VoiceIntent {
    Equip { 
        item_name: String, 
        character_class: Option<String> 
    },
    Transfer { 
        item_name: String, 
        to_vault: bool 
    },
    
    // As mandated by the Domain Expert: Core Inventory features required for MVP rules
    PullPostmaster { 
        character_class: Option<String> 
    },
    QueryInventory { 
        slot: Option<String>, 
        character_class: Option<String> 
    },
    
    Lore { 
        topic: String 
    },
    
    // Fallback block if the LLM cannot figure it out
    Unknown { 
        reason_for_confusion: String 
    },
}
