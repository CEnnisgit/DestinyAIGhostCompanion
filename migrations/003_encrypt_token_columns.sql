-- Phase 4B: Align DB schema with domain BungieOAuthToken struct
-- 1. Add missing refresh_expires_at column
-- 2. Convert token columns to BYTEA for AES-256-GCM ciphertext storage

ALTER TABLE bungie_tokens
ADD COLUMN refresh_expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE bungie_tokens
ALTER COLUMN access_token TYPE BYTEA USING access_token::bytea;

ALTER TABLE bungie_tokens
ALTER COLUMN refresh_token TYPE BYTEA USING refresh_token::bytea;
