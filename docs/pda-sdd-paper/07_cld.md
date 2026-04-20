# §4.3.4: Change Log Document (CLD)

The CLD meticulously chronicles the evolution of the entire project — modifications, additions, and accomplishments across SRSD, DDD, and source code.

## Structure

```
CLD
├── Feature 1 (maps to SGI-MF main function)
│   ├── Log <Auto-Incremented>
│   │   ├── 1. Significance
│   │   ├── 2. Results
│   │   ├── 3. Date
│   │   ├── 4. Change Summary
│   │   ├── 5. Detailed Changes
│   │   ├── 6. References
│   │   ├── 7. Issue Tracking System
│   │   └── 8. Author
│   ├── Log <Auto-Incremented>
│   └── Log <Auto-Incremented>
│
├── Feature 2
├── Feature 3
└── Feature n
```

## Organization

The CLD is organized into **distinct sections, each corresponding to a primary function** outlined in the SRSD (beginning with SGI-MF). The number of CLD sections directly aligns with the number of main functions specified in the SRSD.

## Log Entry — 8 Required Fields

Each log entry comprises eight essential elements:

| # | Field | Description |
|---|-------|-------------|
| 1 | **Significance** | Major or Minor + domain classification (Requirements, Design, or Code) |
| 2 | **Results** | Outcome: Success, Failure, or Approved Modification |
| 3 | **Date** | Date and time of the activity |
| 4 | **Change Summary** | Brief summary of what changed |
| 5 | **Detailed Changes** | Full details of the activity |
| 6 | **References** | Links to relevant SRSD requirements |
| 7 | **Issue Tracking** | Ticket number (if electronic ticketing is used) |
| 8 | **Author** | Name of the individual who performed or recorded the activity |
