-- Phase 4A: enable pgvector for the lore RAG pipeline (Phase 4E).
-- The pgvector/pgvector image ships the extension; this makes it available
-- in the ghost_companion database.
CREATE EXTENSION IF NOT EXISTS vector;
