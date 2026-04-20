# Functional Requirements: Input/Output (SFR-IO)

## Data Entry (SFR-IODE)
- **`SFR-IODE-01`**: The system must capture raw microphone audio from the user through the active client interface (React, iOS, or Webapp).
- **`SFR-IODE-02`**: The system must accept natural language voice commands to equip specific items (e.g., "Ghost, equip my Sunshot").
- **`SFR-IODE-03`**: The system must accept natural language voice commands to vault specific items (e.g., "Ghost, put this hand cannon in the vault").
- **`SFR-IODE-04`**: The system must allow users to select or switch the active AI Persona via the client interface.

## Data Output (SFR-IODO)
- **`SFR-IODO-01`**: The system must output audio using a Text-to-Speech (TTS) engine, emulating the Ghost persona.
- **`SFR-IODO-02`**: The system must confirm the success or failure of all Bungie API execution workflows (Equipping/Vaulting) back to the user contextually.
- **`SFR-IODO-05`**: All textual and verbal outputs must be strictly styled according to the actively selected AI Persona prompt.
- **`SFR-IODO-06`**: The system must retrieve and output Destiny universe lore context when the user asks an open-ended narrative question.
