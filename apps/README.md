# Apps

These are the **runnable applications** of the Ghost Companion project. Each app is a different way to interact with the same shared backend logic that lives in `crates/`.

Think of `crates/` as the engine, and `apps/` as the different cars you can put that engine into.

## Directory

| App | Language | What It Is | Phase |
|:----|:---------|:-----------|:------|
| `server/` | Rust | The **startup wiring** — see below | Phase 4 |
| `desktop/` | TypeScript | Electron `.exe` + Web browser UI | Phase 5 |
| `ios/` | Swift | Native iPhone app | Future |

---

## `server/` — The Composition Root

> ⚠️ **This is NOT a "server" in the traditional sense.** It does not contain any routes, handlers, database queries, or business logic.

This is the **Composition Root** — a tiny Rust binary whose only job is to:

1. Read config from environment variables.
2. Construct the concrete adapters from `crates/db/` and `crates/api/`.
3. Inject them into the domain sagas from `crates/domain/`.
4. Start the `axum` listener.

It's essentially the `fn main()` glue that plugs everything together:

```
crates/domain/  (logic)     ─┐
crates/db/      (database)  ─┼─►  apps/server/  (wires them + starts)
crates/api/     (networking) ─┘
```

All the real code lives in the crates. This app is ~50 lines of setup.

---

## `desktop/` — Electron + Web Client

The user-facing frontend built with Vite + React + TypeScript. Runs as both:
- An **Electron desktop app** (`.exe`) — for gaming alongside Destiny 2.
- A **web app** in the browser — same codebase, no Electron wrapper.

The web and desktop versions share identical code. Two build commands:
- `npm run dev` → web only
- `npm run dev:electron` → desktop window

Connects to the Rust backend via WebSocket at `ws://localhost:8080/ws/voice`.

---

## `ios/` — Native iOS Client

A future Swift/SwiftUI iPhone app connecting to the same Rust backend. The legacy experimental version is archived in `archive/legacy-ios/` for reference.

---

## How They Connect

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ apps/desktop│     │  apps/ios   │     │ (future web │
│  (Electron) │     │   (Swift)   │     │   clients)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │         WebSocket / HTTP              │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │ apps/server │  ← starts the listener
                    │  (Rust bin) │
                    └──────┬──────┘
                           │ wires together:
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        crates/api   crates/domain  crates/db
```
