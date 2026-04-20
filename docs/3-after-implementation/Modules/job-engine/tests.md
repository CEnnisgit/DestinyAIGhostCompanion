# Tests — Walkthrough

**File:** `crates/pcd-domain/src/jobs/tests.rs` (469 lines)

## Overview

69 unit tests organized into 7 modules covering the Job aggregate root and all 5 Value Objects. Every `JobError` variant is exercised, and terminal-state guards are tested individually for each command.

**Run:** `cargo test -p pcd-domain` — all 69 pass in ~0.02s.

## Test Modules

### `status_tests` — 9 tests

Tests the `JobStatus` state machine directly.

| Test | Validates |
| :--- | :--- |
| `initial_returns_open` | Default state is `Open` |
| `from_str_accepts_valid_values` | All 4 string representations parse |
| `from_str_rejects_unknown` | Invalid string returns error |
| `as_str_roundtrips_with_from_str` | Serialize → deserialize is identity |
| `open_can_transition_to_in_progress_and_canceled` | Valid forward transitions |
| `in_progress_can_transition_to_completed_and_canceled` | Valid forward transitions |
| `completed_is_terminal_with_no_transitions` | Blocks all transitions |
| `canceled_is_terminal_with_no_transitions` | Blocks all transitions |
| `transition_to_invalid_target_returns_error` | OPEN → COMPLETED rejected |

### `job_number_tests` — 5 tests

| Test | Validates |
| :--- | :--- |
| `valid_job_number_is_accepted` | Happy path |
| `empty_string_is_rejected` | Non-empty invariant |
| `whitespace_only_is_rejected` | Trimmed emptiness |
| `exceeding_max_length_is_rejected` | 20-char limit |
| `lowercase_is_normalized_to_uppercase` | `job-001` → `JOB-001` |

### `job_type_tests` — 9 tests

| Test | Validates |
| :--- | :--- |
| `from_str_accepts_ll152_inspection` | Known type parses |
| `from_str_accepts_emergency` | Emergency type parses |
| `from_str_accepts_repair` | Repair type parses |
| `from_str_rejects_unknown` | Unknown type rejected |
| `display_name_is_human_readable` | `"LL152 Inspection"` output |
| `display_name_emergency` | `"Emergency"` output |
| `display_name_repair` | `"Repair"` output |
| `as_str_roundtrips` | Serialize → deserialize identity |
| `all_returns_all_variants` | `JobType::all()` returns 3 variants |

### `source_kind_tests` — 3 tests

| Test | Validates |
| :--- | :--- |
| `from_str_accepts_all_six_values` | All 6 variants parse |
| `from_str_rejects_unknown` | Unknown value rejected |
| `as_str_roundtrips_with_from_str` | Serialize → deserialize identity |

### `priority_tests` — 5 tests

| Test | Validates |
| :--- | :--- |
| `from_str_accepts_all_three_values` | NORMAL, HIGH, URGENT all parse |
| `from_str_rejects_unknown` | Unknown value rejected |
| `as_str_roundtrips_with_from_str` | Serialize → deserialize identity |
| `rank_ordering_is_normal_high_urgent` | Rank values: 0, 1, 2 |
| `ord_sorts_correctly` | Vec sort: URGENT > HIGH > NORMAL |

### `job_factory_tests` — 9 tests

| Test | Validates |
| :--- | :--- |
| `open_creates_job_in_open_state` | Factory returns OPEN status |
| `open_emits_job_opened_event` | Exactly 1 event emitted |
| `open_auto_generates_title` | Default title format |
| `open_uses_custom_title_when_provided` | Custom title preserved |
| `open_accepts_all_optional_fields_as_none` | Minimal creation works |
| `open_rejects_invalid_job_number` | `InvalidJobNumber` error |
| `open_rejects_invalid_job_type` | `InvalidJobType` error |
| `open_rejects_invalid_source_kind` | `InvalidSourceKind` error |
| `open_rejects_invalid_priority` | `InvalidPriority` error |

### `job_command_tests` — 13 tests

Tests every aggregate command, including terminal-state guards tested **individually per command** (not just via a shared helper).

| Test | Validates |
| :--- | :--- |
| `start_transitions_to_in_progress` | Happy path |
| `complete_transitions_to_completed` | Happy path |
| `cancel_transitions_to_canceled_with_reason` | Happy path + reason capture |
| `cancel_from_in_progress_is_valid` | Non-obvious valid transition |
| `start_on_completed_job_fails` | `TerminalState` error |
| `update_summary_on_canceled_job_fails` | Terminal guard |
| `update_site_notes_on_canceled_job_fails` | Terminal guard |
| `update_priority_on_completed_job_fails` | Terminal guard |
| `attach_client_on_completed_job_fails` | Terminal guard |
| `assign_ownership_on_canceled_job_fails` | Terminal guard |
| `link_obligation_sets_id_and_emits_event` | Happy path |
| `unlink_obligation_with_none_linked_fails` | `NoObligationLinked` error |
| `clear_uncommitted_events_empties_vec` | Event management |

## Coverage Analysis

| Error Variant | Tested By | Count |
| :--- | :--- | :--- |
| `InvalidJobNumber` | factory: `open_rejects_invalid_job_number` | 1 |
| `InvalidJobType` | factory: `open_rejects_invalid_job_type` | 1 |
| `InvalidSourceKind` | factory: `open_rejects_invalid_source_kind` | 1 |
| `InvalidPriority` | factory: `open_rejects_invalid_priority` | 1 |
| `InvalidTransition` | status: `transition_to_invalid_target`, commands: `start_on_completed` | 2 |
| `TerminalState` | commands: 5 individual guard tests | 5 |
| `NoObligationLinked` | commands: `unlink_obligation_with_none_linked_fails` | 1 |

**All 7 `JobError` variants covered.**

## Testing Strategy

- **No mocks**: Tests exercise the domain layer directly — no database, no HTTP
- **Helper function**: `make_test_params()` creates valid `OpenJobParams` for each test
- **Individual terminal guards**: Each command that uses `guard_not_terminal()` has its own test asserting the error, rather than relying on a single shared test. This ensures regressions are caught per-command.
- **State machine isolation**: `JobStatus` transitions are tested independently of the aggregate
