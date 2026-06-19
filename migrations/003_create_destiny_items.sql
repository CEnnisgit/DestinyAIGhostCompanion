-- Phase 4D: minimal Destiny item lookup table for name -> hash resolution.
-- Fully populated by the Phase 4E manifest ETL; for now it backs basic
-- ILIKE fuzzy matching in ManifestItemResolver (ManifestDatabasePort).
CREATE TABLE IF NOT EXISTS destiny_items (
    hash          BIGINT PRIMARY KEY,
    name          TEXT NOT NULL,
    item_type     TEXT,
    tier_type     TEXT,
    icon_path     TEXT
);

CREATE INDEX IF NOT EXISTS idx_destiny_items_name
    ON destiny_items USING GIN (to_tsvector('english', name));
