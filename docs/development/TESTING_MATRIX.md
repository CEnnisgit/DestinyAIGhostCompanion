# Destiny Ghost Testing Matrix

> **Version:** 2.0.0
> **Last Updated:** 2026-04-20
> **Status:** Active — update this document after implementing each testing phase
>
> Tracks test coverage per module across all layers. Update ✅/🔲 markers as tests are added.

---

## Quick Stats

| Layer | Tests | Status |
|-------|------:|--------|
| **domain** | 2 | ✅ Phase 3 baseline |
| **db** | 0 → ~10 target | 🔲 Phase 4 |
| **api** | 0 → ~8 target | 🔲 Phase 4 |
| **E2E** | 0 → ~3 target | 🔲 Phase 5 |

---

## Domain Layer — Unit Tests

| Module | Entity / Saga | Tests | Status |
|--------|--------------|------:|:------:|
| auth | OAuthSessionSaga | 1 | ✅ |
| auth | BungieMembershipId | 1 | ✅ |
| voice_ai | VoiceCommandSaga (failover) | 1 | ✅ |
| voice_ai | VoiceIntent | 0 | 🔲 |
| inventory | EquipItemSaga | 0 | 🔲 |
| lore | LoreSaga | 0 | 🔲 |

---

## DB Layer — Integration Tests (target: ~10)

> **Phase:** 4
> **Infrastructure:** SQLite test databases
> **Location:** `crates/db/tests/`

| Adapter | Roundtrip | Queries | Tests | Status |
|---------|:---------:|:-------:|------:|:------:|
| TokenStorageAdapter | 🔲 save+find | 🔲 find_by_membership | 0/2 | 🔲 |
| ManifestDatabaseAdapter | 🔲 load manifest | 🔲 fuzzy item search | 0/3 | 🔲 |
| GrimoireDatabaseAdapter | 🔲 lore fetch | 🔲 semantic search | 0/2 | 🔲 |

---

## API Layer — Handler Tests (target: ~8)

> **Phase:** 4
> **Infrastructure:** Axum `TestClient`
> **Location:** `crates/api/tests/`

| Route Group | Endpoints | Tests | Status |
|-------------|-----------|------:|:------:|
| Auth | GET /auth/callback, POST /auth/refresh | 0/2 | 🔲 |
| Inventory | POST /inventory/equip, POST /inventory/vault | 0/2 | 🔲 |
| Voice | POST /voice/command (WebSocket) | 0/2 | 🔲 |
| Lore | GET /lore/query | 0/1 | 🔲 |

---

## End-to-End Tests (target: ~3)

> **Phase:** 5
> **Location:** workspace root `tests/e2e/`

| Test | What It Proves | Status |
|------|----------------|:------:|
| Equip happy path | Voice → Intent → Equip → Bungie confirms | 🔲 |
| Lore retrieval | Voice → Intent → RAG → LLM response | 🔲 |
| Auth refresh | Expired token → auto-refresh → retry succeeds | 🔲 |

---

## Risk Assessment

| Module | Domain | DB | API | Overall Risk |
|--------|:------:|:--:|:---:|:------------:|
| Auth | 🟢 | 🔴 | 🔴 | 🟡 Medium |
| VoiceAI | 🟢 | — | 🔴 | 🟡 Medium |
| Inventory | 🟡 | 🔴 | 🔴 | 🔴 High |
| Lore | 🟡 | 🔴 | 🔴 | 🟡 Medium |

**Risk level logic:**
- 🟢 **Low**: Domain tests cover all logic, module is simple
- 🟡 **Medium**: Domain covered but DB/API untested. Simple operations, low chance of bug
- 🔴 **High**: Complex module with multi-step workflows or external API dependencies

---

## Changelog

| Date | Change |
|------|--------|
| 2026-04-20 | Matrix rewritten for Destiny Ghost Companion. Domain baseline: 2 tests. |
