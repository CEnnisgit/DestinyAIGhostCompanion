# General Information: Objectives (SGI-OJ)

## 1. Primary Objectives
1. **Reduce Friction**: Eliminate the need to use a second screen, a smartphone, or pause gameplay to swap gear during intense encounters.
2. **Increase Immersion**: Maintain the in-universe illusion by allowing players to converse with their "Ghost" directly using natural language.
3. **Ensure Zero-Cost Scalability**: By designing the LLM inference architecture around local models (Ollama), the product ensures zero continuous API costs for the end-user while maximizing privacy.

## 2. Success Metrics
- End-to-end voice intent execution (Speech → STT → Intent → API → Equip) completes reliably.
- Accurate identification of "fuzzy" item names (e.g. "Equip sunshot" resolving faithfully to "Sunshot" hand cannon).
- Seamless error handling in the case of Bungie.net downtime, ensuring the application fails gracefully without crashing.
