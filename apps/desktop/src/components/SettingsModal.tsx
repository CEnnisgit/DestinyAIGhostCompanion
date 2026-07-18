import { useState } from "react";
import { useGhost } from "../store";

export function SettingsModal({ onClose }: { onClose: () => void }) {
  const g = useGhost();
  const [draft, setDraft] = useState(g.backendURL);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Erases the Guardian's server-side account. Closes only once the server
  // confirms; on failure the user stays signed in and sees why, rather than
  // being told a deletion happened that didn't.
  const deleteAccount = async () => {
    setDeletingAccount(true);
    setDeleteError(null);
    try {
      await g.deleteAccount();
      onClose();
    } catch {
      setDeleteError("Could not delete your account. Check your connection and try again.");
    } finally {
      setDeletingAccount(false);
      setConfirmingDelete(false);
    }
  };

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

            <div className="section-label">Delete Account</div>
            <p className="muted small">
              Permanently erases your saved conversations and your Bungie sign-in from our server,
              and signs you out everywhere. Your Destiny account and game data are untouched. This
              cannot be undone.
            </p>
            {confirmingDelete ? (
              <>
                <button className="btn danger" onClick={deleteAccount} disabled={deletingAccount}>
                  {deletingAccount ? "Deleting…" : "Yes, permanently delete my account"}
                </button>
                <button className="btn ghost" onClick={() => setConfirmingDelete(false)} disabled={deletingAccount}>
                  Cancel
                </button>
              </>
            ) : (
              <button className="btn danger" onClick={() => setConfirmingDelete(true)}>
                Delete Account
              </button>
            )}
            {deleteError && <p className="muted small error-text">{deleteError}</p>}
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
        <p className="muted small">
          Ghost Companion is an unofficial, fan-made app — not affiliated with, endorsed by, or
          sponsored by Bungie, Inc. Destiny is a trademark of Bungie, Inc.{" "}
          <a href="https://cennisgit.github.io/DestinyAIGhostCompanion/privacy/" target="_blank" rel="noreferrer">
            Privacy Policy
          </a>
        </p>

        <button className="btn ghost" onClick={onClose}>
          Done
        </button>
      </div>
    </div>
  );
}
