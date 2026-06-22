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
    pub expires_at: DateTime<Utc>,
}

impl Session {
    pub fn new(membership_id: BungieMembershipId, expires_at: DateTime<Utc>) -> Self {
        Self {
            membership_id,
            expires_at,
        }
    }

    /// True once the session has passed its expiry.
    pub fn is_expired(&self, now: DateTime<Utc>) -> bool {
        now >= self.expires_at
    }
}
