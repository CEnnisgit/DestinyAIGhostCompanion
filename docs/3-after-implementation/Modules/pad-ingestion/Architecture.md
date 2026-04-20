# PAD Ingestion Architecture

The `pad-ingestion` app is a Rust-based CLI worker responsible for bootstrapping the building identity layer from NYC's Property Address Directory (PAD). This is **Pipeline A** — the foundational data source that all other pipelines build upon.

## System Components

```mermaid
graph TD
    CLI[CLI Args / main.rs] --> BBL_Load[BBL Cache Loader]
    CLI --> ADR_Pass1[ADR Pass 1: Tie-Breaking]
    CLI --> ADR_Pass2[ADR Pass 2: Address Streaming]

    BBL_Load --> BblTxt[bbl.txt / CSV]
    ADR_Pass1 --> AdrTxt[adr.txt / CSV]
    ADR_Pass2 --> AdrTxt

    BBL_Load --> BblCache[BblCache / HashMap]
    ADR_Pass1 --> Pipeline[pipeline.rs]
    Pipeline --> Models[models.rs]
    Pipeline -.-> ParseErrors[Parse Errors]

    subgraph Database Flush
        DB_Build[flush_buildings]
        DB_Anom[flush_anomalies]
        DB_Err[flush_parse_errors]
        DB_Addr[flush_addresses_streaming]
    end

    BblCache --> DB_Build
    Pipeline --> DB_Build
    Pipeline --> DB_Anom
    ParseErrors --> DB_Err
    ADR_Pass2 --> DB_Addr

    DB_Build --> Postgres[(Postgres DB)]
    DB_Anom --> Postgres
    DB_Err --> Postgres
    DB_Addr --> Postgres
```

## Ingestion Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User (CLI)
    participant M as main.rs
    participant P as pipeline.rs
    participant D as db.rs
    participant DB as Postgres

    U->>M: Start with bbl_file, adr_file, pad_version

    Note over M,P: Phase 1 — BBL Evidence Cache
    M->>P: build_bbl_cache(bbl.txt)
    P-->>M: BblCache (HashMap)

    Note over M,P: Phase 2 — ADR Processing & Tie-Breaking
    M->>P: process_adr_and_tiebreak(adr.txt)
    loop For each ADR row
        P->>P: Validate BIN (ERROR/INFO)
        P->>P: Validate BBL (WARN if invalid)
        P->>P: Tally BIN→BBL frequency
    end
    P->>P: Tie-break each BIN to primary BBL
    P-->>M: Vec of TieBreakerResult + ParseErrors

    Note over M,DB: Phase 3 — Database Flush
    M->>D: flush_buildings() [chunked upserts]
    D->>DB: Fetch existing buildings (batch)
    D->>D: Diff old vs new, build EventRows
    D->>DB: UPSERT buildings (QueryBuilder batch)
    D->>DB: INSERT building_events (if changed)

    M->>D: flush_anomalies()
    D->>DB: INSERT import_anomalies (BIN_MULTIPLE_BBLS)

    M->>D: flush_parse_errors()
    D->>DB: INSERT import_anomalies (all severities)
    D->>DB: INSERT quarantined_rows (ERROR only)

    Note over M,DB: Phase 4 — Address Streaming (2nd pass)
    M->>D: flush_addresses_streaming(adr.txt)
    D->>DB: DELETE stale addresses
    loop For each CSV chunk
        D->>D: Normalize street names
        D->>DB: INSERT building_addresses (batch)
    end
```

## Module Responsibilities

| Module | Responsibility |
| :--- | :--- |
| **main** | Orchestrates the multi-phase pipeline: CLI parsing, BBL cache load, tie-breaking, and four sequential DB flush operations. |
| **pipeline** | Pure domain logic: builds the BBL evidence cache, validates BINs/BBLs with three severity tiers, tallies BIN→BBL frequencies, and applies tie-breaking. |
| **db** | Batched database operations using `QueryBuilder`. Handles change detection, event logging, anomaly/quarantine writes, and streaming address inserts. |
| **models** | Strong typing: `Bin` VO (hard + soft validation), `Bbl` VO (10-digit canonical form), and CSV deserialization structs for `adr.txt` and `bbl.txt`. |
