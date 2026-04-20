# Command Center Acceptance Tests

> Test stack: **Vitest** with mocked repositories  
> Option B: `COMPLETED` = inspection submitted, delivery tracked on report

---

## Canonical Definitions

```typescript
// Email Pending
const isEmailPending = (job, report) =>
  job.status === 'COMPLETED' && report && report.sent_at === null;

// Operationally Done
const isOperationallyDone = (job, report) =>
  job.status === 'COMPLETED' && report && report.sent_at !== null;

// No-show (15 min grace)
const isNoShow = (job, form, now) =>
  job.status === 'SCHEDULED' &&
  now > new Date(job.scheduled_end).getTime() + 15 * 60 * 1000 &&
  (!form || !['IN_PROGRESS', 'COMPLETED'].includes(form.status));

// Report missing (5 min after form completed)
const isReportMissing = (form, report, now) =>
  form.status === 'COMPLETED' &&
  !report &&
  now > new Date(form.submitted_at).getTime() + 5 * 60 * 1000;
```

---

## A. Queue Computation Tests

### A1. noShow Queue

```typescript
describe('noShow queue', () => {
  it('A1.1 - appears after grace period', async () => {
    // scheduled_end = now - 16 min, no form
    // → appears in queues.noShow
  });

  it('A1.2 - does not appear before grace', async () => {
    // scheduled_end = now - 14 min
    // → NOT in queues.noShow
  });

  it('A1.3 - started form suppresses noShow', async () => {
    // overdue but form.status = IN_PROGRESS
    // → NOT in queues.noShow
  });

  it('A1.4 - completed form suppresses noShow', async () => {
    // overdue but form.status = COMPLETED
    // → NOT in queues.noShow
  });
});
```

### A2. reportMissing Queue

```typescript
describe('reportMissing queue', () => {
  it('A2.1 - appears after 5 minutes', async () => {
    // form.status = COMPLETED, submitted_at = now - 6 min, no report
    // → appears in queues.reportMissing
  });

  it('A2.2 - does not appear before 5 minutes', async () => {
    // submitted_at = now - 4 min
    // → NOT in queues.reportMissing
  });

  it('A2.3 - report exists suppresses', async () => {
    // report exists for form_id
    // → NOT in queues.reportMissing
  });
});
```

### A3. readyToSend Queue (Email Pending)

```typescript
describe('readyToSend queue', () => {
  it('A3.1 - COMPLETED + report exists + sent_at null', async () => {
    // → appears in queues.readyToSend
  });

  it('A3.2 - emailed suppresses', async () => {
    // sent_at IS NOT NULL
    // → NOT in queues.readyToSend
  });
});
```

### A4. flagged Queue

```typescript
describe('flagged queue', () => {
  it('A4.1 - open flag appears', async () => {
    // flag.resolved_at IS NULL
    // → appears in queues.flagged
  });

  it('A4.2 - resolved flag does not appear', async () => {
    // flag.resolved_at IS NOT NULL
    // → NOT in queues.flagged
  });
});
```

---

## B. API Contract Tests

```typescript
describe('GET /command-center', () => {
  it('B1 - response shape', async () => {
    // expect: queues { noShow, reportMissing, readyToSend, flagged }
    // expect: kpis { ... }
  });

  it('B2 - company scoping', async () => {
    // company A admin sees only company A jobs
  });
});
```

---

## C. Action Tests

```typescript
describe('POST /reports/:id/send', () => {
  it('C1 - sets sent_at, clears readyToSend, job stays COMPLETED', async () => {
    // job.status must remain COMPLETED
  });

  it('C2 - returns 409 if already sent', async () => {
    // idempotency check
  });
});

describe('POST /jobs/:id/report/regenerate', () => {
  it('D1 - removes from reportMissing, adds to readyToSend', async () => {
    // after regeneration
  });
});
```

---

## Pre-flight Regression Check

```typescript
describe('Option B consistency', () => {
  it('JobStatus enum does NOT contain REPORT_READY', () => {
    // grep schema or import enum
  });
});
```
