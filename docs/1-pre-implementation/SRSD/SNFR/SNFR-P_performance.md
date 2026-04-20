# Non-Functional Requirements: Performance (SNFR-P)

## Response Time (SNFR-PRT)
- **`SNFR-PRT-01`**: End-to-end voice intent execution (Speech → STT → Intent → API → Equip) must complete in under 3.5 seconds to feel responsive and comparable to an in-game Ghost.
- **`SNFR-PRT-02` (Rate Limiting Delay)**: If the Bungie API throttles a request (HTTP 429), the system must backoff and retry seamlessly, ensuring the user is informed of the delay rather than hard-failing the interaction.

## Throughput (SNFR-PT)
- **`SNFR-PT-01`**: The local application must support continuous open-mic parsing without leaking memory or degrading system performance during hours-long gaming sessions.
