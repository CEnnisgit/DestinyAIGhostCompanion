# Functional Requirements: Processing (SFR-PR)

## Data Processing (SFR-PRDP)
- **`SFR-PRDP-01` (Dataset Generation)**: The system supports dedicated pipelines for structuring and generating instructional datasets to fine-tune local models on Destiny logic.
- **`SFR-PRDP-02` (Item Name Resolution)**: The system must perform fuzzy-matching string resolution against the Destiny Manifest to translate spoken phrases ("equip sun bucket") to exact item hashes ("Sunshot").
- **`SFR-PRDP-03` (Item Location Resolution)**: The system must scan the master profile response to locate the target `instanceId` across all characters, vault space, and postmaster allocations.
- **`SFR-PRDP-04` (Lore Data Retrieval)**: The system must extract contextual strings from the Bungie Manifest lore definitions when constructing inputs for conversational LLM queries.

## Complex Calculations/Algorithms (SFR-PRC)
- **`SFR-PRC-01` (Speech-to-Text)**: Audio bytes captured from the client must be transcribed into raw text using local or browser-fallback STT algorithms.
- **`SFR-PRC-02` (Persona Prompt Construction)**: The system must format the final prompt supplied to the LLM interface by aggregating the selected Persona system prompt, the immediate user transcript, and any fetched inventory state data.
- **`SFR-PRC-03` (Browser Speech Fallback)**: The front-end clients must implement native `SpeechRecognition` and `SpeechSynthesis` Web APIs as a fallback when server-side STT/TTS modules are unavailable.

## Data Manipulation (SFR-PRDM)
- **`SFR-PRDM-01` (Intent Classification)**: The intent parser must confidently categorize a transcribed user query into either an "Actionable Matrix" (Equip/Vault) or a "Conversational Matrix" (Lore inquiry/Jokes).
- **`SFR-PRDM-02` (Intent-to-Payload Translation)**: Actionable matrix intents must be converted directly into structured parameter sets suitable for the Inventory Execution Module.
