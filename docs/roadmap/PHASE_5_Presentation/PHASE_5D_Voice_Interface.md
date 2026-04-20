# Phase 5D: Voice Interface

> **Status:** 🔲 Not Started
> **Objective:** Implement microphone capture using the Web Speech API and stream transcribed text to the Rust backend via WebSocket.
> **Location:** `apps/desktop/src/`
> **Depends On:** Phase 5C (authenticated session), Phase 4C (WebSocket server)

---

## Context for the Agent

The Rust backend (Phase 4C) exposes:
- `GET /ws/voice` — Upgrades to a WebSocket connection.
- **Inbound:** `{ "text": "equip my Sunshot" }`
- **Outbound:** `{ "response": "Done! Sunshot equipped.", "intent": "equip_item" }`

Per the project's `AGENTS.md`:
> Voice mode should stay functional even when no server-side STT/TTS provider is configured. Browser speech capture and browser speech synthesis are the baseline fallback.

Your job is to build the voice capture UI using the **Web Speech API** as the baseline, with an optional fallback to typed text.

## Deliverables

### 1. `apps/desktop/src/hooks/useWebSocket.ts`
A custom React hook managing a persistent WebSocket connection:
```typescript
interface UseWebSocketReturn {
  isConnected: boolean;
  sendMessage: (text: string) => void;
  lastMessage: GhostResponse | null;
  error: string | null;
}
```
- Connect to `VITE_WS_URL` on mount.
- Auto-reconnect with exponential backoff on disconnect (1s, 2s, 4s, max 30s).
- Include the auth session token in the WebSocket handshake query params.

### 2. `apps/desktop/src/hooks/useSpeechRecognition.ts`
A custom React hook wrapping the Web Speech API:
```typescript
interface UseSpeechRecognitionReturn {
  isListening: boolean;
  transcript: string;
  startListening: () => void;
  stopListening: () => void;
  isSupported: boolean;
}
```
- Use `webkitSpeechRecognition` or `SpeechRecognition` (browser-native).
- Set `continuous = false` and `interimResults = true`.
- On `onresult`, capture the final transcript and automatically send it via the WebSocket hook.
- Handle `onerror` gracefully — if the browser doesn't support speech recognition, set `isSupported = false` and fall back to typed text.

### 3. `apps/desktop/src/hooks/useSpeechSynthesis.ts`
A custom React hook for text-to-speech (Ghost speaking back):
```typescript
interface UseSpeechSynthesisReturn {
  speak: (text: string) => void;
  isSpeaking: boolean;
  cancel: () => void;
}
```
- Use `window.speechSynthesis` (browser-native).
- Select a voice that sounds appropriate — prefer English voices with a slightly robotic tone.
- When a Ghost response arrives via WebSocket, automatically speak it.

### 4. `apps/desktop/src/components/VoiceButton.tsx`
A large, circular, animated microphone button:
- **Idle state:** Subtle glow using `--accent` color. Ghost mark icon in center.
- **Listening state:** Pulsing ring animation (accent blue → gold). Microphone icon appears.
- **Processing state:** Spinning/loading animation while waiting for the WebSocket response.
- **Speaking state:** Sound wave animation while the Ghost speaks back.
- Click to toggle listening on/off.
- Show the live transcript text below the button as the user speaks.

### 5. `apps/desktop/src/components/VoicePanel.tsx`
The main voice interaction area:
- Large `VoiceButton` centered.
- Live transcript display below.
- Last Ghost response displayed with fade-in animation.
- A small text input below for manual typing when voice isn't available.
- Status indicator showing WebSocket connection state.

### 6. Integration with `AppLayout`
Add a tab or toggle in the main layout to switch between:
- **Chat Mode** (text-based, from Phase 5F)
- **Voice Mode** (this phase)

## Browser Compatibility
- Chrome/Edge: Full Web Speech API support.
- Firefox: No built-in speech recognition. Fall back to typed input.
- Electron: Uses Chromium, so full support.

## Verification
- [ ] Click the voice button → browser requests microphone permission.
- [ ] Speak "hello Ghost" → transcript appears below the button.
- [ ] Transcript is sent via WebSocket → Ghost response appears and is spoken aloud.
- [ ] If the browser doesn't support speech recognition, the text input fallback is visible.
- [ ] WebSocket auto-reconnects after the backend restarts.

## ADR References
- **ADR 008**: Voice AI Failover Circuit — the backend handles failover, but the frontend must also handle WebSocket disconnects gracefully.

## Next Phase
Once verified, proceed to → [Phase 5F: Lore Chat](./PHASE_5F_Lore_Chat.md)
