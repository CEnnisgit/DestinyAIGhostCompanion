# Phase 4: Infrastructure Adapters

> **Status:** 🟡 In Progress
> **Prerequisite:** Phase 1-3 Domain Foundation (✅ Complete)

## Strategy

Phase 4 connects the pure Domain layer (`crates/domain/`) to the real world by implementing concrete Adapters in `crates/db/` and `crates/api/`.

We use **Vertical Feature Slicing**: each sub-phase delivers one fully functional, end-to-end feature. This approach is optimized for a developer + AI agent workflow — the agent receives one isolated phase document at a time.

## Sub-Phase Tracker

| Phase | Title | Status | Deliverable |
|:------|:------|:-------|:------------|
| 4A | [Local Foundation](./PHASE_4A_Local_Foundation.md) | 🔲 | Docker + Postgres running locally |
| 4B | [Auth Slice](./PHASE_4B_Auth_Slice.md) | 🔲 | Working Bungie OAuth login |
| 4C | [Conversation Slice](./PHASE_4C_Conversation_Slice.md) | 🔲 | Ghost can speak via WebSocket |
| 4D | [Inventory Slice](./PHASE_4D_Inventory_Slice.md) | 🔲 | Ghost can move weapons in-game |
| 4E | [Lore RAG Slice](./PHASE_4E_Lore_RAG_Slice.md) | 🔲 | Ghost answers Destiny lore questions |

## Dependency Order

```
4A ──► 4B ──► 4C ──┐
                    ├──► 4E
         4D ───────┘
```

- **4A** must be completed first (provides Postgres).
- **4B** must follow (all other features require an authenticated user token).
- **4C** and **4D** can be done in parallel once 4B is complete.
- **4E** depends on 4C (the RAG pipeline feeds into the conversation engine) and 4D (manifest item resolution feeds into inventory lookups).
