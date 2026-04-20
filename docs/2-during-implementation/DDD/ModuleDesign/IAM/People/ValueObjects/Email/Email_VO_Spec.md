# Email Value Object Specification

**Module:** IAM
**Parent Aggregate:** User
**Role:** Login identity — globally unique across all users
**Version:** 1.0.0
**Status:** Draft

---

## 1. Purpose

Email is the single identifier that connects a person to their account. It's what they type to log in, what they use to receive invitations, and what other users see when searching for people to connect with.

Because email is the login identity, getting it wrong has real consequences: duplicate accounts, failed logins, invitation delivery failures. The VO exists to guarantee that every email stored in the system is clean, consistent, and comparable.

---

## 2. Canonical Representation

- **Canonical field:** `value` (String)
- **Canonical form:** Lowercased, trimmed string (e.g., `"marcus@example.com"`)
- **Equality rule:** Exact match on canonical form. `Marcus@Gmail.com` and `marcus@gmail.com` are the same email.

---

## 3. Shape

```rust
/// A validated, lowercased, trimmed email address.
/// Construction guarantees invariants are satisfied.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email(String);

impl Email {
    pub fn new(raw: &str) -> Result<Self, EmailError> { /* ... */ }
    pub fn as_str(&self) -> &str { &self.0 }
}
```

The inner `String` is private. There is no `From<String>` — all construction goes through `Email::new()`, which enforces invariants.

---

## 4. Invariants (Hard Validation Rules)

| #  | Rule                          | Rationale                                              |
| :- | :---------------------------- | :----------------------------------------------------- |
| 1  | Must be non-empty after trim  | An empty email is not an identity                      |
| 2  | Must contain exactly one `@`  | Minimum structural validity                            |
| 3  | Local part (before @) non-empty | `@example.com` is not a valid email                  |
| 4  | Domain part (after @) non-empty | `marcus@` is not a valid email                       |
| 5  | Domain must contain at least one `.` | `marcus@localhost` is not a real-world email   |
| 6  | Max length 254 characters     | RFC 5321 limit                                         |

### What we do NOT validate

- **Full RFC 5322 compliance.** Emails like `"weird chars"@example.com` are technically valid per the RFC but never seen in practice. We validate the 99.9% case.
- **DNS/MX record existence.** That's a delivery concern, not an identity concern. If the email is structurally valid, we accept it.

### Why this level of validation

We're not an email service. We need enough validation to catch typos and garbage input (`""`, `"asdf"`, `"@"`), but we don't need to parse every edge case in RFC 5322. The real uniqueness enforcement happens at the DB level.

---

## 5. Normalization Rules

Applied inside `Email::new()` before validation:

1. **Trim** leading/trailing whitespace.
2. **Lowercase** the entire string. Email local parts are technically case-sensitive per the RFC, but no major provider treats them that way, and case-sensitive emails would create duplicate-account bugs.

After normalization, invariants are checked against the cleaned value.

---

## 6. Errors

```rust
pub enum EmailError {
    Empty,
    MissingAtSign,
    EmptyLocalPart,
    EmptyDomain,
    DomainMissingDot,
    TooLong,
}
```

---

## 7. Serialization

| Context | Format | Example |
| :--- | :--- | :--- |
| Domain | `Email` struct (newtype) | `Email("marcus@example.com")` |
| JSON (API) | Plain string | `"marcus@example.com"` |
| Database | `TEXT` column (lowercased) | `marcus@example.com` |

Serde: `Email` implements `Serialize` (as string) and `Deserialize` (via `Email::new()`, so deserialization validates).

---

## 8. Persistence Mapping

| Domain Field | DB Column | Type | Constraint |
| :--- | :--- | :--- | :--- |
| `value` | `users.email` | TEXT | UNIQUE, CHECK (email = lower(email)) |

The `CHECK (email = lower(email))` constraint is defense-in-depth. The VO guarantees lowercasing, but the DB constraint catches any bypass (e.g., direct SQL inserts during debugging).

---

## 9. Examples

**Valid (after normalization):**

| Input | Normalized | Notes |
| :--- | :--- | :--- |
| `"marcus@example.com"` | `"marcus@example.com"` | Already clean |
| `" Marcus@Gmail.COM "` | `"marcus@gmail.com"` | Trimmed + lowercased |
| `"plumber.joe+test@yahoo.com"` | `"plumber.joe+test@yahoo.com"` | Plus addressing is valid |

**Invalid (hard reject):**

| Input | Error | Why |
| :--- | :--- | :--- |
| `""` | `Empty` | Nothing to work with |
| `"  "` | `Empty` | Whitespace-only |
| `"marcus"` | `MissingAtSign` | No @ sign |
| `"@example.com"` | `EmptyLocalPart` | Who is this? |
| `"marcus@"` | `EmptyDomain` | Where does this go? |
| `"marcus@localhost"` | `DomainMissingDot` | Not a real-world domain |

---

## 10. Non-goals

- **Email verification flow** (send a confirmation link) — Phase 3B concern, not VO-level.
- **Multiple emails per user** — not planned. One email = one identity.
- **Email change cooldown** — application-level policy if needed, not VO-level.
