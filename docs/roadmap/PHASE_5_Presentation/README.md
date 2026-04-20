# Phase 5: Presentation Layer

> **Status:** 🔲 Queued
> **Prerequisite:** Phase 4 Infrastructure (must be complete — the backend must be running)

## Strategy

Phase 5 builds the frontend that users actually see, interact with, and speak into. The project ships as **two targets** from a single codebase:

1. **Electron Desktop App** (`.exe`) — Primary experience for gamers. Runs alongside Destiny 2.
2. **Web Version** — Identical UI served from the Rust backend for browser-only users.

We use **Vertical Feature Slicing** again. Each sub-phase delivers one visible, testable piece of the UI.

## Existing Assets

There is a legacy `webapp/index.html` (648 lines) containing a **complete Destiny-themed design system** with CSS custom properties, glassmorphism panels, chat bubbles, and responsive layouts. This design system should be harvested and reused — do NOT start from scratch.

There is also a legacy `frontend/` React app (CRA-based) that should be **replaced** with a modern Vite + React scaffold inside `apps/desktop/`.

## Sub-Phase Tracker

| Phase | Title | Status | Deliverable |
|:------|:------|:-------|:------------|
| 5A | [Project Scaffold](./PHASE_5A_Project_Scaffold.md) | 🔲 | Vite + React + Electron shell running |
| 5B | [Design System](./PHASE_5B_Design_System.md) | 🔲 | Destiny-themed tokens, components, layouts |
| 5C | [Auth UI](./PHASE_5C_Auth_UI.md) | 🔲 | Bungie login screen + OAuth redirect |
| 5D | [Voice Interface](./PHASE_5D_Voice_Interface.md) | 🔲 | Microphone capture + WebSocket streaming |
| 5E | [Inventory UI](./PHASE_5E_Inventory_UI.md) | 🔲 | Visual gear grid with equip/vault actions |
| 5F | [Lore Chat](./PHASE_5F_Lore_Chat.md) | 🔲 | Conversational AI chat panel |

## Dependency Order

```
5A ──► 5B ──► 5C ──┐
                    ├──► 5D ──► 5F
                    ├──► 5E
                    └────────────┘
```

- **5A** must be completed first (provides the project scaffold).
- **5B** must follow (all UI components depend on the design tokens).
- **5C** must follow (all features require an authenticated session).
- **5D**, **5E** can be done in parallel once 5C is complete.
- **5F** depends on 5D (voice + lore chat share the same conversation panel).
