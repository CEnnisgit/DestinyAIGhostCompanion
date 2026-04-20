# Saga Root: EquipItemSaga

**Module Path:** `crates/domain/src/inventory/saga.rs`

## Description
The strict Destiny 2 logic state machine orchestrating physical inventory manipulation.

## Core Process Flow
This file perfectly solves the legacy python architecture bugs using two ADR parameters:
1. **ADR 010 (Strict Serial Mutations):** The Saga completely avoids `futures::join_all!` concurrency, physically awaiting every single Bungie API sequence step to guarantee the Edge Network does not rate-limit or lock the transaction.
2. **ADR 011 (Graceful Error States):** Rather than crashing when the in-game Vault is full midway through a sequence, the Saga intercepts the exact point of failure and builds a highly-contextual string returning exactly why the sequence failed, preventing game-state corruption.
