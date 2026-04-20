# Non-Functional Requirements: Maintainability (SNFR-M)

## Modular Isolation (SNFR-MM)
- **`SNFR-MM-01`**: The codebase must rigidly abide by Vertical Slices isolating `/auth`, `/inventory`, and `/chat`. This ensures that a Bungie API schema change does not break the LLM inference prompt constructions.

## Portability (SNFR-MP)
- **`SNFR-MP-01` (Executable Bundling)**: The application architecture must support being frozen via PyInstaller into a single `ghost_companion.exe`.
- **`SNFR-MP-02`**: The desktop distribution should bundle the pre-built React Single Page Application (SPA) inside the `.exe` static folder to eliminate the requirement for the end-user to install `Node.js` locally.
