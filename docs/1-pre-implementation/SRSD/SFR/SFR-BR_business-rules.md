# Functional Requirements: Business Rules (SFR-BR)

## Hard Constraints (SFR-BRC)
- **`SFR-BRC-01` (Dismantle Action Prohibition)**: **CRITICAL.** The system must absolutely never generate or execute an API payload that results in the dismantling or deletion of an item.
- **`SFR-BRC-02` (Resource Spending Prohibition)**: The system must never execute vendor requests, bounty acquisitions, or any workflow that requires the spending of in-game currencies.
- **`SFR-BRC-03` (Subclass Editing Exclusion)**: Modifying subclasses, aspects, or fragments is currently out of scope and must be rejected by the intent parser.
- **`SFR-BRC-04` (Mod Socketing Exclusion)**: Socketing armor or weapon mods is out of scope and must be rejected.
- **`SFR-BRC-06` (AI-to-API Isolation Boundary)**: **CRITICAL.** The LLM must never have direct code-execution access to the Bungie.net SDK wrapper. The LLM must output a JSON intent, which is statically validated by a separate Inventory action executor module.

## Workflow Rules (SFR-BRW)
- **`SFR-BRW-01` (Transfer Workflow)**: If a requested item is not on the active character, the system must first execute a transitive transfer workflow (Character -> Vault -> Active Character) before attempting to equip.
- **`SFR-BRW-02` (Equip Workflow)**: Once an item is validated as being in the active character's inventory layout, the system may execute the EquipItem payload safely.
- **`SFR-BRW-03` (Vault Transfer Workflow)**: Vaulting an item requires validating its presence on the active character before executing the TransferToVault payload.
- **`SFR-BRW-04` (Postmaster Overflow Workflow)**: If an item resides in the postmaster, it must be successfully pulled to character inventory before any subsequent equip or vault actions can complete.
- **`SFR-BRW-05` (Cross-Character Un-Equip Constraint)**: Items currently actively equipped on an alternate character cannot be moved. They must first be explicitly unequipped (swapped with a placeholder) before the transfer workflow can begin.

## Validation Status (SFR-BRV)
- **`SFR-BRV-01`**: System must validate the precise `itemHash` and `instanceId` from the active profile payload before initiating any movement actions.
