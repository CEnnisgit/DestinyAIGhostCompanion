//! Cross-device chat sync: conversations stored server-side, keyed by the owning
//! Guardian, so they follow the player across web, iOS, and desktop.
pub mod model;
pub mod ports;
pub mod saga;
