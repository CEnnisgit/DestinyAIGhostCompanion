# Destiny Ghost Test Strategy

> **Version:** 2.0.0
> **Last Updated:** 2026-04-20
> **Status:** Active — updated as each Phase milestone adds new testing layers

---

## The One Rule That Answers Every Testing Question

**Each test proves that one layer fulfills its contract. Nothing more.**

A domain test proves domain logic works. A DB test proves SQLite queries are correct. An API test proves the HTTP interface is correct. When you catch yourself writing a test that crosses two layers, you're doing the adjacent layer's job — stop.

---

## Part 1: What Each Layer's Tests Prove

### `crates/domain` — "Does my business logic work?"

**Test type:** Unit tests. Pure functions, no I/O, no database, no HTTP.

**What to test:**
- Saga orchestration produces correct state (`EquipItemSaga` transitions through steps)
- Port trait contracts are fulfilled by mock implementations
- Intent parsing handles all `VoiceIntent` variants correctly
- Error yielding returns contextual messages (ADR 011), not panics

**What NOT to test:**
- ❌ Serialization (that's Serde's job)
- ❌ That `Uuid::new_v4()` generates unique IDs
- ❌ That `async_trait` dispatches correctly

---

### `crates/db` — "Does my SQLite work?"

**Test type:** Integration tests. Require a real SQLite database.

**What to test:**
- Token `save()` → `find_by_membership()` round-trips correctly
- Manifest item lookup returns the correct `DestinyItemHash` for a fuzzy query
- Lore RAG retrieval returns semantically relevant passages
- NULL handling is correct (optional fields save as NULL, come back as `None`)

**What NOT to test:**
- ❌ Domain validation (that's `crates/domain`'s job — the DB test assumes it received a valid domain object)
- ❌ That `sqlx` works (SQLx is a well-tested library)
- ❌ Every possible query combination (focus on the ones your app actually calls)

---

### `crates/api` — "Does the HTTP interface work?"

**Test type:** Handler tests (in-process, no real HTTP server) OR lightweight integration.

**What to test:**
- Routes exist and match expected HTTP methods
- Bungie OAuth callback correctly exchanges authorization codes
- WebSocket voice command pipeline correctly parses and dispatches intents
- Status codes: 200 for success, 401 for expired tokens, 400 for bad input

**What NOT to test:**
- ❌ Domain logic (if the domain already tests `EquipItemSaga`, don't re-test it through the API)
- ❌ SQL correctness (that's the DB layer's job)
- ❌ That Axum routes requests to handlers (that's Axum's job)

---

## Part 2: End-to-End Tests

Exercises the full stack: WebSocket → API → Domain → DB → Bungie → response.

**When valuable:**
- Multi-step workflows where order matters (equip cross-character item)
- Cross-module operations (voice command → intent parse → inventory action)
- Scenarios where composition root wiring matters

**When NOT valuable:**
- Simple CRUD (if `save()` and `find_by_id()` work individually, they work together)
- Validating individual fields (that's a unit test)

**Destiny Ghost needs 2-3 E2E tests total**, covering equip lifecycle and lore retrieval.

---

## Part 3: What's NOT Worth Testing

| Don't Test | Why |
|-----------|-----|
| `From<Row>` impls in isolation | Tested implicitly by save+find roundtrip |
| `#[derive(Serialize)]` output | Serde is well-tested. If the derive compiles, it works |
| That `Router::new().route(...)` registers a route | That's Axum's job |
| That `SqlitePool` connects to a database | That's SQLx's job |
| Individual SQL clauses | Test the full adapter method, not fragments |
| "What if SQLite is corrupted?" | `anyhow::Error` handles this already |

---

## Part 4: Implementation Phasing

Tests are implemented alongside their relevant Phase milestone:

| Phase | Tests Added | Why Now |
|-------|-------------|---------|
| **Phase 3 (Domain)** | Domain unit tests (baseline) | Pure logic must be proven before infrastructure |
| **Phase 4 (Infrastructure)** | DB + API tests (~18) | SQLite queries and Bungie HTTP calls need verification |
| **Phase 5 (Presentation)** | E2E workflow tests (~3) | Full stack is complete — test real user flows |

---

## Part 5: Anti-Patterns to Avoid

1. **"Test everything through the API"** — Tests everything, proves nothing specific. When it fails, you don't know which layer broke.
2. **"Mock the database"** — For API tests, fine. For DB tests, never. The whole point is to verify SQL against real SQLite.
3. **"Re-test domain logic in API tests"** — The domain already tests saga error handling. API test should only verify the status code is 400.
4. **"Test every field in the response"** — Assert the shape, not every field. If the derive compiles, Serde serializes correctly.
5. **"Write tests before you have infrastructure"** — Get the adapters wired first, then prove they work.

---

## Part 6: Test Infrastructure

| Concern | Solution |
|---------|----------|
| **Test database** | In-memory SQLite (`:memory:`) for fast ephemeral test DBs |
| **Bungie API mocks** | Mock `BungieInventoryPort` trait with known responses |
| **HTTP test client** | Axum's `TestClient` for handler tests (Phase 4) |
| **CI** | `cargo test --workspace` with no external dependencies required |

---

## References

- [ADR-0010](../adr/0010-strict-serial-inventory-mutations.md) — Serial mutation testing
- [ADR-0011](../adr/0011-inventory-saga-state-rollbacks.md) — Error yielding verification
- [TESTING_MATRIX.md](./TESTING_MATRIX.md) — Per-module coverage tracking
