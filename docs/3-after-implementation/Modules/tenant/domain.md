# Tenant Domain — Code Walkthrough

> **Crate:** `pcd-domain/src/tenant/`
> **Files:** `mod.rs`, `client.rs`, `saved_building.rs`, `repository.rs`, `tests.rs`

## Module Structure

```
tenant/
├── mod.rs             ← Module exports, re-exports key types
├── client.rs          ← Client aggregate (create, update_contact, block/unblock)
├── saved_building.rs  ← SavedBuilding entity (new, reconstitute)
├── repository.rs      ← ClientRepository + SavedBuildingRepository trait ports
└── tests.rs           ← 16 unit tests covering all commands and invariants
```

## Client Aggregate (`client.rs`)

### Identity

- `id: Uuid` — auto-generated on creation
- `company_id: Uuid` — tenant scope (FK to companies table)

### Fields

- `name: String` — required, trimmed, non-empty
- `phone: Option<String>` — optional contact phone
- `address: Option<String>` — optional default address
- `is_blocked: bool` — lifecycle flag
- `blocked_reason: Option<String>` — required when blocked (CHECK constraint)
- `created_at`, `updated_at` — timestamps

### Commands

| Command | Method | Invariants |
|---|---|---|
| Create | `Client::create(params)` | Name must be non-empty after trim |
| Update Contact | `client.update_contact(name, phone, address)` | New name must be non-empty if provided |
| Block | `client.block(reason)` | Cannot block already-blocked client; reason required |
| Unblock | `client.unblock()` | Cannot unblock non-blocked client |

### Factory vs Reconstitute

- `Client::create()` — validates input, generates UUID, sets timestamps
- `Client::reconstitute()` — no validation, used by persistence layer to hydrate from DB

### Error Type

```rust
pub enum ClientError {
    EmptyName,
    EmptyBlockReason,
    AlreadyBlocked,
    NotBlocked,
}
```

## SavedBuilding Entity (`saved_building.rs`)

Not an aggregate — no business logic beyond save/remove. A lightweight bookmark.

### Fields

- `id: Uuid` — auto-generated
- `company_id: Uuid` — tenant scope
- `building_id: Uuid` — FK to global buildings table
- `created_at: DateTime<Utc>`

### Methods

- `SavedBuilding::new(company_id, building_id)` — creates with new UUID
- `SavedBuilding::reconstitute(...)` — hydrate from DB

### Database Constraint

`UNIQUE(company_id, building_id)` — a company can only bookmark a building once.

## Tests (16 tests in `tests.rs`)

| Test | What It Covers |
|---|---|
| `create_client_with_only_name` | Minimal creation path |
| `create_client_with_all_fields` | Name + phone + address |
| `create_client_rejects_empty_name` | Empty string validation |
| `create_client_rejects_whitespace_only_name` | Whitespace-only validation |
| `create_client_trims_name` | Leading/trailing whitespace removed |
| `update_contact_changes_name` | Name update |
| `update_contact_changes_phone` | Phone update |
| `update_contact_clears_phone` | Phone set to None |
| `update_contact_rejects_empty_name` | Cannot set name to empty |
| `update_contact_advances_updated_at` | Timestamp tracking |
| `block_sets_flag_and_reason` | Blocking mechanics |
| `block_rejects_already_blocked` | Idempotency guard |
| `block_rejects_empty_reason` | Reason required |
| `block_rejects_whitespace_reason` | Whitespace-only reason rejected |
| `unblock_clears_flag_and_reason` | Unblocking mechanics |
| `unblock_rejects_non_blocked` | Guard against unblocking non-blocked |
