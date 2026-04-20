# PRD Extraction Notes: Destiny AI Ghost Companion

> **Source:** [PRD_DESTINY_GHOST.md](../../) *(Phase 0 artifact)*
> **Generated:** 2026-04-20
> **Purpose:** Structured extraction from PRD to verify SRSD alignment and identify gaps before drafting technical specs.

---

## 1. Goals & Product Promise (PRD §1)

### Core Objective
- "Seamless, hands-free method to make quick inventory and vault actions via voice commands while actively in-game"
- Zero inventory-screen interruptions
- Immersive Ghost persona interaction

| PRD Claim | SRSD Target Code | Status |
|-----------|-----------------|--------|
| Hands-free voice commands | `SFR-IODE-01` (Voice Input Capture) | 🆕 Draft |
| Zero inventory screen needed | `SNFR-UEU-01` (Ease of Use) | 🆕 Draft |
| Immersive Ghost persona | `SFR-IODO-05` (Persona-Styled Response) | 🆕 Draft |

---

## 2. Target Personas (PRD §2)

| Persona | Primary Need | SRSD Mapping |
|---------|-------------|--------------|
| Hardcore Raider | Instant weapon/armor swap mid-encounter | `SFR-IODE-02` (Equip Command), `SNFR-PRT-01` (Response Time) |
| Lore Enthusiast | In-universe conversation with Ghost | `SFR-IODO-06` (Lore Context Output), `SFR-PRDM-01` (Conversational vs Action Intent) |
| Casual Player | Simple vault management without apps | `SNFR-UEU-02` (Minimal Interaction Steps), `SFR-IODE-03` (Vault Command) |

---

## 3. System Capabilities Mapping (PRD §3.1)

| PRD Capability | SRSD Target Code | Category |
|---------------|-----------------|----------|
| Multi-Client Architecture (React, iOS, Vanilla) | `SFR-IRI-01` (Client Interface Contract) | SFR-IR |
| Local AI Inference (Ollama/LLaMA/Phi-3) | `SFR-IRI-02` (LLM Provider Interface) | SFR-IR |
| Grok Fallback Model Support | `SFR-IRI-03` (External LLM Fallback) | SFR-IR |
| Custom Model Fine-Tuning Pipelines | `SFR-PRDP-01` (Dataset Generation) | SFR-PR |
| Desktop Executable Bundling (PyInstaller) | `SNFR-MP-01` (Portability) | SNFR-M |
| Secure Bungie OAuth (AES token storage) | `SFR-SRAN-01` (OAuth2 Auth Flow) | SFR-SR |

---

## 4. Core User Capabilities Mapping (PRD §3.2)

### Voice-Activated Translation
| Step | SRSD Requirement |
|------|-----------------|
| Mic capture → raw audio | `SFR-IODE-01` Voice Input Capture |
| Audio → transcript (STT) | `SFR-PRC-01` Speech-to-Text Processing |
| Transcript → intent classification | `SFR-PRDM-01` Intent Classification (Action vs Chat) |
| Intent → API payload construction | `SFR-PRDM-02` Intent-to-Payload Translation |
| Response → TTS output | `SFR-IODO-01` Text-to-Speech Output |

### Equip on the Fly
| Step | SRSD Requirement |
|------|-----------------|
| Parse item name from intent | `SFR-PRDP-02` Item Name Resolution (fuzzy match against manifest) |
| Locate item (vault/character/postmaster) | `SFR-PRDP-03` Item Location Resolution |
| Transfer to active character if needed | `SFR-BRW-01` Transfer Workflow |
| Equip on active character | `SFR-BRW-02` Equip Workflow |
| Confirm success to user | `SFR-IODO-02` Action Confirmation Output |

### Vaulting
| Step | SRSD Requirement |
|------|-----------------|
| Parse item name from intent | `SFR-PRDP-02` (shared with Equip) |
| Validate item is on active character | `SFR-BRV-01` Item Location Validation |
| Transfer to vault | `SFR-BRW-03` Vault Transfer Workflow |
| Confirm success to user | `SFR-IODO-02` (shared with Equip) |

### Lore Context Integration
| Step | SRSD Requirement |
|------|-----------------|
| Detect lore-related conversational intent | `SFR-PRDM-01` (shared) |
| Fetch lore context from local store | `SFR-PRDP-04` Lore Data Retrieval |
| Generate in-universe response | `SFR-IODO-06` Lore Context Output |

### Dynamic AI Personalities
| Step | SRSD Requirement |
|------|-----------------|
| User selects or switches persona | `SFR-IODE-04` Persona Selection Input |
| System prompt adapts to persona | `SFR-PRC-02` Persona Prompt Construction |
| All responses styled to active persona | `SFR-IODO-05` Persona-Styled Response |

---

## 5. Boundaries & Constraints Mapping (PRD §4)

### Hard Prohibitions (Bungie API Enforced)

| Constraint | SRSD Requirement | Priority |
|-----------|-----------------|----------|
| No item dismantling | `SFR-BRC-01` Dismantle Action Prohibition | **CRITICAL** |
| No resource spending | `SFR-BRC-02` Resource Spending Prohibition | **CRITICAL** |

### Scope Deferrals (v1 Design Choice)

| Constraint | SRSD Requirement | Priority |
|-----------|-----------------|----------|
| No subclass/loadout editing | `SFR-BRC-03` Subclass Editing Exclusion | HIGH |
| No mod socketing | `SFR-BRC-04` Mod Socketing Exclusion | HIGH |
| No vendor purchases/bounties | `SFR-BRC-05` Vendor Interaction Exclusion | HIGH |

---

## 6. Architectural Safety Mapping (PRD §5)

| PRD Requirement | SRSD Target Code | Category |
|----------------|-----------------|----------|
| Vertical Slice Isolation | `SNFR-MM-01` Module Independence | SNFR-M |
| LLM Hallucination Containment | `SFR-BRC-06` AI-to-API Isolation Boundary | SFR-BR |
| Client Agnostic API Boundaries | `SFR-IRI-01` (shared) | SFR-IR |

> [!IMPORTANT]
> **`SFR-BRC-06` (AI-to-API Isolation)** is the single most critical safety requirement. The LLM must NEVER directly construct or execute Bungie API calls. It outputs a typed intent object; statically-typed service logic validates and executes.

---

## 7. Gap Analysis

### ✅ Fully Mapped (No Gaps)
| Area | Notes |
|------|-------|
| Voice pipeline (STT → Intent → Action → TTS) | Full chain mapped to `SFR-IODE`, `SFR-PRC`, `SFR-PRDM`, `SFR-IODO` |
| Equip/Vault workflows | State transitions covered in `SFR-BRW-01..03` |
| Safety prohibitions | All 6 constraints mapped to `SFR-BRC-01..06` |
| OAuth & token security | Covered by `SFR-SRAN-01` + `SNFR-SC` |

### ⚠️ Ambiguities Identified (Need Clarification During Implementation)

| ID | Area | Question | Priority |
|----|------|----------|----------|
| GAP-01 | **Bungie Manifest Caching** | How frequently should the Destiny manifest be refreshed locally? The env var `BUNGIE_MANIFEST_TTL` exists but no SRSD spec defines behavior on stale manifests. | MEDIUM |
| GAP-02 | **Postmaster Item Handling** | PRD does not explicitly address postmaster overflow. AGENTS.md states "postmaster items must be pulled before equip/vault workflows complete." Needs a dedicated `SFR-BRW-04`. | HIGH |
| GAP-03 | **Cross-Character Transfers** | AGENTS.md states "equipped items on another character cannot be moved until unequipped." The exact multi-step unequip→transfer→equip chain needs explicit workflow specification. | HIGH |
| GAP-04 | **Voice Mode Fallback** | AGENTS.md requires voice mode to work even without server-side STT/TTS. Browser speech APIs as baseline fallback needs a dedicated `SFR-PRC` entry. | MEDIUM |
| GAP-05 | **Rate Limiting Strategy** | Bungie API enforces rate limits. No SRSD spec currently defines retry/backoff behavior for throttled requests. | MEDIUM |

---

## 8. Blockers & Recommendations

### 🔴 Blockers (Require Resolution Before SRSD Finalization)

None. All critical items have target SRSD mappings.

### 🟡 Recommendations (Resolve During SRSD Drafting)

1. **Add `SFR-BRW-04`:** Postmaster pull workflow (GAP-02).
2. **Add `SFR-BRW-05`:** Cross-character unequip→transfer→equip chain (GAP-03).
3. **Add `SFR-PRC-03`:** Browser speech fallback for STT/TTS (GAP-04).
4. **Add `SNFR-PRT-02`:** Bungie API rate limit retry/backoff policy (GAP-05).
5. **Add `SFR-IRDX-01`:** Manifest cache TTL and staleness policy (GAP-01).

---

## 9. Verification Summary

| Section | PRD Items | SRSD Target Codes | Status |
|---------|-----------|-------------------|--------|
| SGI (Scope/Objectives) | Product overview, personas, boundaries | 3 scope items | 🆕 Draft |
| SFR-IO (Input/Output) | Voice capture, TTS output, persona selection | 6 requirements | 🆕 Draft |
| SFR-PR (Processing) | STT, intent classification, persona prompts | 4 requirements | 🆕 Draft |
| SFR-BR (Business Rules) | Prohibitions, workflows, AI isolation | 11 requirements | 🆕 Draft |
| SFR-SR (Security) | OAuth2, token encryption | 1 requirement | 🆕 Draft |
| SFR-IR (Integration) | Ollama, Grok, Bungie, client contracts | 3 requirements | 🆕 Draft |
| SNFR-P (Performance) | Response time, rate limiting | 2 requirements | 🆕 Draft |
| SNFR-U (Usability) | Hands-free, minimal steps | 2 requirements | 🆕 Draft |
| SNFR-M (Maintainability) | Module isolation, portability | 2 requirements | 🆕 Draft |
| SNFR-S (Security) | Token lifecycle | Inherited | 🆕 Draft |

**Conclusion:** The PRD maps cleanly into the PDA-SDD SRSD coding system. Five gaps were identified (GAP-01 through GAP-05), all resolvable during SRSD drafting with no blockers to execution.
