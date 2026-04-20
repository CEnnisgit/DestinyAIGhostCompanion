# SNFR-U: Usability Requirements

> **Parent:** [SNFR Index](../README.md) | **Prev:** [SNFR-P](./SNFR-P_performance.md) | **Next:** [SNFR-S](./SNFR-S_security.md)

## Sub-Types
- [SNFR-UEU (Ease of Use)](#snfr-ueu-ease-of-use)
- [SNFR-UE (Efficiency)](#snfr-ue-efficiency)
- [SNFR-UA (Aesthetics)](#snfr-ua-aesthetics)

---

## SNFR-UEU: Ease of Use

### Plumber (Field) Experience

| Code | Description | Target | PRD Ref |
|------|-------------|--------|---------|
| `SNFR-UEU-01` | **Phone-First Design:** Mobile interface prioritizes touch; minimal typing required. | Yes | §0.2 |
| `SNFR-UEU-02` | **One-Handed Operation:** Primary actions (next, save, photo) reachable with thumb on standard phone. | Yes | §0.2 |
| `SNFR-UEU-03` | **Max Taps to Job:** From login/home to viewing current job details. | ≤ 3 taps | §3.1 |
| `SNFR-UEU-04` | **Zero Training Start:** New user can complete first capture within 10 minutes of onboarding. | Yes | §6.1 |
| `SNFR-UEU-05` | **[TBD] Photo Standards:** Photos must be legible, timestamped, and auto-labeled by context. | Yes | GAP-04 |

### LMP (Dashboard) Experience

| Code | Description | Target | PRD Ref |
|------|-------------|--------|---------|
| `SNFR-UEU-10` | **At-a-Glance Status:** Dashboard shows job counts by status immediately on load. | Yes | §3.2 |
| `SNFR-UEU-11` | **Deadline Visibility:** Approaching deadlines highlighted prominently (color/icon). | Yes | §4.1.6 |

---

## SNFR-UE: Efficiency

### Time-to-Value

| Code | Description | Target | PRD Ref |
|------|-------------|--------|---------|
| `SNFR-UE-01` | **Time-to-Capture:** Complete GPS1 capture from start to submit. | < 2 minutes | §0.2 |
| `SNFR-UE-02` | **No Retyping:** LMP generates GPS1/GPS2 packet without re-entering Plumber's data. | 0 fields retyped | §0.3 |

### Smart Defaults

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SNFR-UE-10` | **Pre-filled Address:** When job created from existing Building, address data pre-populated. | §2.1 |
| `SNFR-UE-11` | **Default Inspection Date:** Defaults to "today" when Plumber starts capture. | §2.3 |

---

## SNFR-UA: Aesthetics

### Visual Design

| Code | Description |
|------|-------------|
| `SNFR-UA-01` | **High Contrast Mode:** Interface readable in outdoor/bright conditions. |
| `SNFR-UA-02` | **Clean, Modern UI:** Consistent design system (shadcn/Tailwind-based). |
| `SNFR-UA-03` | **Status Colors:** Distinct colors for each job status (e.g., green=Finalized, yellow=Needs Review, red=Overdue). |

### Accessibility

| Code | Description |
|------|-------------|
| `SNFR-UA-10` | **Font Size:** Minimum 16px body text for field readability. |
| `SNFR-UA-11` | **Touch Targets:** Minimum 44x44px for all interactive elements. |
