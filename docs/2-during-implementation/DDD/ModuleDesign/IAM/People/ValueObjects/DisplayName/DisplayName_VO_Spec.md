# DisplayName Value Object Specification

**Module:** IAM
**Parent Aggregate:** User
**Role:** Human-readable display name
**Version:** 1.0.0
**Status:** Draft

---

## 1. Purpose

DisplayName is the human-readable label for a person in the system. It appears in:

- Membership lists ("Marcus Gettys — Admin")
- Job assignment ("Assigned to: Marcus Gettys")
- Activity logs ("Marcus Gettys submitted findings")
- Professional network profiles

The VO exists to guarantee the stored name is trimmed (no accidental whitespace padding) and non-empty (a blank name is not a valid identity label).

---

## 2. Canonical Representation

- **Canonical field:** `value` (String)
- **Canonical form:** Trimmed string with original casing preserved
- **Equality rule:** Exact match on trimmed value (case-sensitive — "Marcus" ≠ "marcus")

---

## 3. Shape

```rust
/// A validated, trimmed display name.
/// Construction guarantees invariants are satisfied.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct DisplayName(String);

impl DisplayName {
    pub fn new(raw: &str) -> Result<Self, DisplayNameError> { /* ... */ }
    pub fn as_str(&self) -> &str { &self.0 }
}
```

The inner `String` is private. All construction goes through `DisplayName::new()`.

---

## 4. Invariants (Hard Validation Rules)

| # | Rule | Rationale |
| :- | :--- | :--- |
| 1 | Must be non-empty after trim | A blank name is not a valid display label |
| 2 | Max length 200 characters | Prevents abuse; no real name exceeds this |

### What we do NOT validate

- **Character set restrictions.** Names can contain Unicode, hyphens, apostrophes, spaces, etc. We don't reject "José" or "O'Brien" or "Mary-Jane."
- **"Real name" verification.** The system doesn't check if the name is a real human name. "Plumber Joe" and "Test User" are both accepted.

---

## 5. Normalization Rules

Applied inside `DisplayName::new()` before validation:

1. **Trim** leading/trailing whitespace.
2. **Collapse** internal whitespace runs to single spaces (e.g., `"Marcus  Gettys"` → `"Marcus Gettys"`).

After normalization, invariants are checked against the cleaned value.

---

## 6. Errors

```rust
pub enum DisplayNameError {
    Empty,
    TooLong,
}
```

---

## 7. Serialization

| Context | Format | Example |
| :--- | :--- | :--- |
| Domain | `DisplayName` struct (newtype) | `DisplayName("Marcus Gettys")` |
| JSON (API) | Plain string | `"Marcus Gettys"` |
| Database | `TEXT` column | `Marcus Gettys` |

Serde: `DisplayName` implements `Serialize` (as string) and `Deserialize` (via `DisplayName::new()`, so deserialization validates).

---

## 8. Persistence Mapping

| Domain Field | DB Column | Type | Constraint |
| :--- | :--- | :--- | :--- |
| `value` | `users.name` | TEXT | CHECK (length(trim(name)) > 0), CHECK (name = trim(name)) |

The CHECK constraints are defense-in-depth. The VO guarantees trimming and non-emptiness, but the DB constraints catch any bypass.

---

## 9. Examples

**Valid (after normalization):**

| Input | Normalized | Notes |
| :--- | :--- | :--- |
| `"Marcus Gettys"` | `"Marcus Gettys"` | Already clean |
| `"  Marcus Gettys  "` | `"Marcus Gettys"` | Trimmed |
| `"Marcus  Gettys"` | `"Marcus Gettys"` | Internal whitespace collapsed |
| `"José O'Brien-Smith"` | `"José O'Brien-Smith"` | Unicode, apostrophes, hyphens are valid |

**Invalid (hard reject):**

| Input | Error | Why |
| :--- | :--- | :--- |
| `""` | `Empty` | No name |
| `"   "` | `Empty` | Whitespace-only |

---

## 10. Non-goals

- **Splitting into first/last name.** Display name is a single string. Some cultures don't split names the western way.
- **Case normalization.** Names preserve original casing. "mcdonald" and "McDonald" are stored as entered.
- **Uniqueness.** Names are not unique. Two people can have the same display name.
