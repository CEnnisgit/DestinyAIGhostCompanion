# Hexagonal Ports

**Module Path:** `crates/domain/src/inventory/ports.rs`

## 1. BungieInventoryPort (Secondary/Driven)
Represents the raw execution endpoints of the Bungie API, completely stripped of any `.reqwest` logic or URL formation properties. It simply expects a `BungieMembershipId` and `DestinyItemHash`, and executes the strict mutation.

## 2. ManifestDatabasePort (Secondary/Driven)
As defined in **ADR 012**, this port pushes the complexity of Fuzzy String Matching (e.g. converting "Sun sht" to a Sunshot Hash integer) out of the Domain and assigns it to the `.sqlite` database implementations.
