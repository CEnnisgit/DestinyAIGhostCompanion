//! An authenticated session: proof that a request belongs to a specific
//! Guardian. Minted after a successful Bungie OAuth login and presented on
//! subsequent requests so the server can trust *who* is calling without
//! re-running OAuth — and so a user can only ever reach their own data.

use chrono::{DateTime, Utc};

use super::membership::BungieMembershipId;

/// A verified session. The `membership_id` is the authenticated owner; the
/// server derives data access from this, never from a client-supplied claim.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Session {
    pub membership_id: BungieMembershipId,
    /// When the session was minted — used for revocation: a sign-out marks all
    /// sessions issued before that moment as invalid.
    pub issued_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
}

impl Session {
    pub fn new(
        membership_id: BungieMembershipId,
        issued_at: DateTime<Utc>,
        expires_at: DateTime<Utc>,
    ) -> Self {
        Self {
            membership_id,
            issued_at,
            expires_at,
        }
    }

    /// True once the session has passed its expiry.
    pub fn is_expired(&self, now: DateTime<Utc>) -> bool {
        now >= self.expires_at
    }

    /// True when the session was issued before a revocation cutoff (e.g. set by a
    /// sign-out), and is therefore no longer valid.
    pub fn is_revoked(&self, revoked_before: Option<DateTime<Utc>>) -> bool {
        matches!(revoked_before, Some(cutoff) if self.issued_at < cutoff)
    }
}
