# design/GPS1_FIELD_SPEC.md

> **Status:** Draft / TBD
> **Source:** GAP-01 from PRD Extraction

## Overview
This document will define the exact field mapping for the GPS1 Gas Piping System Inspection Report.

## Required Fields (Preliminary from PRD)
- **Job Header:**
  - Address
  - BIN / Block / Lot
  - Community District
  - Owner Contact Info
  - Access Notes

- **Inspection Findings:**
  - [TBD] List of specific gas piping conditions
  - [TBD] List of boolean checks (Pass/Fail/NA)

- **Attachments:**
  - Meter Room Photo
  - Boiler Room Photo
  - Defect Photos (if applicable)

## TODO
- [ ] Obtain official NYC DOB GPS1 PDF form.
- [ ] Map every input field to a JSON schema property.
- [ ] Define validation rules for each field.
