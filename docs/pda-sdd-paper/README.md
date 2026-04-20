# PDA-SDD Paper — Reference Material

> **Source:** Alzahrani, A.A.H. "Pre-During-After Software Development Documentation (PDA-SDD): A Phase-Based Approach for Comprehensive Software Documentation in Modern Development Paradigms." *Computers* 2025, 14, 378.
> 
> **DOI:** https://doi.org/10.3390/computers14090378

This folder contains the cleaned-up content of the PDA-SDD research paper, split into sections for easy reference.

## Sections

| File | Paper Section | Description |
|------|--------------|-------------|
| [01_introduction.md](./01_introduction.md) | §1–2 | Introduction, research questions, methodology |
| [02_related_work.md](./02_related_work.md) | §3 | Background on existing documentation models |
| [03_model_overview.md](./03_model_overview.md) | §4.1–4.2 | PDA-SDD rationale, core model, 3 phases |
| [04_srsd.md](./04_srsd.md) | §4.3.1 | Software Requirements Specification Document |
| [05_rld.md](./05_rld.md) | §4.3.2 | Resources List Document |
| [06_ddd.md](./06_ddd.md) | §4.3.3 | Detailed Design Document |
| [07_cld.md](./07_cld.md) | §4.3.4 | Change Log Document |
| [08_sumd.md](./08_sumd.md) | §4.3.5 | Software User Manual Document |
| [09_eula.md](./09_eula.md) | §4.3.6 | End User License Agreement |
| [10_advantages.md](./10_advantages.md) | §4.4–4.5 | Distinctive advantages, comparative analysis |
| [11_evaluation.md](./11_evaluation.md) | §5–8 | Survey results, discussion, limitations, future work |

## How We Use PDA-SDD

Our project adapts PDA-SDD as follows:

| Phase | PDA-SDD Docs | Our Implementation |
|-------|-------------|-------------------|
| **Pre** | SRSD, RLD | `docs/1-pre-implementation/SRSD/`, `docs/1-pre-implementation/RLD.md` |
| **During** | DDD, CLD | `docs/2-during-implementation/DDD/`, `docs/2-during-implementation/CLD/` |
| **After** | SUMD, EULA | `docs/3-after-implementation/` |
