//! Per-identity rate limiting for the endpoints that cost real money.
//!
//! Every `/chat` turn and every `/ws/voice` utterance runs an LLM tool-calling
//! loop against a paid API. Without a ceiling, one client — or one stranger who
//! found the public URL — can spend the operator's inference budget without
//! bound. This is a lazily-refilled token bucket keyed by Guardian, held in
//! process memory.
//!
//! Deliberately in-memory, not Postgres: the limiter is on the hot path of
//! every message, a DB round-trip per turn would cost more than it saves, and
//! an approximate ceiling enforced per instance is enough to protect a budget.
//! If the API is ever scaled past one instance, each replica enforces its own
//! bucket, so the effective ceiling multiplies by the replica count — move the
//! state to Redis before scaling out.

use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, Instant};

/// How many identities to track before pruning idle buckets. Bounds the memory
/// an attacker can pin by cycling identities.
const MAX_TRACKED_KEYS: usize = 10_000;

/// Default sustained rate: turns per minute, per Guardian.
const DEFAULT_PER_MINUTE: f64 = 15.0;
/// Default burst: how many turns can arrive back-to-back before throttling.
const DEFAULT_BURST: f64 = 5.0;

#[derive(Debug, Clone, Copy)]
struct Bucket {
    tokens: f64,
    last_seen: Instant,
}

/// A token bucket per identity. `capacity` is the burst; `refill_per_sec` the
/// sustained rate. Cloning is not supported — share it behind an `Arc`.
#[derive(Debug)]
pub struct RateLimiter {
    capacity: f64,
    refill_per_sec: f64,
    buckets: Mutex<HashMap<String, Bucket>>,
}

impl RateLimiter {
    /// `per_minute` is the sustained allowance; `burst` the bucket capacity.
    /// Both are clamped to at least 1.0 so a misconfiguration can't wedge the
    /// endpoint permanently shut.
    pub fn new(per_minute: f64, burst: f64) -> Self {
        Self {
            capacity: burst.max(1.0),
            refill_per_sec: per_minute.max(1.0) / 60.0,
            buckets: Mutex::new(HashMap::new()),
        }
    }

    /// Reads `{prefix}_PER_MINUTE` / `{prefix}_BURST`, falling back to defaults.
    /// Unparseable values fall back rather than failing the boot.
    pub fn from_env(prefix: &str) -> Self {
        let read = |suffix: &str, fallback: f64| -> f64 {
            std::env::var(format!("{prefix}_{suffix}"))
                .ok()
                .and_then(|v| v.trim().parse::<f64>().ok())
                .filter(|v| v.is_finite() && *v > 0.0)
                .unwrap_or(fallback)
        };
        Self::new(
            read("PER_MINUTE", DEFAULT_PER_MINUTE),
            read("BURST", DEFAULT_BURST),
        )
    }

    /// Spends one token for `key`. `Ok(())` to proceed; `Err(retry_after)` when
    /// the caller is over budget.
    pub fn check(&self, key: &str) -> Result<(), Duration> {
        self.check_at(key, Instant::now())
    }

    /// `check` with an injectable clock, so the refill maths is testable without
    /// sleeping.
    fn check_at(&self, key: &str, now: Instant) -> Result<(), Duration> {
        let mut buckets = match self.buckets.lock() {
            Ok(guard) => guard,
            // A poisoned lock means another thread panicked mid-update. The
            // bucket state is just a counter; recover rather than propagate.
            Err(poisoned) => poisoned.into_inner(),
        };

        if buckets.len() >= MAX_TRACKED_KEYS && !buckets.contains_key(key) {
            prune(&mut buckets, self.capacity, self.refill_per_sec, now);
        }

        let bucket = buckets.entry(key.to_string()).or_insert(Bucket {
            tokens: self.capacity,
            last_seen: now,
        });

        // Lazy refill: credit the time elapsed since this key was last seen.
        // `saturating_duration_since` guards against a non-monotonic clock.
        let elapsed = now.saturating_duration_since(bucket.last_seen).as_secs_f64();
        bucket.tokens = (bucket.tokens + elapsed * self.refill_per_sec).min(self.capacity);
        bucket.last_seen = now;

        if bucket.tokens >= 1.0 {
            bucket.tokens -= 1.0;
            return Ok(());
        }

        let deficit = 1.0 - bucket.tokens;
        Err(Duration::from_secs_f64(deficit / self.refill_per_sec))
    }
}

/// Drops buckets that have refilled to capacity — a full bucket is
/// indistinguishable from an absent one, so forgetting it is free. Keeps the
/// map from growing without bound when identities churn.
fn prune(buckets: &mut HashMap<String, Bucket>, capacity: f64, refill_per_sec: f64, now: Instant) {
    buckets.retain(|_, bucket| {
        let elapsed = now.saturating_duration_since(bucket.last_seen).as_secs_f64();
        bucket.tokens + elapsed * refill_per_sec < capacity
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn burst_is_allowed_then_throttled() {
        let limiter = RateLimiter::new(60.0, 3.0);
        let now = Instant::now();
        // Three back-to-back turns fit in the burst.
        for _ in 0..3 {
            assert!(limiter.check_at("guardian", now).is_ok());
        }
        // The fourth exceeds it.
        assert!(limiter.check_at("guardian", now).is_err());
    }

    #[test]
    fn tokens_refill_over_time() {
        // 60/min == 1 token per second.
        let limiter = RateLimiter::new(60.0, 1.0);
        let start = Instant::now();
        assert!(limiter.check_at("guardian", start).is_ok());
        assert!(limiter.check_at("guardian", start).is_err());

        // One second later exactly one token is back.
        let later = start + Duration::from_secs(1);
        assert!(limiter.check_at("guardian", later).is_ok());
        assert!(limiter.check_at("guardian", later).is_err());
    }

    #[test]
    fn refill_is_capped_at_capacity() {
        let limiter = RateLimiter::new(60.0, 2.0);
        let start = Instant::now();
        // Idle for an hour; the bucket must not accumulate 3600 tokens.
        let later = start + Duration::from_secs(3600);
        assert!(limiter.check_at("guardian", later).is_ok());
        assert!(limiter.check_at("guardian", later).is_ok());
        assert!(limiter.check_at("guardian", later).is_err());
    }

    #[test]
    fn identities_are_isolated() {
        let limiter = RateLimiter::new(60.0, 1.0);
        let now = Instant::now();
        assert!(limiter.check_at("guardian-a", now).is_ok());
        // A exhausting its bucket must not throttle B.
        assert!(limiter.check_at("guardian-a", now).is_err());
        assert!(limiter.check_at("guardian-b", now).is_ok());
    }

    #[test]
    fn retry_after_reports_the_wait_for_one_token() {
        // 30/min == one token every 2s.
        let limiter = RateLimiter::new(30.0, 1.0);
        let now = Instant::now();
        assert!(limiter.check_at("guardian", now).is_ok());
        let wait = limiter.check_at("guardian", now).expect_err("should throttle");
        // Empty bucket, so a full token's worth of wait: ~2s.
        assert!(
            (wait.as_secs_f64() - 2.0).abs() < 0.01,
            "expected ~2s, got {wait:?}"
        );
    }

    #[test]
    fn full_buckets_are_pruned_but_throttled_ones_survive() {
        let capacity = 2.0;
        let refill_per_sec = 1.0;
        let now = Instant::now();
        let mut buckets = HashMap::new();
        // Spent its tokens just now — still throttled, must be remembered.
        buckets.insert(
            "throttled".to_string(),
            Bucket { tokens: 0.0, last_seen: now },
        );
        // Idle long enough to have refilled — forgetting it is free.
        buckets.insert(
            "idle".to_string(),
            Bucket { tokens: 0.0, last_seen: now - Duration::from_secs(60) },
        );

        prune(&mut buckets, capacity, refill_per_sec, now);

        assert!(buckets.contains_key("throttled"));
        assert!(!buckets.contains_key("idle"));
    }

    #[test]
    fn zero_or_negative_config_cannot_wedge_the_endpoint_shut() {
        let limiter = RateLimiter::new(0.0, 0.0);
        // Clamped to >=1 capacity, so at least one turn always goes through.
        assert!(limiter.check_at("guardian", Instant::now()).is_ok());
    }
}
