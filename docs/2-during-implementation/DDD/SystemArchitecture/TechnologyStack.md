# Detailed Design: Technology Stack (SystemArchitecture)

This document formalizes the technologies utilized across the Destiny AI Ghost Companion monorepo.

## 1. Multi-Crate Backend (Rust)
The core backend execution relies on natively compiled Rust via a Cargo Workspace to maximize performance and strictly control memory behavior while running alongside the game logic.
- **Language**: Rust (Edition 2021)
- **HTTP/Routing**: Axum + Tower (Leveraging `tokio` for async concurrency)
- **Database Driver**: SQLx (Compile-time validated SQL queries without the overhead of an ORM)
- **Serialization**: Serde (JSON parsing for Bungie API integrations)

## 2. Desktop Interface (Frontend)
The user-facing application is delivered as a standalone native Desktop executable.
- **Framework**: Electron (Node.js backend wrapper for the desktop context)
- **UI Render Layer**: React (Bootstrapped via Vite for HMR)
- **State Management**: Zustand or React Context
- **Design/Styling**: Utility-first styling with strict Destiny 2 dark-theme branding applied to the Electron window.

## 3. Data Storage & Execution
- **Relational Storage**: PostgreSQL (Deployed via Docker Compose for local environment strict isolation)
- **Manifest Cache**: SQLite (Direct file-read for the static Bungie item definitions manifest)
- **AI Inference Engine**: Ollama (Running locally via loopback HTTP `11434` for LLaMA/Phi-3 execution)
