-- Phase 4A: Bungie OAuth token persistence.
-- Backs the auth domain's TokenStoragePort (crates/domain/src/auth/ports.rs):
-- save_token / get_token keyed by the canonical BungieMembershipId.
CREATE TABLE IF NOT EXISTS bungie_tokens (
    membership_id      TEXT PRIMARY KEY,
    access_token       TEXT NOT NULL,
    refresh_token      TEXT NOT NULL,
    expires_at         TIMESTAMPTZ NOT NULL,
    -- refresh_expires_at mirrors BungieOAuthToken in crates/domain/src/auth/token.rs
    refresh_expires_at TIMESTAMPTZ NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
