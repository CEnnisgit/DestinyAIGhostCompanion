# External Lore Import

Drop `*.jsonl` files here to teach the Ghost lore beyond the live game — Destiny 1
Grimoire, lore-book transcripts, Ishtar Collective exports, fan compilations.
On startup the backend imports every entry; full-text search works immediately,
and embeddings are filled in on the next manifest sync.

## Format

One JSON object per line (JSONL):

```jsonl
{"name": "The Books of Sorrow: I - The First Knife", "description": "Before they were the Hive, they were the Krill...", "category": "Lore Book"}
{"name": "Ghost Fragment: The Traveler", "description": "...", "category": "Grimoire (D1)"}
```

- `name` (required) — the entry title.
- `description` (required) — the lore text.
- `category` (optional) — defaults to `Imported`; used by the Codex.

Re-importing the same `name` updates the entry (keyed by a stable hash), so you
can refine datasets safely.

## Getting "all of Destiny history"

1. **Official in-game lore (the bulk of D2):** set a real `BUNGIE_API_KEY` and
   `GHOST_MANIFEST_SYNC=1`. The backend downloads the Bungie Manifest and ingests
   every `DestinyLoreDefinition` (lore books, Grimoire, the Books of Sorrow,
   Unveiling, …) plus item flavor text — thousands of entries.
2. **Destiny 1 Grimoire + transcripts:** these live outside the D2 manifest. Drop
   a community dataset here as JSONL. The [Ishtar Collective](https://www.ishtar-collective.net/)
   is the comprehensive community archive; convert an export to the format above.

Set `GHOST_LORE_IMPORT_DIR` to point elsewhere if you keep datasets outside the repo.
