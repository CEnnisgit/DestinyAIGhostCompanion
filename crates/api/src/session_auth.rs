//! HMAC-signed session tokens — the adapter for the auth domain's
//! `SessionAuthority` port.
//!
//! A token is `base64url(payload) "." base64url(HMAC-SHA256(payload))`, where the
//! payload is `{"sub": <membership_id>, "exp": <unix_seconds>}`. It is stateless
//! (no session table): verification re-computes the MAC in constant time and
//! checks expiry. The signing key comes from `GHOST_SESSION_SECRET`; rotating it
//! invalidates every issued token.

use anyhow::{anyhow, Context};
use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
use chrono::{DateTime, TimeZone, Utc};
use hmac::{Hmac, Mac};
use serde::{Deserialize, Serialize};
use sha2::Sha256;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::SessionAuthority;
use domain::auth::session::Session;

type HmacSha256 = Hmac<Sha256>;

/// Signs and verifies session tokens with a shared secret.
pub struct HmacSessionAuthority {
    secret: Vec<u8>,
}

#[derive(Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: i64,
}

impl HmacSessionAuthority {
    pub fn new(secret: impl Into<Vec<u8>>) -> Self {
        Self {
            secret: secret.into(),
        }
    }

    /// Reads `GHOST_SESSION_SECRET`. Returns `None` when unset/blank so the
    /// composition root can decide whether to generate an ephemeral dev secret.
    pub fn from_env() -> Option<Self> {
        std::env::var("GHOST_SESSION_SECRET")
            .ok()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .map(Self::new)
    }

    fn sign(&self, message: &[u8]) -> Vec<u8> {
        let mut mac = HmacSha256::new_from_slice(&self.secret).expect("HMAC accepts any key length");
        mac.update(message);
        mac.finalize().into_bytes().to_vec()
    }
}

impl SessionAuthority for HmacSessionAuthority {
    fn mint(&self, session: &Session) -> Result<String, anyhow::Error> {
        let claims = Claims {
            sub: session.membership_id.0.clone(),
            exp: session.expires_at.timestamp(),
        };
        let payload = serde_json::to_vec(&claims).context("serializing session claims")?;
        let payload_b64 = URL_SAFE_NO_PAD.encode(&payload);
        let sig_b64 = URL_SAFE_NO_PAD.encode(self.sign(payload_b64.as_bytes()));
        Ok(format!("{payload_b64}.{sig_b64}"))
    }

    fn verify(&self, token: &str) -> Result<Session, anyhow::Error> {
        let (payload_b64, sig_b64) = token
            .split_once('.')
            .ok_or_else(|| anyhow!("malformed session token"))?;

        // Constant-time MAC check via the verifier (don't compare strings).
        let expected_sig = URL_SAFE_NO_PAD
            .decode(sig_b64)
            .context("decoding session signature")?;
        let mut mac =
            HmacSha256::new_from_slice(&self.secret).expect("HMAC accepts any key length");
        mac.update(payload_b64.as_bytes());
        mac.verify_slice(&expected_sig)
            .map_err(|_| anyhow!("invalid session signature"))?;

        let payload = URL_SAFE_NO_PAD
            .decode(payload_b64)
            .context("decoding session payload")?;
        let claims: Claims = serde_json::from_slice(&payload).context("parsing session claims")?;

        let expires_at: DateTime<Utc> = Utc
            .timestamp_opt(claims.exp, 0)
            .single()
            .ok_or_else(|| anyhow!("invalid session expiry"))?;
        let session = Session::new(
            BungieMembershipId::new(claims.sub).map_err(|e| anyhow!(e))?,
            expires_at,
        );
        if session.is_expired(Utc::now()) {
            return Err(anyhow!("session expired"));
        }
        Ok(session)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Duration;

    fn member() -> BungieMembershipId {
        BungieMembershipId::new("4611686018467260000").unwrap()
    }

    #[test]
    fn round_trips_a_valid_session() {
        let authority = HmacSessionAuthority::new(b"test-secret".to_vec());
        let session = Session::new(member(), Utc::now() + Duration::days(30));
        let token = authority.mint(&session).unwrap();
        let verified = authority.verify(&token).unwrap();
        assert_eq!(verified.membership_id, session.membership_id);
    }

    #[test]
    fn rejects_a_tampered_payload() {
        let authority = HmacSessionAuthority::new(b"test-secret".to_vec());
        let session = Session::new(member(), Utc::now() + Duration::days(30));
        let token = authority.mint(&session).unwrap();

        // Forge a different membership in the payload, keep the old signature.
        let forged_claims = Claims { sub: "hacker".into(), exp: (Utc::now() + Duration::days(30)).timestamp() };
        let forged_payload = URL_SAFE_NO_PAD.encode(serde_json::to_vec(&forged_claims).unwrap());
        let sig = token.split_once('.').unwrap().1;
        let forged = format!("{forged_payload}.{sig}");
        assert!(authority.verify(&forged).is_err());
    }

    #[test]
    fn rejects_a_wrong_secret() {
        let signer = HmacSessionAuthority::new(b"secret-a".to_vec());
        let attacker = HmacSessionAuthority::new(b"secret-b".to_vec());
        let token = signer
            .mint(&Session::new(member(), Utc::now() + Duration::days(1)))
            .unwrap();
        assert!(attacker.verify(&token).is_err());
    }

    #[test]
    fn rejects_an_expired_session() {
        let authority = HmacSessionAuthority::new(b"test-secret".to_vec());
        let token = authority
            .mint(&Session::new(member(), Utc::now() - Duration::seconds(1)))
            .unwrap();
        assert!(authority.verify(&token).is_err());
    }
}
