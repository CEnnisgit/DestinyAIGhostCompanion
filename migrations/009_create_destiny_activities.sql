-- Local mirror of the manifest's DestinyActivityDefinition, so the Ghost can
-- resolve an activity hash (e.g. from a player's history) to its name offline,
-- with no per-hash API call and no rate limit. Populated by ManifestSync from
-- the manifest SQLite we already download.
CREATE TABLE IF NOT EXISTS destiny_activities (
    hash        BIGINT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    icon_path   TEXT
);
