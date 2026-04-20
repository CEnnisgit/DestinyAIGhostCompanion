# Hexagonal Ports

**Module Path:** `crates/domain/src/lore/ports.rs`

## 1. GrimoireDatabasePort (Secondary/Driven)
As defined in **ADR 015**, this trait dictates that the implementing database adapter MUST execute semantic searching (RAG) rather than simplistic string overlaps.
