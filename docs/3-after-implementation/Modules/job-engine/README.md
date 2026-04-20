# Job Engine Module

## Overview
The Job Engine is a **company-scoped, workflow-agnostic work container** that manages the lifecycle of any field assignment. It is the central aggregate of the PCD application — every piece of work a plumber does is tracked as a Job.

The engine deliberately provides only generic lifecycle states (`OPEN → IN_PROGRESS → COMPLETED / CANCELED`). Workflow-specific logic (GPS forms, inspection findings, DOB filing) is layered on top in Phase 2.

## Key Features
- **Hexagonal Architecture**: Domain logic in `pcd-domain`, persistence adapter in `pcd-db`, HTTP API in `pcd-api`, wired via `Arc<dyn JobRepository>`
- **Rich Aggregate Root**: Factory (`open`), reconstitution, 8 mutation commands, terminal-state guards
- **Domain Event Sourcing**: Every command emits a typed domain event stored in `job_events` table
- **Strong Typing via VOs**: JobNumber, JobStatus, JobType, SourceKind, Priority — all validated at construction
- **Command Pattern API**: Generic `command_handler` function reduces boilerplate across 10 PATCH endpoints
- **Transactional Persistence**: Job upsert + event insertion happen in a single database transaction

## Architecture
- [Architecture](Architecture.md) — Component diagram, hexagonal flow, state machine

## Code Walkthroughs
- [domain.md](domain.md) — Job aggregate root: factory, commands, events, reconstitution
- [value-objects.md](value-objects.md) — 5 VOs: JobStatus, JobNumber, JobType, SourceKind, Priority
- [repository.md](repository.md) — Trait port + SqlxJobRepository adapter + persistence shape
- [api.md](api.md) — 13 Axum endpoints, request/response types, command_handler pattern
- [tests.md](tests.md) — 47 unit tests, coverage matrix, testing strategy

## Source Locations

| Crate | Path | Files | Role |
| :--- | :--- | :--- | :--- |
| `pcd-domain` | `crates/pcd-domain/src/jobs/` | 10 | Aggregate, VOs, events, repository trait, tests |
| `pcd-db` | `crates/pcd-db/src/jobs/` | 1 | SqlxJobRepository adapter |
| `pcd-api` | `crates/pcd-api/src/routes/jobs.rs` | 1 | HTTP handlers |
