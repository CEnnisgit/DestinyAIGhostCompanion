# Archive

This directory contains legacy code from the original Python monolith (pre-Rust migration).

These files are preserved for reference only. **Do not import, depend on, or execute any code in this directory.**

## Contents

| Folder | What It Contains |
|:-------|:-----------------|
| `legacy-python/` | The original `ghost/` Python package (assistant.py, auth.py, bungie.py, lore.py, etc.) |
| `legacy-root/` | Root-level Python scripts (server.py, launch.py, generate_dataset.py) and old deployment configs (Dockerfile, render.yaml) |
| `legacy-frontend/` | The original Create React App frontend |
| `legacy-webapp/` | The standalone `index.html` with the Destiny design system (CSS tokens will be harvested in Phase 5B) |
| `legacy-ios/` | An experimental iOS Swift app |
| `legacy-tests/` | Python pytest suite for the old server |

## Why Keep This?
- **Phase 5B** will harvest CSS design tokens from `legacy-webapp/index.html`.
- The `bungie_api_reference.json` in the root is still actively used by the new Rust crates.
- Historical reference for understanding the old architecture.
