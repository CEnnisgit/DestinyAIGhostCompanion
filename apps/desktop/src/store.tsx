import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  GhostBackend,
  type CharacterSummary,
  type SyncedMessage,
  type SyncedThreadSummary,
} from "./api";

export type Role = "guardian" | "ghost";
export interface ChatMessage {
  id: string;
  role: Role;
  text: string;
  intent?: string;
}
export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: number;
}
export type Health = "unknown" | "checking" | "ok" | "offline";

const STORE_KEY = "ghost.conversations";
const URL_KEY = "ghost.backendURL";
const MEMBER_KEY = "ghost.membershipId";
const CHAR_KEY = "ghost.characterId";
const DEFAULT_URL = "http://localhost:8080";

const uid = () => Math.random().toString(36).slice(2) + Date.now().toString(36);
const newConversation = (): Conversation => ({
  id: uid(),
  title: "New Conversation",
  messages: [],
  updatedAt: Date.now(),
});

// Server (synced) → local view-model converters.
const summaryToConversation = (t: SyncedThreadSummary): Conversation => ({
  id: t.id,
  title: t.title,
  messages: [],
  updatedAt: Date.parse(t.updated_at) || Date.now(),
});
const syncedToMessage = (m: SyncedMessage): ChatMessage => ({
  id: m.id,
  role: m.role,
  text: m.text,
  intent: m.intent ?? undefined,
});

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Conversation[];
      if (Array.isArray(parsed) && parsed.length) return parsed.sort((a, b) => b.updatedAt - a.updatedAt);
    }
  } catch {
    /* ignore corrupt storage */
  }
  return [newConversation()];
}

interface GhostState {
  conversations: Conversation[];
  selectedId: string;
  messages: ChatMessage[];
  health: Health;
  isAwaiting: boolean;
  backendURL: string;
  membershipId: string | null;
  characters: CharacterSummary[];
  selectedCharacterId: string | null;
  profileSummary: string | null;
  send: (text: string) => void;
  startConversation: () => void;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  setBackendURL: (url: string) => void;
  checkHealth: () => void;
  signIn: () => void;
  signOut: () => void;
  selectCharacter: (id: string) => void;
}

const GhostContext = createContext<GhostState | null>(null);

export function useGhost(): GhostState {
  const ctx = useContext(GhostContext);
  if (!ctx) throw new Error("useGhost must be used within GhostProvider");
  return ctx;
}

export function GhostProvider({ children }: { children: ReactNode }) {
  const initial = useRef(loadConversations()).current;
  const [conversations, setConversations] = useState<Conversation[]>(initial);
  const [selectedId, setSelectedId] = useState<string>(initial[0].id);
  const [health, setHealth] = useState<Health>("unknown");
  const [isAwaiting, setIsAwaiting] = useState(false);
  const [backendURL, setBackendURLState] = useState<string>(() => localStorage.getItem(URL_KEY) ?? DEFAULT_URL);
  const [membershipId, setMembershipId] = useState<string | null>(() => localStorage.getItem(MEMBER_KEY));
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(() => localStorage.getItem(CHAR_KEY));
  const [profileSummary, setProfileSummary] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const selectedIdRef = useRef(selectedId);
  selectedIdRef.current = selectedId;
  const membershipRef = useRef(membershipId);
  membershipRef.current = membershipId;
  const characterRef = useRef(selectedCharacterId);
  characterRef.current = selectedCharacterId;

  const backend = useMemo(() => new GhostBackend(backendURL), [backendURL]);

  // Persist locally only when signed out; signed-in chats live on the server.
  useEffect(() => {
    if (!membershipId) localStorage.setItem(STORE_KEY, JSON.stringify(conversations));
  }, [conversations, membershipId]);

  // When signed in, conversations sync from the server (cross-device). Loads the
  // thread list; messages are fetched lazily on selection.
  const loadServerThreads = useCallback(async () => {
    const mid = membershipRef.current;
    if (!mid) return;
    try {
      const threads = await backend.listConversations(mid);
      if (threads.length) {
        const convos = threads.map(summaryToConversation);
        setConversations(convos);
        setSelectedId((cur) => (convos.some((c) => c.id === cur) ? cur : convos[0].id));
      } else {
        // No server threads yet: start a fresh one on the server.
        const created = await backend.createConversation(mid);
        setConversations([summaryToConversation(created)]);
        setSelectedId(created.id);
      }
    } catch {
      /* backend unreachable — keep whatever is on screen */
    }
  }, [backend]);

  useEffect(() => {
    if (membershipId) void loadServerThreads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [membershipId, loadServerThreads]);

  // Capture ?membership_id=... after an OAuth web redirect, then clean the URL.
  useEffect(() => {
    const url = new URL(window.location.href);
    const mid = url.searchParams.get("membership_id");
    if (mid) {
      localStorage.setItem(MEMBER_KEY, mid);
      setMembershipId(mid);
      url.searchParams.delete("membership_id");
      window.history.replaceState({}, "", url.pathname + url.search);
    }
  }, []);

  const checkHealth = useCallback(() => {
    setHealth("checking");
    backend
      .health()
      .then((ok) => setHealth(ok ? "ok" : "offline"))
      .catch(() => setHealth("offline"));
  }, [backend]);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const selectCharacter = useCallback((id: string) => {
    localStorage.setItem(CHAR_KEY, id);
    setSelectedCharacterId(id);
  }, []);

  const loadCharacters = useCallback(async () => {
    const mid = membershipRef.current;
    if (!mid) return;
    try {
      const result = await backend.characters(mid);
      setCharacters(result);
      if (result.length && !result.some((c) => c.characterId === characterRef.current)) {
        selectCharacter(result[0].characterId);
      }
    } catch {
      /* not signed in / backend unreachable */
    }
  }, [backend, selectCharacter]);

  useEffect(() => {
    if (membershipId) void loadCharacters();
  }, [membershipId, loadCharacters]);

  useEffect(() => {
    if (!membershipId) {
      setProfileSummary(null);
      return;
    }
    backend
      .profileSummary(membershipId)
      .then(setProfileSummary)
      .catch(() => setProfileSummary(null));
  }, [membershipId, backend]);

  const updateSelected = useCallback((fn: (c: Conversation) => void) => {
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== selectedIdRef.current) return c;
        const copy = { ...c, messages: [...c.messages] };
        fn(copy);
        copy.updatedAt = Date.now();
        return copy;
      }),
    );
  }, []);

  const handleInbound = useCallback(
    (raw: string) => {
      setIsAwaiting(false);
      let message: ChatMessage;
      try {
        const frame = JSON.parse(raw) as { response: string; intent?: string };
        message = { id: uid(), role: "ghost", text: frame.response, intent: frame.intent };
      } catch {
        message = { id: uid(), role: "ghost", text: raw };
      }
      updateSelected((c) => {
        c.messages.push(message);
      });
    },
    [updateSelected],
  );

  const ensureSocket = useCallback((): WebSocket => {
    const existing = socketRef.current;
    if (existing && existing.readyState <= WebSocket.OPEN) return existing;
    const ws = new WebSocket(
      backend.voiceSocketURL({
        membershipId: membershipRef.current ?? undefined,
        characterId: characterRef.current ?? undefined,
      }),
    );
    ws.onmessage = (e) => handleInbound(typeof e.data === "string" ? e.data : "");
    ws.onerror = () => setIsAwaiting(false);
    ws.onclose = () => {
      if (socketRef.current === ws) socketRef.current = null;
    };
    socketRef.current = ws;
    return ws;
  }, [backend, handleInbound]);

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      const isNew = (c: Conversation) => c.messages.length === 0 && c.title === "New Conversation";
      updateSelected((c) => {
        if (isNew(c)) c.title = trimmed.slice(0, 40);
        c.messages.push({ id: uid(), role: "guardian", text: trimmed });
      });

      const mid = membershipRef.current;
      // Signed in: go over HTTP /chat so the server persists the turn and the
      // conversation syncs across devices (and the reply is game-data grounded).
      if (mid) {
        const threadId = selectedIdRef.current;
        setIsAwaiting(true);
        backend
          .chat(trimmed, mid, threadId)
          .then((reply) => {
            updateSelected((c) => {
              c.messages.push({ id: uid(), role: "ghost", text: reply, intent: "conversation" });
            });
          })
          .catch(() => {
            updateSelected((c) => {
              c.messages.push({ id: uid(), role: "ghost", text: "The Ghost is unreachable right now.", intent: "error" });
            });
          })
          .finally(() => setIsAwaiting(false));
        return;
      }

      // Signed out: ephemeral local chat over the WebSocket.
      const payload = JSON.stringify({ text: trimmed });
      const ws = ensureSocket();
      setIsAwaiting(true);
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(payload);
      } else {
        ws.addEventListener("open", () => ws.send(payload), { once: true });
      }
    },
    [backend, ensureSocket, updateSelected],
  );

  const startConversation = useCallback(() => {
    setIsAwaiting(false);
    const mid = membershipRef.current;
    if (mid) {
      // Create the thread on the server so it exists on every device.
      backend
        .createConversation(mid)
        .then((thread) => {
          setConversations((prev) => [summaryToConversation(thread), ...prev]);
          setSelectedId(thread.id);
        })
        .catch(() => {});
      return;
    }
    setConversations((prev) => {
      const current = prev.find((c) => c.id === selectedIdRef.current);
      if (current && current.messages.length === 0) return prev;
      const convo = newConversation();
      setSelectedId(convo.id);
      return [convo, ...prev];
    });
  }, [backend]);

  const selectConversation = useCallback(
    (id: string) => {
      setSelectedId(id);
      setIsAwaiting(false);
      // Lazily fetch this thread's messages from the server when synced.
      const mid = membershipRef.current;
      const existing = conversations.find((c) => c.id === id);
      if (mid && existing && existing.messages.length === 0) {
        backend
          .getConversation(mid, id)
          .then((thread) => {
            setConversations((prev) =>
              prev.map((c) =>
                c.id === id ? { ...c, title: thread.title, messages: thread.messages.map(syncedToMessage) } : c,
              ),
            );
          })
          .catch(() => {});
      }
    },
    [backend, conversations],
  );

  const deleteConversation = useCallback(
    (id: string) => {
      const mid = membershipRef.current;
      if (mid) void backend.deleteConversation(mid, id);
      setConversations((prev) => {
        let next = prev.filter((c) => c.id !== id);
        if (next.length === 0) next = [newConversation()];
        if (!next.some((c) => c.id === selectedIdRef.current)) setSelectedId(next[0].id);
        return next;
      });
    },
    [backend],
  );

  const setBackendURL = useCallback((url: string) => {
    const trimmed = url.trim();
    localStorage.setItem(URL_KEY, trimmed);
    setBackendURLState(trimmed);
    socketRef.current?.close();
    socketRef.current = null;
  }, []);

  const signIn = useCallback(() => {
    const loginUrl = new URL(backend.loginURL());
    loginUrl.searchParams.set("redirect", window.location.origin + window.location.pathname);
    window.location.href = loginUrl.toString();
  }, [backend]);

  const signOut = useCallback(() => {
    localStorage.removeItem(MEMBER_KEY);
    localStorage.removeItem(CHAR_KEY);
    setMembershipId(null);
    setSelectedCharacterId(null);
    setCharacters([]);
    setProfileSummary(null);
    // Drop the synced threads from view and fall back to local conversations.
    const local = loadConversations();
    setConversations(local);
    setSelectedId(local[0].id);
  }, []);

  const messages = conversations.find((c) => c.id === selectedId)?.messages ?? [];

  const value: GhostState = {
    conversations,
    selectedId,
    messages,
    health,
    isAwaiting,
    backendURL,
    membershipId,
    characters,
    selectedCharacterId,
    profileSummary,
    send,
    startConversation,
    selectConversation,
    deleteConversation,
    setBackendURL,
    checkHealth,
    signIn,
    signOut,
    selectCharacter,
  };

  return <GhostContext.Provider value={value}>{children}</GhostContext.Provider>;
}
