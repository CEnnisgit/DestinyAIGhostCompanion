---
description: How to log a feature completion in the CLD directory.
---

# Feature Logging Workflow

Run this workflow when you **complete a feature** or a **significant change**.

## Steps

1.  **Identify the Feature**
    - Check `docs/2-during-implementation/CLD/README.md` for existing features.
    - If your feature exists (e.g., `JOB_MANAGEMENT`), use that folder.
    - If new, create `docs/2-during-implementation/CLD/<FEATURE_NAME>/CHANGELOG.md`.

2.  **Append to the Feature Log**
    - Target File: `docs/2-during-implementation/CLD/<FEATURE_NAME>/CHANGELOG.md`
    - Use `write_file_content` (or read then replace) to **prepend** or **append** the new log.
    - **Format:**
      ```markdown
      ### Log <NNN>: <Title>
      - **Significance:** [Major/Minor] [Req/Design/Code]
      - **Date:** <YYYY-MM-DD>
      - **Author:** Antigravity
      - **Summary:** <One-line summary>
      - **Detailed Changes:**
          - <Bulleted list of changes>
      - **References:** <User Stories (e.g. US-01), specific files>
      - **Result:** Success
      ```

3.  **Verify Traceability**
    - Ensure you referenced the User Story ID from `USER_STORIES.md`.

4.  **Commit**
    - Commit the change log update along with your code changes.
