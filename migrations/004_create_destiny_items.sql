CREATE TABLE IF NOT EXISTS destiny_items (
    hash          BIGINT PRIMARY KEY,
    name          TEXT NOT NULL,
    item_type     TEXT,
    tier_type     TEXT,
    icon_path     TEXT
);

CREATE INDEX IF NOT EXISTS idx_destiny_items_name ON destiny_items USING GIN (to_tsvector('english', name));
