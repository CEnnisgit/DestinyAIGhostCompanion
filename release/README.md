# Release Packaging

Use this folder to keep production artifacts separate from the development workflow. Everything generated for a GitHub release is staged under `release/artifacts/`, leaving `dist/`, `frontend/`, and your local `.env` untouched.

## Prerequisites
- Python environment with project dependencies installed (`pip install -r requirements.txt`)
- `pyinstaller` available on `PATH`
- Node.js + npm for building the React frontend

## Build & Package (GitHub-ready)
1. From the repo root, run:
   ```bash
   python tools/build_release.py --version 0.1.0 --overwrite
   ```
   - Add `--launcher-only` or `--desktop-only` if you want a single target.
   - Add `--skip-build` to repackage existing `dist/` outputs without rebuilding.
2. Find artifacts in `release/artifacts/v0.1.0/`:
   - `GhostCompanionLauncher-v0.1.0.zip` (backend + web UI)
   - `GhostCompanion-v0.1.0.zip` (desktop app)
   - `SHA256SUMS.txt` and `RELEASE-NOTES.txt`
3. Upload the zip files to a GitHub Release. The staged folders remain in the same directory for code signing or final inspection.

## Notes
- The `.env` file is never bundled; the app prompts for missing values at first launch and saves them next to the executable.
- Re-running with a different version tag writes to a new `release/artifacts/vX.Y.Z/` directory (use `--overwrite` to replace an existing one).
