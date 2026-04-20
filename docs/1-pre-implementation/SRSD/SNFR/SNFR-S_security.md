# Non-Functional Requirements: Security (SNFR-S)

## Token Lifecycle Management (SNFR-STL)
- **`SNFR-STL-01`**: The system must never expose the raw OAuth `Bearer` token or `Refresh` token to the client-side UI layers (React/iOS). The tokens must remain locked in the Python backend execution space.
- **`SNFR-STL-02`**: If a refresh token expires (requiring a hard re-authentication), the backend must signal an exact `UNAUTHORIZED_FLOW_REQUIRED` HTTP status to the frontend to prompt the user to re-link their Bungie account.

## Data Privacy (SNFR-SDP)
- **`SNFR-SDP-01`**: Voice recordings and text transcripts must not be sent to external telemetry servers. If Ollama is used, all user conversations must securely remain exclusively on the `localhost` loopback.
