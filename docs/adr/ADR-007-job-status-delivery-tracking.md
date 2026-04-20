# ADR-007: JobStatus Unchanged; Delivery Tracked on Report

**Status**: Accepted  
**Date**: 2025-12-15

## Context

The redesign spec proposed adding `REPORT_READY` status and redefining `COMPLETED` to mean "report email sent." This would require migrating all existing COMPLETED jobs and changing the semantic meaning of a core status.

The PRD and domain flows treat "job completed" as technician submission, while report delivery may be manual or automatic.

## Decision

**Keep `InspectionJob.status = COMPLETED` meaning "inspection submitted."**

Track report delivery via `InspectionReport` fields:
- `sent_at TIMESTAMPTZ`
- `sent_to_email TEXT`
- `sent_by_user_id UUID`
- `delivery_channel TEXT`

Derived operational states:
- **Email Pending** = `COMPLETED AND report.sent_at IS NULL`
- **Operationally Done** = `COMPLETED AND report.sent_at IS NOT NULL`

## Consequences

- No breaking change to job status enum
- No migration of historical job statuses required
- Dashboard must surface "Completed + Email Pending" as first-class attention condition
- Sending a report does NOT transition job status
- Command Center "Ready to Send" queue uses: `COMPLETED + report exists + sent_at NULL`
