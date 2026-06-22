-- Deepen lore: categorize entries and add a full-text search index so the Ghost
-- can find the right lore by natural-language query (not just embeddings).
ALTER TABLE destiny_lore ADD COLUMN IF NOT EXISTS category TEXT;

CREATE INDEX IF NOT EXISTS idx_destiny_lore_fts ON destiny_lore
    USING GIN (to_tsvector('english', name || ' ' || COALESCE(description, '')));
