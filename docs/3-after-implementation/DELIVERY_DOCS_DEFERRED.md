# After-Implementation: Delivery Docs — Deferred

> **Status:** ⏳ Deferred until alpha launch is imminent
> **Reference:** [PDA-SDD Paper — §4.1–4.2](../pda-sdd-paper/03_model_overview.md)

---

## What PDA-SDD Requires for "After-Implementation"

The After-Implementation phase is the **Delivery phase** — when software is handed to end-users. It is distinct from the developer walkthroughs currently in `docs/3-after-implementation/Modules/`.

### Essential Deliverables

| Category | Document | Paper Section | Status |
| :--- | :--- | :--- | :--- |
| **User Documentation** | SUMD (Software User Manual) | [§4.3.5](../pda-sdd-paper/08_sumd.md) | ⏳ Deferred |
| **Technical Documentation** | Updated SRSD (sync with reality) | [§4.3.1](../pda-sdd-paper/04_srsd.md) | ⏳ Deferred |
| **Technical Documentation** | Updated DDD (sync with reality) | [§4.3.3](../pda-sdd-paper/06_ddd.md) | ⏳ Deferred |
| **Legal Documentation** | EULA | [§4.3.6](../pda-sdd-paper/09_eula.md) | ⏳ Deferred |

### Optional Deliverables

| Document | Status |
| :--- | :--- |
| Quick Guide | ⏳ Deferred |
| CLD (Change Log) | ✅ Exists (`docs/2-during-implementation/CLD/`) |
| Certificates | N/A |

---

## When to Do This

**Trigger:** When the alpha launch for the two early-adopter plumbers is within reach — i.e., the web dashboard has a working job flow and the API is deployed.

### SUMD Checklist (for alpha)
- [ ] Introduction — what is PCD, who is it for
- [ ] Getting Started — how to log in, system requirements
- [ ] Core Features — creating a job, tracking status, viewing buildings
- [ ] Troubleshooting — common errors, who to contact
- [ ] Glossary — LL152, BIN, BBL, compliance obligation, etc.

### EULA Checklist (for alpha)
- [ ] Grant of License — alpha/beta terms
- [ ] Ownership — IP belongs to the firm
- [ ] Restrictions — no redistribution
- [ ] Warranty Disclaimer — alpha = no guarantees
- [ ] Termination — alpha can be revoked
- [ ] (Have a lawyer review before giving to real users)

### SRSD/DDD Sync Checklist
- [ ] Review `docs/1-pre-implementation/SRSD/` — do requirements match what was built?
- [ ] Review `docs/2-during-implementation/DDD/` — are module designs current?
- [ ] Flag any drift between specs and implementation

---

## What We Have Now (Developer Walkthroughs)

The content in `docs/3-after-implementation/Modules/` is **engineering documentation** — code walkthroughs, architecture diagrams, test coverage. This is valuable but serves a different purpose than the PDA-SDD delivery docs. It should stay where it is.
