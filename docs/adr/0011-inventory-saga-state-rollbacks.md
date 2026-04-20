# ADR 011: Graceful Inventory Saga Error Yielding

## Status
Accepted

## Context
In the legacy Python orchestrator (`ghost/assistant.py`), an inventory command like *"Equip 3 Kinetic weapons"* was highly brittle. If the script successfully moved Weapon 1 and Weapon 2, but Weapon 3 failed because the in-game Vault was completely full, the Python script simply threw an unhandled Exception and crashed. 

**The Senior System Architect Complaint:**
"This is wildly hostile to the user. You cannot call it an `EquipItemSaga` if it does not actually implement a Saga pattern. If a multi-step workflow fails 60% of the way through, the backend cannot just crash silently, leaving the user's game state corrupted and half-equipped without giving them any feedback. Sagas must gracefully handle mid-flight errors."

## Decision
We will implement **Graceful Error Yielding** inside `crates/domain/src/inventory/saga.rs` (deprecating raw panic patterns).
Because perfect, automated state-rollbacks (e.g., attempting to precisely undo 3 weapon transfers) in Destiny is inherently risky (due to slot capacities dynamically changing), the orchestrator will instead heavily rely on structured user feedback. 

If the Saga succeeds in Steps 1 and 2, but hits an `Err(Vault Full)` at Step 3, the Saga will:
1. Not crash.
2. Halt any further execution.
3. Yield a strict, strongly-typed Error String back to the `crates/api/` driver: *"Successfully equipped Weapon 1 and Weapon 2, but failed to equip Weapon 3 because your Vault is full."*

## Consequences
- **Positive:** The Ghost Companion becomes a hyper-reliable enterprise application. The user receives exact, conversational context of *why* their command partially failed, mirroring actual in-game Destiny 2 mechanics.
- **Negative:** The Saga return types become significantly more complex, requiring careful `Result<_, PartialSagaFailure>` mapping.
