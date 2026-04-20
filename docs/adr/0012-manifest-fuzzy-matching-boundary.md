# ADR 012: Manifest Fuzzy-Matching Boundary

## Status
Accepted

## Context
When a user speaks a command via Voice AI (e.g., "Equip Sun sht"), the Voice AI intent parser generates a literal text string string attempting to represent the item. The `inventory` domain is responsible with querying an external Bungie Manifest to translate that user text into a strict `DestinyItemHash` (an integer).

The architectural question was: *Who is responsible for spell-checking and fuzzy-matching this string?*
1. **Option A:** The `inventory` Domain implements Levenshtein Distance/Jaro-Winkler algorithms and parses the database itself.
2. **Option B:** The `crates/db/` adapter implementation handles the algorithm internally.

## Decision
We will employ **Option B**. The pure `inventory` domain will be mathematically rigid and "dumb." It will blindly call `ManifestDatabasePort::resolve_item_hash("Sun sht")`. 

The implementation of that port (which will physically live in the `crates/db/` directory where the `.sqlite` manifest is cached in-memory) will solely own the responsibility of employing string similarity algorithms (`strsim`) to confidently resolve typos into the correct primary key Hash. 

## Consequences
- **Positive:** Pristine separation of concerns. The Domain layer is entirely free from text-parsing logic or holding the entire 30,000 item manifest array in memory.
- **Negative:** The `db` adapter must take on the computational overhead of string matching, making it slightly more complex than a standard SQL repository.
