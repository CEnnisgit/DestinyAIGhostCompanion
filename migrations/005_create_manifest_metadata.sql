-- Phase 4E: tracks the last-loaded Bungie manifest version so startup can detect
-- a new manifest and trigger a re-download + re-embed (ADR-014/016).
CREATE TABLE IF NOT EXISTS manifest_metadata (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
