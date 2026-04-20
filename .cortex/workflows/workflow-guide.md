---
description: Quick guide to choosing the right workflow
---

# Workflow Guide

Start here to find the right workflow for your task.

## Quick Reference

| I want to... | Use |
|--------------|-----|
| **⭐ Full context recovery (fresh conversation)** | `/onboard` |
| **Start a work session** | `/start-work` |
| **Start a new sub-phase (3B, 3C, etc.)** | `/start-subphase` |
| **Track progress during a sub-phase** | `/maintain-subphase` |
| **Close out a sub-phase with verification** | `/finish-subphase` |
| **Re-learn the PDA-SDD framework** | `/pda-onboard` |
| **Re-learn architectural decisions** | `/adr-onboard` |
| Design a new module | `/design-module` |
| Trace a request through layers | `/trace-request` |
| Audit a module for compliance | `/audit-module` |
| Check for missing ADRs | `/adr-check` |
| Draft an ADR from context | `/adr-capture` |
| Check docs for staleness | `/doc-audit` |
| Log a completed feature to CLD | `/log-feature` |
| Make a well-formed commit | `/commit` |

## Workflow Categories

### 🚀 Session & Phase Management

| Workflow | When to Use |
|----------|-------------|
| `/start-work` | Beginning any work session — checks git status, decides branching |
| `/start-subphase` | Starting a new sub-phase — scaffolds 4 artifacts (matrix, journal, audit, traceability) |
| `/maintain-subphase` | During an active sub-phase — updates journal + matrix each session |
| `/finish-subphase` | Closing a sub-phase — spec audit, traceability proof, gate checks |

### 📋 PDA-SDD Documentation

| Workflow | When to Use |
|----------|-------------|
| `/pda-onboard` | Agent lost context on the Pre-During-After framework — read-only recovery |
| `/pda-pre-implementation` | Generating SRSD + RLD from a PRD |
| `/pda-during-implementation` | Populating DDD + CLD during coding |
| `/pda-after-implementation` | Generating SUMD + EULA after shipping |
| `/pda-sync-feature` | Updating DDD for a single feature cyclically |

### 🏗️ Architecture & Code

| Workflow | When to Use |
|----------|-------------|
| `/design-module` | Research worksheet for a new module — feeds into DDD spec design |
| `/trace-request` | Debugging or understanding request flow through all layers |
| `/audit-module` | Verifying a module follows architectural patterns |

### 📝 Documentation & ADRs

| Workflow | When to Use |
|----------|-------------|
| `/adr-onboard` | Fresh agent needs architectural context — reads EVOLUTION + relevant ADRs |
| `/adr-check` | Mining conversations/commits for missing ADR candidates |
| `/adr-capture` | Drafting an ADR + updating README index + checking EVOLUTION arcs |
| `/doc-audit` | Auditing docs for staleness and missing coverage |
| `/log-feature` | Logging a feature completion to the CLD directory |

### 🔧 Git

| Workflow | When to Use |
|----------|-------------|
| `/commit` | Making a well-formed commit following project conventions |

## Workflow Chains

Some tasks need multiple workflows in sequence:

| Task | Chain |
|------|-------|
| Start a new phase | `/start-work` → `/start-subphase` |
| Each session in a phase | `/start-work` → `/maintain-subphase` |
| Close out a phase | `/finish-subphase` → `/commit` |
| New module research | `/design-module` → `/pda-during-implementation` |
| Refactor + verify | Make changes → `/audit-module` |
| Debug failing request | `/trace-request` → fix → test |
| Agent confused about docs | `/pda-onboard` → continue work |
| Agent confused about architecture | `/adr-onboard` → continue work |
| Full context recovery | `/pda-onboard` + `/adr-onboard` → continue work |
