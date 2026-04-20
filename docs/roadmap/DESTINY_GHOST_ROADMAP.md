# Destiny AI Ghost Companion Roadmap

Welcome to the central tracking board for the Rust migration.

## Active Trackers

### ✅ Complete
1. [Phase 1-3: Domain Foundation](./PHASE_1_3_Domain_Foundation.md)

### 🟡 In Progress
2. [Phase 4: Infrastructure Adapters](./PHASE_4_Infrastructure/README.md)
   - [4A: Local Foundation](./PHASE_4_Infrastructure/PHASE_4A_Local_Foundation.md) — Docker, Postgres, pgvector
   - [4B: Auth Slice](./PHASE_4_Infrastructure/PHASE_4B_Auth_Slice.md) — OAuth token persistence + Bungie identity
   - [4C: Conversation Slice](./PHASE_4_Infrastructure/PHASE_4C_Conversation_Slice.md) — WebSocket server + OpenAI client
   - [4D: Inventory Slice](./PHASE_4_Infrastructure/PHASE_4D_Inventory_Slice.md) — Bungie API equip/transfer/vault
   - [4E: Lore RAG Slice](./PHASE_4_Infrastructure/PHASE_4E_Lore_RAG_Slice.md) — Manifest ETL + pgvector search

### 🔲 Queued
3. [Phase 5: Presentation](./PHASE_5_Presentation/README.md)
   - [5A: Project Scaffold](./PHASE_5_Presentation/PHASE_5A_Project_Scaffold.md) — Vite + React + Electron
   - [5B: Design System](./PHASE_5_Presentation/PHASE_5B_Design_System.md) — Destiny-themed tokens + components
   - [5C: Auth UI](./PHASE_5_Presentation/PHASE_5C_Auth_UI.md) — Bungie login screen + OAuth redirect
   - [5D: Voice Interface](./PHASE_5_Presentation/PHASE_5D_Voice_Interface.md) — Microphone + WebSocket streaming
   - [5E: Inventory UI](./PHASE_5_Presentation/PHASE_5E_Inventory_UI.md) — Visual gear management grid
   - [5F: Lore Chat](./PHASE_5_Presentation/PHASE_5F_Lore_Chat.md) — Conversational AI chat panel
