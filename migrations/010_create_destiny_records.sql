-- Local mirror of the manifest's DestinyRecordDefinition (Triumphs/Records), so
-- the Ghost can name a record hash (e.g. from profile component 900) offline,
-- with no per-hash API call. Populated by ManifestSync from the manifest SQLite.
CREATE TABLE IF NOT EXISTS destiny_records (
    hash        BIGINT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT
);
