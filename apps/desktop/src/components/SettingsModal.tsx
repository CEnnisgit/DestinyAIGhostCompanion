import { useState } from "react";
import { useGhost } from "../store";

export function SettingsModal({ onClose }: { onClose: () => void }) {
  const g = useGhost();
  const [draft, setDraft] = useState(g.backendURL);

  return (
    <div className="scrim center" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Settings</h3>

        <div className="section-label">Bungie Account</div>
        {g.membershipId ? (
          <>
            <p className="muted">Signed in · {g.membershipId}</p>
            {g.characters.length > 0 && (
              <div className="char-list">
                {g.characters.map((c) => (
                  <button
                    key={c.characterId}
                    className={"char" + (c.characterId === g.selectedCharacterId ? " active" : "")}
                    onClick={() => g.selectCharacter(c.characterId)}
                  >
                    <span>{c.className}</span>
                    <span className="muted small">◇ {c.light}</span>
                  </button>
                ))}
              </div>
            )}
            <button className="btn ghost" onClick={g.signOut}>
              Sign Out
            </button>
          </>
        ) : (
          <button className="btn" onClick={g.signIn}>
            Sign in with Bungie
          </button>
        )}

        <div className="section-label">Backend</div>
        <input className="text-input" value={draft} onChange={(e) => setDraft(e.target.value)} spellCheck={false} />
        <button
          className="btn"
          onClick={() => {
            g.setBackendURL(draft);
            g.checkHealth();
          }}
        >
          Save &amp; Check Connection
        </button>

        <p className="muted">Status: {g.health.toUpperCase()} · Use an HTTPS URL in production.</p>
        <p className="muted small">Not affiliated with Bungie, Inc.</p>

        <button className="btn ghost" onClick={onClose}>
          Done
        </button>
      </div>
    </div>
  );
}
