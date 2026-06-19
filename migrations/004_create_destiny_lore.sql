-- Phase 4E: lore entries with semantic embeddings for RAG search.
-- embedding is a 1536-dim vector (OpenAI text-embedding-3-small); nullable until
-- the embedding backfill runs. Cosine distance (<=>) drives the similarity search.
CREATE TABLE IF NOT EXISTS destiny_lore (
    hash        BIGINT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    embedding   vector(1536)
);

CREATE INDEX IF NOT EXISTS idx_destiny_lore_embedding ON destiny_lore
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
