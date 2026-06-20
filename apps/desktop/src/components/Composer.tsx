import { useEffect, useState, type KeyboardEvent } from "react";
import { useGhost } from "../store";
import { useSpeech } from "../hooks/useSpeech";

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z" />
      <path d="M17 11a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
      <path d="M12 4l-7 7h4v7h6v-7h4z" />
    </svg>
  );
}

export function Composer() {
  const { send } = useGhost();
  const [draft, setDraft] = useState("");
  const speech = useSpeech();

  useEffect(() => {
    if (speech.recording) setDraft(speech.transcript);
  }, [speech.transcript, speech.recording]);

  const submit = () => {
    const text = draft.trim();
    if (!text) return;
    send(text);
    setDraft("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const toggleMic = () => (speech.recording ? speech.stop() : speech.start());

  return (
    <div className="composer">
      <div className="composer-pill">
        {speech.supported && (
          <button
            className={"icon-btn mic" + (speech.recording ? " recording" : "")}
            onClick={toggleMic}
            title={speech.recording ? "Stop" : "Speak"}
          >
            <MicIcon />
          </button>
        )}
        <textarea
          className="composer-input"
          placeholder="Speak to your Ghost…"
          rows={1}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button className="icon-btn send" onClick={submit} disabled={!draft.trim()} title="Send">
          <SendIcon />
        </button>
      </div>
    </div>
  );
}
