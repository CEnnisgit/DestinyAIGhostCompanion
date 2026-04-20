# PCD Test Strategy

> **Version:** 1.0.0
> **Last Updated:** 2026-04-02
> **Status:** Active — updated as each Phase 3 milestone adds new testing layers

---

## The One Rule That Answers Every Testing Question

**Each test proves that one layer fulfills its contract. Nothing more.**

A domain test proves domain logic works. A DB test proves SQL is correct. An API test proves the HTTP interface is correct. When you catch yourself writing a test that crosses two layers, you're doing the adjacent layer's job — stop.

---

## Part 1: What Each Layer's Tests Prove

### `pcd-domain` — "Does my business logic work?"

**Test type:** Unit tests. Pure functions, no I/O, no database, no HTTP.

**What to test:**
- Factory methods produce correct state (`User::new()` → active, has UUID)
- Invariants reject bad input (`Email::new("")` → Err)
- Commands transition state correctly (`job.start()` → InProgress)
- State machines enforce valid transitions (`canceled → start` → Err)
- Value objects normalize input (`Email` lowercases, `DisplayName` trims)

**What NOT to test:**
- ❌ Serialization (that's Serde's job, not yours)
- ❌ That `Uuid::new_v4()` generates unique IDs (that's the UUID crate's job)
- ❌ That `chrono::Utc::now()` returns the current time

---

### `pcd-db` — "Does my SQL work?"

**Test type:** Integration tests. Require a real Postgres database.

**What to test:**
- `save()` → `find_by_id()` round-trips correctly (data survives persistence)
- Column mapping is correct (`UserRow` fields match the actual table columns)
- Query filters work (`find_by_email` returns the right user, not some other user)
- DB constraints enforce invariants (`UNIQUE email` rejects duplicates)
- NULL handling is correct (optional fields save as NULL, come back as `None`)

**What NOT to test:**
- ❌ Domain validation (that's pcd-domain's job — the DB test assumes it received a valid domain object)
- ❌ That SQLx works (SQLx is a well-tested library)
- ❌ Every possible query combination (focus on the ones your app actually calls)

**Why this matters for PCD specifically:**

SQL is hand-written strings. There's no compile-time verification that `$4` maps to the right column. If you accidentally swap `.bind(user.is_active)` and `.bind(user.personal_workspace_id)`, the compiler won't catch it. The only thing that catches it is a DB test that writes a user and reads it back.

---

### `pcd-api` — "Does the HTTP interface work?"

**Test type:** Handler tests (in-process, no real HTTP server) OR lightweight integration.

**What to test:**
- Routes exist and match expected HTTP methods
- Request deserialization: does JSON → struct work correctly?
- Response serialization: does struct → JSON include all fields?
- Status codes: 200 for success, 404 for not found, 400 for bad input, 422 for domain errors
- Error messages: does the user see a useful message or a stack trace?

**What NOT to test:**
- ❌ Domain logic (if you're testing that `deactivate()` fails on an already-deactivated user inside an API test, you're duplicating a domain test)
- ❌ SQL correctness (that's the DB layer's job)
- ❌ That Axum routes requests to handlers (that's Axum's job)

---

## Part 2: End-to-End Tests

Exercises the full stack: HTTP → API → domain → DB → response.

**When valuable:**
- Multi-step workflows where order matters (LL152 lifecycle)
- Cross-entity operations (create job → auto-create LL152 extension)
- Scenarios where composition root wiring matters

**When NOT valuable:**
- Simple CRUD (if `save()` and `find_by_id()` work individually, they work together)
- Validating individual fields (that's a unit test)

**PCD needs 2-3 E2E tests total**, covering LL152 lifecycle and credential attachment.

---

## Part 3: What's NOT Worth Testing

| Don't Test | Why |
|-----------|-----|
| `From<Row>` impls in isolation | Tested implicitly by save+find roundtrip |
| `#[derive(Serialize)]` output | Serde is well-tested. If the derive compiles, it works |
| That `Router::new().route(...)` registers a route | That's Axum's job |
| That `PgPool` connects to a database | That's SQLx's job |
| Individual SQL clauses | Test the full repo method, not fragments |
| "What if Postgres is down?" | `anyhow::Error` handles this already |

---

## Part 4: Implementation Phasing

Tests are implemented alongside their relevant Phase 3 milestone:

| Phase | Tests Added | Why Now |
|-------|-------------|---------|
| **3A (Identity Foundation)** | DB repo tests (~20) | Hand-written SQL needs verification before anything is built on top |
| **3B (Authentication)** | API handler tests (~9) | Auth changes every handler — test after they stabilize |
| **3C (Authorization)** | E2E workflow tests (~3) | Full stack is complete — test real user flows |

---

## Part 5: Anti-Patterns to Avoid

1. **"Test everything through the API"** — Tests everything, proves nothing specific. When it fails, you don't know which layer broke.
2. **"Mock the database"** — For API tests, fine. For DB tests, never. The whole point is to verify SQL against real Postgres.
3. **"Re-test domain logic in API tests"** — The domain already tests `CompanyError::EmptyName`. API test should only verify the status code is 400.
4. **"Test every field in the response"** — Assert the shape, not every field. If the derive compiles, Serde serializes correctly.
5. **"Write tests before you have infrastructure"** — `#[sqlx::test]` gives per-test databases for free. Don't over-engineer.

---

## Part 6: Test Infrastructure

| Concern | Solution |
|---------|----------|
| **Test database** | `#[sqlx::test]` — auto-creates ephemeral Postgres DB per test |
| **Test fixtures** | Shared `fixtures.rs` with FK chain setup (workspace → company → user → membership) |
| **HTTP test client** | Axum's `TestClient` for handler tests (Phase 3B) |
| **CI** | `cargo test -p pcd-db` with Postgres service container |

---

## References

- [ADR-0036](../adr/0036-singular-module-names.md) — Naming conventions
- [TESTING_MATRIX.md](./TESTING_MATRIX.md) — Per-entity coverage tracking
