import { useState } from "react";
import { useGhost } from "../store";

export function SettingsModal({ onClose }: { onClose: () => void }) {
  const { backendURL, setBackendURL, checkHealth, health } = useGhost();
  const [draft, setDraft] = useState(backendURL);

  return (
    <div className="scrim center" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Settings</h3>

        <label className="field-label">Backend URL</label>
        <input className="text-input" value={draft} onChange={(e) => setDraft(e.target.value)} spellCheck={false} />
        <button
          className="btn"
          onClick={() => {
            setBackendURL(draft);
            checkHealth();
          }}
        >
          Save &amp; Check Connection
        </button>

        <p className="muted">Status: {health.toUpperCase()} · Use an HTTPS URL in production.</p>
        <p className="muted small">Not affiliated with Bungie, Inc.</p>

        <button className="btn ghost" onClick={onClose}>
          Done
        </button>
      </div>
    </div>
  );
}
