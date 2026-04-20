# Detailed Design: Non-Functional Traceability Matrix

> **Source SRSD Codes:** Phase 1 `SNFR`
> **Target Architecture:** Phase 2 Cargo Workspace

| SRSD Code | Description | Target Module Crate | Rationale |
|-----------|-------------|---------------------|-----------|
| `SNFR-PRT-01` | Voice execution latency < 3.5s | `crates/api` & `crates/domain` | Axum + Tokio ensures high-throughput, while Rust local inference requests wait as minimally as possible. |
| `SNFR-PRT-02` | Bungie Rate Limiting | `crates/domain` | Rust `reqwest` client implements exponential backoff on HTTP 429 errors. |
| `SNFR-PT-01` | Long duration performance leakage | Cargo Workspace | Rust's borrow-checker inherently prevents standard memory-leak fatigue seen in long running python processes. |
| `SNFR-SCH-01..03` | Minimal Hardware Footprint | Cargo Workspace | Native desktop (Electron) paired with Rust binary consumes drastically less overhead. |
| `SNFR-UEU-01..02` | Hands-Free navigation | `apps/frontend` | React SPA implements pure global hotkey listener or constant voice activation. |
| `SNFR-UA-01` | Accessibility / UI Chat logs | `apps/frontend` | UI handles fetching and rendering pagination lists. |
| `SNFR-RAV-01` | Bungie downtime grace | `crates/api` | Axum HTTP exception filters catch external 5xx and return typed errors to the front end. |
| `SNFR-RF-01..02` | LLM & STT failovers | `crates/domain` & `apps/frontend` | Fallback models triggered automatically upon ping timeouts. |
| `SNFR-STL-01..02` | Token persistence isolation | `crates/db` | The frontend securely communicates via isolated APIs; literal Bungie tokens sit exclusively in Postgres. |
| `SNFR-SDP-01` | Privacy & explicit Localhost loops | `crates/domain` | Intent configurations explicitly reject external transmission unless xAI/Grok fallback is explicitly enabled. |
| `SNFR-MM-01` | Vertical slice encapsulation | Cargo Workspace | The distinct split of `crates/db`, `crates/domain`, and `crates/api` rigidly silo responsibilities securely. |
| `SNFR-MP-01..02` | Executable `.exe` bundling | `apps/frontend` | Electron builder handles the packaging. |
