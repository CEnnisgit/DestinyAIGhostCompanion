# Event History — Query Guide

Practical queries for reading from the three event tables. Useful for debugging, auditing, and future UI features.

## Building Events

### Recent changes for a specific building

```sql
SELECT event_type, changed_fields, created_at
FROM building_events
WHERE bin = '1056789'
ORDER BY created_at DESC
LIMIT 20;
```

### All buildings created in the latest PAD import

```sql
SELECT bin, changed_fields, created_at
FROM building_events
WHERE event_type = 'PAD_UPDATE_25A'
  AND changed_fields->>'action' = 'CREATED'
ORDER BY created_at;
```

### Buildings where primary BBL changed

```sql
SELECT bin,
       changed_fields->'primary_bbl'->>'old' AS old_bbl,
       changed_fields->'primary_bbl'->>'new' AS new_bbl,
       created_at
FROM building_events
WHERE changed_fields ? 'primary_bbl'
ORDER BY created_at DESC;
```

### Count of changes per PAD version

```sql
SELECT event_type, COUNT(*) AS event_count
FROM building_events
GROUP BY event_type
ORDER BY event_type;
```

---

## Obligation Events

### Obligations deactivated in the latest import

```sql
SELECT oe.obligation_id, co.bin, co.program_code, co.cycle_key,
       oe.old_value, oe.new_value, oe.occurred_at
FROM obligation_events oe
JOIN compliance_obligations co ON co.id = oe.obligation_id
WHERE oe.event_type = 'ROSTER_STATUS_CHANGED'
ORDER BY oe.occurred_at DESC
LIMIT 50;
```

### Deactivation history for a specific building

```sql
SELECT oe.*, co.cycle_key, co.subcycle
FROM obligation_events oe
JOIN compliance_obligations co ON co.id = oe.obligation_id
WHERE co.bin = '1056789'
ORDER BY oe.occurred_at DESC;
```

### Import run summary (how many obligations were deactivated per run)

```sql
SELECT import_run_id, COUNT(*) AS deactivated
FROM obligation_events
WHERE event_type = 'ROSTER_STATUS_CHANGED'
GROUP BY import_run_id
ORDER BY MIN(occurred_at) DESC;
```

---

## Job Events

### Full event history for a job

```sql
SELECT event_type, payload, actor_user_id, created_at
FROM job_events
WHERE job_id = '<uuid>'
ORDER BY created_at;
```

### Recent activity across all jobs

```sql
SELECT je.event_type, je.payload->>'job_number' AS job_number,
       je.actor_user_id, je.created_at
FROM job_events je
ORDER BY je.created_at DESC
LIMIT 50;
```

### Jobs started and completed (measure turnaround)

```sql
SELECT
    s.job_id,
    s.created_at AS started_at,
    c.created_at AS completed_at,
    c.created_at - s.created_at AS duration
FROM job_events s
JOIN job_events c ON c.job_id = s.job_id AND c.event_type = 'JOB_COMPLETED'
WHERE s.event_type = 'JOB_STARTED'
ORDER BY s.created_at DESC;
```

### Cancellation reasons

```sql
SELECT payload->>'cancellation_reason' AS reason,
       payload->>'previous_status' AS was_in_status,
       created_at
FROM job_events
WHERE event_type = 'JOB_CANCELED'
ORDER BY created_at DESC;
```
