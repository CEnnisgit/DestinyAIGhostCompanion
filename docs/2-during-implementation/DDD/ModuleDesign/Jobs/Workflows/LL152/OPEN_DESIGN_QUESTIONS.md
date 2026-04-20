# LL152 Design Questions — Resolution Log

> All 7 original design questions have been resolved (2026-03-27).
> This file now serves as a resolution log and captures field observations that emerged during the design discussions.

---

## Resolved Questions

| # | Question | Resolution | Date |
|---|----------|-----------|------|
| Q1 | When is branch determined? | At intake. Defaults to `STANDARD_INSPECTION`. | 2026-03-27 |
| Q2 | Reclassification audit trail? | Must emit `BRANCH_RECLASSIFIED` event. Post-alpha. | 2026-03-27 |
| Q3 | Branch C artifact surface? | **Deferred.** Insufficient evidence. Post-alpha. | 2026-03-27 |
| Q4 | Alpha scope? | Branch A only. B/C deferred-but-known. | 2026-03-27 |
| Q5 | Review states distinct? | Yes. Alpha stops at `READY_FOR_REVIEW`. | 2026-03-27 |
| Q6 | Findings storage? | Child entities in `inspection_findings` table. | 2026-03-27 |
| Q7 | Photo attachment level? | Both: finding-level (required) + job-level. Nullable FK. | 2026-03-27 |

Full resolution text is in [LL152_Inspection_Workflow.md](./LL152_Inspection_Workflow.md) §12.

---

## Field Observation Discoveries

The following insights emerged from discussing the QI's (User A's) real-world workflow during the design question sessions. These are not speculative — they come from actual field experience.

### Discovery 1: Recall Transition (READY_FOR_REVIEW → CAPTURING)

**Source:** User A's father does ~5 inspections per day. After getting home, he noticed he had entered the wrong inspection time on one job (6pm instead of 2pm). His LMP's current app locks submissions and does not allow edits. He had to call middle management and file an issue to correct a simple timestamp.

**Design impact:** The PCD state machine must support a **recall transition** so the QI can pull back a submission before the LMP opens it:

```
READY_FOR_REVIEW → CAPTURING  (QI-initiated recall)
```

**Guard:** Only allowed if the job has NOT been moved to `UNDER_REVIEW` by the LMP. Once the LMP opens it, the QI can no longer unilaterally recall.

**This is a key UX differentiator** — competing tools lock submissions and make corrections painful. PCD should make corrections easy.

### Discovery 2: In-App Camera Capture

**Source:** On the same day, User A's father uploaded photos of the wrong building to a job — he had selected a photo from his camera roll that was actually from the previous building he'd inspected.

**Design impact:** The mobile app should prefer **in-app camera capture** over camera-roll selection. When the QI takes a photo through the app, it is automatically:
- Associated with the current job
- Timestamped
- (Future) GPS-tagged to confirm they're at the correct building

Camera-roll selection should still be available as a fallback, but in-app capture should be the primary flow.

### Discovery 3: Batch Review Flow

**Source:** The QI completes multiple inspections during the day (one job per building), then reviews them at home before handing off to the LMP.

**Design impact:** The alpha workflow should support a natural "review your day" flow:
- During the day: jobs move from `DRAFT → CAPTURING` on-site
- At home: QI reviews all captured jobs (still in `CAPTURING` state)
- When satisfied: QI submits each job individually (`CAPTURING → READY_FOR_REVIEW`)

The "submit for review" moment should feel deliberate, not automatic. The app should surface "you have 3 unsubmitted inspections" so nothing falls through the cracks.

---

### Discovery 4: Finalization Boundary (Compliance Lives Here)

**Source:** NYC LL152 legal research during Phase 3C.1 authorization design (2026-03-31). Reviewed NYC DOB gas piping inspection rules, GPS1 form requirements, and related local laws.

**Key finding:** NYC LL152 compliance rules govern the **official inspection artifact** (the signed report/certification filed with DOB), not internal app workflows like role-based submit/approve splits. The law cares about:

- Accuracy of signed/certified reports
- Filing deadlines (30-day report, 60-day certification, 120-180 day corrections)
- Immediate hazardous condition reporting
- 8-year record retention
- Criminal liability for false statements

**Design impact:** The real compliance boundary is **finalization**, not role permissions. The inspection lifecycle should enforce:

| Stage | Editable? | What happens |
|-------|----------|-------------|
| **Draft** | ✅ Yes | Findings, notes, photos, timestamps can change freely |
| **Finalized/Signed** | ❌ Locked | Content snapshot becomes the official inspection record |
| **After finalization** | New records only | Correction certification, addendum, or superseding inspection |

**Rules derived from this:**

1. **Never silently mutate a finalized record.** The legal system expects the original signed report plus correction certifications — not overwritten history.
2. **The Recall transition (Discovery 1) only applies to pre-finalization states.** Once finalized, even the QI can't unilaterally change the record.
3. **The "approve" permission is better understood as "finalize/sign."** It's not an internal workflow approval — it's the act that creates the official compliance artifact.
4. **Audit trail is mandatory after finalization.** Full history of who changed what and when, with all correction certifications tracked as separate records.

**Cross-reference:** This finding resolved 3C.1 Q4 (ADR-0034 companion) and reframed SFR-SRAZ-05 from "Approve/Return" to "Finalize/Sign Report."

**Status:** Principle established. Implementation details (immutability enforcement, correction workflow, audit schema) deferred to spec writing phase.

---

## Remaining Open Questions

### GPS1 Location Data vs Building Truth

**Surfaced in:** `gps_1_form_spec.md` §7.1

**Question:** How should the GPS1 form's location-information section relate to canonical `Building` data?

**Context:** The GPS1 form has a "Location Information" section that identifies the inspection site. Most of this data (address, BIN, block/lot) originates from the Building aggregate.

**Tension:** Copying Building data into a separate report-layer model risks duplication and staleness. But the GPS1 may need to preserve location-as-it-was-at-inspection-time (snapshot behavior).

**Likely resolution:** Pull from `Building` at report-generation time. But this needs validation against:

- Whether the LMP ever edits location details on the form
- Whether the GPS1 must preserve a snapshot (point-in-time building identity)
- Offline capture scenarios

**Status:** Deferred — resolve during schema design or first implementation pass.
