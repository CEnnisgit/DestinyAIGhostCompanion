import { useEffect, useRef } from "react";
import { useGhost, type ChatMessage } from "../store";
import { GhostMark } from "./GhostMark";
import { Composer } from "./Composer";

const SUGGESTIONS = [
  "Tell me about the Last City",
  "Equip Sunshot on my Hunter",
  "What's in my Postmaster?",
  "Who is the Traveler?",
];

function intentClass(intent?: string): string {
  switch (intent) {
    case "lore":
      return "tag-lore";
    case "error":
      return "tag-error";
    default:
      return "tag-accent";
  }
}

function MessageRow({ message }: { message: ChatMessage }) {
  if (message.role === "guardian") {
    return (
      <div className="row guardian">
        <div className="bubble">{message.text}</div>
      </div>
    );
  }
  return (
    <div className="row ghost">
      <GhostMark size={28} />
      <div className="ghost-body">
        <div className="ghost-head">
          <span className="ghost-label">GHOST</span>
          {message.intent && (
            <span className={"intent " + intentClass(message.intent)}>{message.intent.toUpperCase()}</span>
          )}
        </div>
        <div className="ghost-text">{message.text}</div>
      </div>
    </div>
  );
}

export function ChatView() {
  const { messages, isAwaiting, send } = useGhost();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isAwaiting]);

  return (
    <div className="chat">
      <div className="messages">
        <div className="column">
          {messages.length === 0 && !isAwaiting && (
            <div className="empty">
              <GhostMark size={68} glow />
              <h2>Eyes up, Guardian.</h2>
              <p>Ask me to manage your gear or dig into Destiny lore.</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="suggestion" onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m) => (
            <MessageRow key={m.id} message={m} />
          ))}
          {isAwaiting && (
            <div className="row ghost">
              <GhostMark size={28} glow />
              <div className="typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
      <Composer />
    </div>
  );
}
