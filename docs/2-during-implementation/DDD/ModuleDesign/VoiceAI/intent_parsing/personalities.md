# Value Object: GhostPersonality

**Module Path:** `crates/domain/src/voice_ai/personalities.rs`

## Description
This enum replaces the legacy `ghost/personalities.py`. It hardcodes the System Prompts that are injected into the Generative AI Port.

## Invariants
By defining the personalities statically as Rust Enums (e.g. `GhostPersonality::Titan`), we guarantee that standard system constraints (like demanding JSON struct formats) are permanently glued to the persona prompt and cannot accidentally be omitted.
