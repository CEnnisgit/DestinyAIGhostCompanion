# SRSD: Software Requirements Specification Document

> **Status:** Baseline / Phase 1
> **Project:** Destiny AI Ghost Companion
> **Source:** [PRD_EXTRACTION_NOTES.md](../PRD_EXTRACTION_NOTES.md)

## 1. Introduction
The SRSD defines the strict functional and non-functional requirements extracted directly from the Phase 0 PRD Extraction file for the Destiny AI Ghost Companion. It bridges the conceptual product features (voice commands, seamless inventory management) into hard, verifiable technical rules.

### Sub-Sections
- [**SGI** (General Info)](./SGI/) - Application Scope, Immersion Objectives, Main Voice Functions
- [**SFR** (Functional)](./SFR/) - Input/Output, Business Prohibitions, Authentication flow, LLM Integration
- [**SNFR** (Non-Functional)](./SNFR/) - AI Response Performance, Usability, Executable Portability

---

## 2. Traceability Summary

### Functional Requirements (SFR)
- **SFR-IO (Input/Output):** Microphone capture capabilities, Text-To-Speech execution.
- **SFR-PR (Processing):** Speech-To-Text processing, AI Intent Classification, Item Name Resolution.
- **SFR-BR (Business Rules):** Hard API limitations, explicit bounds preventing destructive actions (e.g. dismantling items).
- **SFR-SR (Security):** Bungie OAuth2 handshake security, Local AES token storage.
- **SFR-IR (Integration):** Contracts for external dependencies (Ollama localhost bounds, Bungie HTTPS requirements).

### Non-Functional Requirements (SNFR)
- **SNFR-P (Performance):** Tolerance thresholds for LLM inference turn-arounds.
- **SNFR-SC (Scalability):** Hardware constraints for executing local models alongside the video game.
- **SNFR-U (Usability):** Defining what "hands-free" and "zero-click" mechanically means for the operator.
- **SNFR-R (Reliability):** LLM Model failover thresholds (Grok fallback logic).
- **SNFR-S (Security):** Token lifecycle persistence.
- **SNFR-M (Maintainability):** Vertical Slice module isolation limits, Desktop `.exe` portable footprint limits.
