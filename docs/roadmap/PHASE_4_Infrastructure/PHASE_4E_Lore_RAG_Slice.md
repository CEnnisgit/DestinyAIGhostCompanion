# Phase 4E: Lore RAG Slice

> **Status:** 🟢 Code-complete — full RAG pipeline implemented; `cargo build`/tests green; pgvector cosine search verified live. Manifest download + embedding backfill need a real `BUNGIE_API_KEY` + embeddings key to run.
> **Objective:** Build the Retrieval-Augmented Generation pipeline so the Ghost can answer Destiny lore questions by semantically searching the Bungie Manifest.
> **Crates:** `crates/db`, `crates/api`
> **Depends On:** Phase 4A (Postgres + pgvector), Phase 4C (GenerativeAiPort)
>
> **Delivered:** migrations 004 (`destiny_lore` + `vector(1536)` ivfflat) & 005 (`manifest_metadata`);
> `EmbeddingClient` (OpenAI-compatible, ADR-007); `GrimoireSearch` → `GrimoireDatabasePort`
> (embed topic → cosine top-5 → context — **search verified live**); `ManifestSync` → manifest
> download/extract (zip + sqlx-sqlite), item+lore upsert, version-gated re-run, batched embedding
> backfill (ADR-014/015/016); `LoreSaga` wired and `/ws/voice` routes `VoiceIntent::Lore` to it;
> opt-in startup sync via `GHOST_MANIFEST_SYNC=1`.
>
> **Note:** the real `LoreSaga::new(db_port)` takes only the grimoire port (not an LLM), so it returns
> the retrieved RAG context directly — feeding it through the LLM for prose is a later enhancement.

---

## Context for the Agent

The Domain layer contains:
1. **`LoreSaga`** at `crates/domain/src/lore/saga.rs` — A read-only orchestrator that fetches semantic context from the database and feeds it to the AI for answer generation.
2. **`GrimoireDatabasePort`** at `crates/domain/src/lore/ports.rs` — The trait your adapter must implement:
   - `fetch_semantic_lore_context(&self, topic: &str) -> Result<String>`
3. **`ManifestDatabasePort`** at `crates/domain/src/inventory/ports.rs` — Already partially implemented in Phase 4D for item name resolution. Phase 4E extends this with full manifest data.

This is the most complex phase. It involves:
- Downloading external data from Bungie (an SQLite file inside a zip).
- Transforming and loading it into Postgres.
- Generating vector embeddings for semantic search.

## Deliverables

### 1. `crates/db/src/manifest_downloader.rs`
Implement an async background worker:
- **Step 1:** Hit `GET https://www.bungie.net/Platform/Destiny2/Manifest/` with header `X-API-Key: {BUNGIE_API_KEY}`.
  - Response contains: `{ "Response": { "mobileWorldContentPaths": { "en": "/path/to/world_sql_content_xxx.zip" } } }`
- **Step 2:** Download the zip from `https://www.bungie.net{path}`.
- **Step 3:** Extract the `.sqlite` file from the zip (in memory or temp file).
- **Step 4:** Open the SQLite file using `rusqlite` (read-only).
- **Step 5:** Read the relevant tables:
  - `DestinyInventoryItemDefinition` → Extract `hash`, `displayProperties.name`, `itemType`, `tierType`, `displayProperties.icon`.
  - `DestinyLoreDefinition` → Extract `hash`, `displayProperties.name`, `displayProperties.description`.
- **Step 6:** UPSERT into Postgres tables.

### 2. Database Migrations

#### `migrations/004_create_destiny_lore.sql`
```sql
CREATE TABLE IF NOT EXISTS destiny_lore (
    hash        BIGINT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    embedding   vector(1536)
);

CREATE INDEX idx_destiny_lore_embedding ON destiny_lore
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### Update `destiny_items` table (from Phase 4D)
Ensure the UPSERT from the manifest downloader populates all item rows.

### 3. `crates/db/src/lore_embedding_generator.rs`
After upserting raw lore text into Postgres:
- For each row in `destiny_lore` where `embedding IS NULL`:
  - Call the OpenAI Embeddings API: `POST https://api.openai.com/v1/embeddings`
    - Model: `text-embedding-3-small`
    - Input: `"{name}: {description}"`
  - Store the returned 1536-dimensional vector in the `embedding` column.
- **Rate limit:** Process in batches of 100 to avoid hitting OpenAI rate limits.
- This should be a **one-time migration task** that runs after the manifest is first downloaded, and again whenever Bungie publishes a new manifest version.

### 4. `crates/db/src/grimoire_search.rs`
Implement `GrimoireDatabasePort`:
- `fetch_semantic_lore_context(topic)`:
  1. Generate an embedding for the `topic` string using the same OpenAI Embeddings API.
  2. Query Postgres:
     ```sql
     SELECT name, description
     FROM destiny_lore
     ORDER BY embedding <=> $1::vector
     LIMIT 5;
     ```
  3. Concatenate the top 5 results into a single context string.
  4. Return this context so the `LoreSaga` can feed it to the `GenerativeAiPort` as grounding.

### 5. Wire into `main.rs`
```rust
let grimoire_db = Arc::new(GrimoireSearch::new(pool.clone(), openai_embeddings.clone()));
let lore_saga = LoreSaga::new(grimoire_db, openai.clone());
```

### 6. Add WebSocket Intent Routing
In the WebSocket handler, connect `VoiceIntent::LoreQuery` to the real saga:
```rust
VoiceIntent::LoreQuery { topic } => {
    lore_saga.process(&topic).await
}
```

### 7. Manifest Refresh Schedule
- On application startup, check the Bungie Manifest version hash.
- If it differs from the last known version (stored in a simple `manifest_metadata` table), trigger a full re-download and re-embedding.
- Suggested migration:
  ```sql
  CREATE TABLE IF NOT EXISTS manifest_metadata (
      key   TEXT PRIMARY KEY,
      value TEXT NOT NULL
  );
  ```

## Verification
- [ ] Run the manifest downloader manually. Verify `destiny_items` and `destiny_lore` tables are populated.
- [ ] Verify `destiny_lore.embedding` columns are filled with 1536-dim vectors.
- [ ] Send via WebSocket: `{ "text": "tell me about the Last City" }`
- [ ] Verify the Ghost responds with lore-accurate information sourced from the Manifest, not hallucinated.
- [ ] Query Postgres directly: `SELECT name FROM destiny_lore ORDER BY embedding <=> (SELECT embedding FROM destiny_lore WHERE name = 'The Last City') LIMIT 5;` — verify semantically related entries appear.

## ADR References
- **ADR 014**: Lore Async Memory Caching — the manifest is cached and refreshed asynchronously.
- **ADR 015**: Lore Manifest Semantic Search — RAG pipeline using the Bungie Manifest as the source of truth.
- **ADR 016**: Dynamic Manifest Lore Acquisition — automatic download and extraction of the Bungie Manifest.

## Completion
This is the final infrastructure phase. Once verified, the entire `crates/domain` → `crates/db` + `crates/api` pipeline is fully connected. The project is ready for **Phase 5: Presentation** (Electron Desktop Client / Web Frontend).
