# Entity-Relationship Diagram: Inventory Bounded Context

## Context
Unlike highly stateful domains, the `Inventory` domain within the Ghost Companion is effectively **Stateless** concerning user data. Bungie natively holds the user's inventory state. However, the system requires a strictly structured, highly-performant local cache to map textual transcriptions to strict Bungie `DestinyItemHash` structures, as dictated by **ADR 012**.

This diagram represents the SQLite Manifest database schema located physically in `crates/db/`.

## Diagram

```mermaid
erDiagram
    %% The Local Manifest Cache (Read-Only)
    DestinyItemCache {
        integer item_hash PK "The absolute DestinyItemHash"
        string display_name "e.g., 'Sunshot'"
        string lowercase_name "e.g., 'sunshot' (Indexed for strsim algorithm)"
        string item_type "e.g., 'Weapon', 'Armor'"
        string icon_path "Bungie CDN URL for frontend display"
    }

    %% Ephemeral Mapping (Not Stored)
    VoiceTranscription "1" --o "1" DestinyItemCache : "fuzzy resolves to"
```

## Security & Scaling Invariants
1. **Destructive Updates:** The `DestinyItemCache` table is violently destroyed and rebuilt whenever Bungie deploys a hotfix or patch. The `crates/db` adapter will physically delete the SQLite file and re-download the JSON-to-SQLite manifest. Therefore, absolutely NO foreign keys from other modules (like `VoiceAI` analytics) can directly enforce constraints against `item_hash` without risking cascading deletion errors during a patch.
2. **Read-Only Lock:** The backend server will open this database cache with strict `PRAGMA query_only = true` to prevent accidental mutation of the immutable Destiny 2 catalog.
