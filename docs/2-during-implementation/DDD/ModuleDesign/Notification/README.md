# NotificationModule

> **Source of Truth:** [`apps/backend/src/modules/notifications`](file:///c:/github/pcd/apps/backend/src/modules/notifications)
> **Scope:** [Pilot Core (LL152) - Supporting](file:///c:/github/pcd/docs/PILOT_SCOPE_CONTEXT.md)

## Traceability

> **Refer to:** [TraceabilityMatrix_SFR.md](../../Traceability/TraceabilityMatrix_SFR.md)

- **Primary Responsibility**: Transactional Emails (`SFR-BRW-*`) and Reminders.
- **Key Requirements**:
  - `SFR-BRW-10`: Dispatch Notification (Technician).
  - `SFR-BRW-11`: Submission Notification (LMP).
  - `SFR-BRW-13`: Deadline Reminder.

## Module Responsibilities

1. **Email Delivery**: Sending transactional emails via SendGrid/SMTP.
2. **Templating**: Hydrating job data into email templates.

## Module Structure

- **Package**: `apps/backend/src/modules/notifications` works with `job-dispatch` events.

## Module Interactions

- **Consumes**: Domain Events from `Jobs` (`JobDispatched`, `JobSubmitted`).
- **Produces**: External Email API calls.

## Algorithm Descriptions

- **Retry Logic**: Exponential backoff for failed email deliveries.
- **Template Rendering**: Hydrating Handlebars/HTML templates.

## Data Structure Selection

- **Queue**: Background job queue (BullMQ/Redis) for reliability.
