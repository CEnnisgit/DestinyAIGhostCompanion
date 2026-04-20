# Backend API Roadmap

> Last Updated: 2025-12-15

---

## ✅ Complete

### Auth Domain
- [x] User registration (email/password, argon2)
- [x] Login + JWT token issuance
- [x] Refresh token strategy
- [x] Password reset with email
- [x] Auth middleware
- [x] Role-based access control (4 roles)
- [x] Rate limiting

### Company Domain
- [x] Company CRUD
- [x] Technician management (add/remove/list)
- [x] Company admin assignment
- [x] Service area configuration
- [x] `/me/company` endpoint

### Compliance Domain
- [x] Building CRUD
- [x] Job lifecycle + state machine
- [x] LL152 form handling (create/update/submit)
- [x] LL152 validation service
- [x] Report versioning

### Email
- [x] Resend integration
- [x] Password reset email

### Infrastructure
- [x] Structured logging (pino)
- [x] Error handling middleware
- [x] **Feature-Centric Architecture** — "Split & Seal" packages (`@pcd/*`) for shared domain logic

---

## ⚠️ MVP (Upgrade Before Production)

- [ ] **Real PDF Generation** — Replace text placeholder with pdfkit + NYC DOB format
- [ ] **Report Storage** — Add S3/R2, upload PDFs, store real URLs
- [ ] **Refresh Token Revocation** — Store in DB, check `is_revoked`
- [ ] **Photo Upload Endpoint** — Implement route (schema exists)

---

## ⏳ Future

- [ ] Job notification emails (assigned, completed, report ready)
- [ ] SMS notifications (Twilio)
- [ ] Company matching algorithm
- [ ] Advanced reporting features
