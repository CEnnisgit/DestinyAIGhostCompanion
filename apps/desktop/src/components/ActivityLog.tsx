import { useEffect, useMemo, useState } from "react";
import { GhostBackend, type ActivityRecord } from "../api";
import { useGhost } from "../store";
import { CloseIcon } from "./Icons";

/// The Guardian's recent in-game activity: what they played, when, completion,
/// and the fireteam — across Destiny 2 and Destiny 1. Fed by `/activity/summary`.
export function ActivityLog({ onClose }: { onClose: () => void }) {
  const { backendURL, membershipId } = useGhost();
  const backend = useMemo(() => new GhostBackend(backendURL), [backendURL]);

  const [narrative, setNarrative] = useState("");
  const [records, setRecords] = useState<ActivityRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!membershipId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    backend
      .activitySummary(membershipId)
      .then((s) => {
        setNarrative(s.narrative);
        setRecords(s.recent);
      })
      .catch(() => {
        setNarrative("");
        setRecords([]);
      })
      .finally(() => setLoading(false));
  }, [backend, membershipId]);

  return (
    <div className="scrim center" onClick={onClose}>
      <div className="modal codex" onClick={(e) => e.stopPropagation()}>
        <div className="codex-head">
          <h3>Activity Log</h3>
          <div className="codex-head-actions">
            <button className="icon-btn" onClick={onClose} aria-label="Close">
              <CloseIcon />
            </button>
          </div>
        </div>

        {!membershipId && (
          <p className="muted">Sign in with Bungie to let the Ghost read your activity history.</p>
        )}

        {membershipId && narrative && <p className="activity-narrative">{narrative}</p>}

        <div className="codex-entries">
          {loading && <p className="muted">Reading your records…</p>}
          {!loading && membershipId && records.length === 0 && (
            <p className="muted">No recent activity found — or your Bungie session needs a refresh.</p>
          )}
          {records.map((r, i) => (
            <div key={i} className="lore-entry">
              <div className="lore-entry-head">
                <span className="lore-name">{r.name}</span>
                <span className="lore-cat">{r.mode}</span>
                <span className={"activity-status " + (r.completed ? "done" : "open")}>
                  {r.completed ? "COMPLETED" : "PLAYED"}
                </span>
                {r.game === "Destiny1" && <span className="lore-src">D1</span>}
                <span className="spacer" />
                <span className="activity-date">{formatDate(r.period)}</span>
              </div>
              {r.fireteam.length > 0 && (
                <p className="lore-desc">
                  <span className="activity-with">Fireteam:</span> {r.fireteam.join(", ")}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/// "2026-06-18T20:00:00Z" → "Jun 18, 2026" (falls back to the raw date part).
function formatDate(period: string): string {
  const d = new Date(period);
  if (Number.isNaN(d.getTime())) return period.split("T")[0] ?? period;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}
