# Saga Root: LoreSaga

**Module Path:** `crates/domain/src/lore/saga.rs`

## Description
A perfectly isolated read-only orchestrator. It receives a query (e.g. from `VoiceIntent::Lore`), retrieves the semantic Grimoire data through the DB port, and returns it dynamically to the UI driver.
