# ADR 016: Dynamic Manifest Acquisition for Lore

## Status
Accepted

## Context
When analyzing the legacy `ghost/lore.py` codebase, we discovered a fatal deployment dependency.
**What we did before:** The script relied entirely on a manually curated folder of `.md` files residing at `data/lore/`. This folder was generated locally on one developer's PC. If a different developer cloned the repository, or if the system was deployed to a cloud server, the application would instantly crash because the `.md` files were missing. The app was physically tied to one machine.

To build a professional, deployable backend, we had to break free from this "PC-Bound" architecture.

## Options Evaluated
We evaluated three primary solutions to un-bind the lore data from the developer's PC:
1. **Option 1: Embed Files into Binary.** We could use a Rust build script (`build.rs`) to hardcode the `data/lore` text directly into the compiled `.exe`. (Rejected: Bloats the binary, impossible to push live lore updates without recompiling).
2. **Option 2: External Web APIs.** Rather than storing data, the backend could send HTTP requests to community APIs (like Ishtar Collective) whenever a user asked a question. (Rejected: Introduces third-party dependency risks and heavy network latency for RAG searches).
3. **Option 3: The Native Bungie Manifest.** The Bungie API exposes a public endpoint (`/Platform/Destiny2/Manifest/`) that allows any server to dynamically download an official SQLite database containing the `DestinyLoreDefinition` table.

## Decision
**What we are doing now:** We selected **Option 3**. We have completely deleted all references to the local `data/lore/` filesystem.

When the Ghost Companion backend boots up, the `crates/db/` adapter will automatically query Bungie, download the latest version of the official SQLite Manifest into a temporary directory if it isn't already cached, and extract the JSON lore properties from `DestinyLoreDefinition`. 

## Consequences
- **Positive:** Banishment of PC-Bound Dependencies. The application is now universally portable. Anyone can run a Docker container containing the API, and the system will natively establish its own knowledge base directly from Bungie upon startup.
- **Positive:** Zero Maintenance. As Destiny 2 adds new expansions and new lore, the bot will automatically update itself without any developer ever needing to copy/paste new `.md` files.
