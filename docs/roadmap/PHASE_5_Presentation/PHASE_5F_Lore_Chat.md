# Phase 5F: Lore Chat

> **Status:** 🔲 Not Started
> **Objective:** Build the conversational AI chat panel where users ask the Ghost questions and receive lore-grounded, RAG-powered answers.
> **Location:** `apps/desktop/src/`
> **Depends On:** Phase 5D (WebSocket + voice hooks), Phase 4E (Lore RAG pipeline)

---

## Context for the Agent

The Rust backend (Phase 4E) provides:
- `VoiceIntent::LoreQuery { topic }` → triggers the `LoreSaga` which fetches semantic lore context from Postgres via `pgvector` and generates an AI response.
- The WebSocket returns: `{ "response": "The Last City is...", "intent": "lore_query" }`

The legacy `webapp/index.html` already contains a fully functional chat interface with:
- User bubbles (blue gradient), Ghost bubbles (dark with gold border), System bubbles (red for errors).
- Quick-action chips for preset prompts.
- Persistent transcript in localStorage.
- A composer (textarea + submit button).

Your job is to build the final React chat panel by combining the legacy design with the live WebSocket connection.

## Deliverables

### 1. `apps/desktop/src/components/chat/ChatMessage.tsx`
Renders a single chat message using the `ChatBubble` component from Phase 5B:
```typescript
interface ChatMessageProps {
  role: 'user' | 'ghost' | 'system';
  content: string;
  intent?: string;    // e.g., "lore_query", "equip_item", "greeting"
  timestamp: Date;
}
```
- Ghost messages with `intent: "lore_query"` should display a small "📖 Lore" badge.
- Ghost messages with `intent: "equip_item"` should display a small "⚔️ Inventory" badge.
- Messages animate in with the `rise` keyframe.

### 2. `apps/desktop/src/components/chat/ChatPanel.tsx`
The full chat container:
- Scrollable message list with auto-scroll to bottom on new messages.
- Quick-action chips at the top (preset lore prompts):
  - "Tell me about the Traveler"
  - "Who is Savathûn?"
  - "Explain the Darkness"
  - "What happened in the Red War?"
- The `Composer` component at the bottom (from Phase 5B).
- Typing indicator: When the Ghost is processing, show a pulsing "Ghost is thinking..." animation.

### 3. `apps/desktop/src/hooks/useChatHistory.ts`
A custom React hook managing chat state:
```typescript
interface UseChatHistoryReturn {
  messages: ChatMessageProps[];
  addUserMessage: (text: string) => void;
  addGhostMessage: (text: string, intent: string) => void;
  addSystemMessage: (text: string) => void;
  clearHistory: () => void;
}
```
- Persist to `localStorage` (key: `ghost-chat-history`).
- Limit stored history to the last 100 messages to prevent storage bloat.

### 4. `apps/desktop/src/pages/ChatPage.tsx`
The full chat experience page:
- `ChatPanel` as the main content area.
- Voice button (from Phase 5D) integrated — users can speak OR type.
- Mode toggle: "Voice Mode" vs "Text Mode".
- In Voice Mode, the `VoiceButton` is prominent and the text composer is minimized.
- In Text Mode, the full composer is shown and voice button is a small icon.

### 5. Integration: Unified Message Flow
Both voice and text input should follow the same pipeline:
1. User speaks or types → text is captured.
2. Text is sent via WebSocket: `{ "text": "..." }`.
3. Ghost response arrives: `{ "response": "...", "intent": "..." }`.
4. Response is added to chat history and (optionally) spoken aloud.
5. If intent is `equip_item`, the inventory UI can optionally update.

### 6. Navigation
Add tabs or a sidebar to the `AppLayout` for switching between:
- 🗨️ **Chat** (this page)
- 🎒 **Inventory** (Phase 5E)
- ⚙️ **Settings** (runtime config — API keys, voice preferences)

## Design Constraints
- The chat must feel like talking to a real Destiny Ghost — warm, slightly formal, helpful.
- Use the Ghost mark icon as the avatar for Ghost messages.
- Quick-action chips should have a subtle hover glow animation.
- The typing indicator should use the Ghost's accent color (`--accent`) with a pulsing opacity.
- Preserve the legacy webapp's "Transmit" button naming — it's thematic.

## Verification
- [ ] Type "Tell me about the Traveler" → Ghost responds with lore-accurate information.
- [ ] Quick-action chips populate the composer and can be submitted.
- [ ] Chat history persists across page refreshes.
- [ ] Voice mode works: speak a question → Ghost responds audibly.
- [ ] Error responses display as red system bubbles.
- [ ] Navigation between Chat and Inventory works via tabs.

## ADR References
- **ADR 014/015**: Lore RAG — responses are grounded in the Bungie Manifest, not hallucinated.
- **ADR 007**: Universal LLM Adapter — the AI backend can be swapped without frontend changes.

## Completion
This is the final presentation phase. Once verified, the Destiny AI Ghost Companion is a fully functional desktop application and web app. 🎮

The project is ready for **Beta Testing** and **User Feedback**.
