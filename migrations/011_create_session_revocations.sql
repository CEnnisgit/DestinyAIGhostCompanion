-- Session revocation. Sessions are stateless signed tokens, so we can't delete
-- them; instead we record a per-user cutoff. Any session issued before the
-- cutoff is treated as revoked. Signing out sets the cutoff to NOW().
CREATE TABLE IF NOT EXISTS session_revocations (
    membership_id  TEXT PRIMARY KEY,
    revoked_before TIMESTAMPTZ NOT NULL
);
