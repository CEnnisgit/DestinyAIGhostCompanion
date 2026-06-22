import { useGhost } from "../store";
import { GhostMark } from "./GhostMark";
import { MenuIcon, PencilIcon, GearIcon, BookIcon } from "./Icons";

export function Header({
  onMenu,
  onSettings,
  onCodex,
}: {
  onMenu: () => void;
  onSettings: () => void;
  onCodex: () => void;
}) {
  const { health, startConversation } = useGhost();

  const statusText =
    health === "ok" ? "ONLINE" : health === "checking" ? "LINKING…" : health === "offline" ? "OFFLINE" : "STANDBY";

  return (
    <header className="header">
      <button className="icon-btn" onClick={onMenu} title="Conversations" aria-label="Conversations">
        <MenuIcon />
      </button>
      <GhostMark size={30} glow={health === "ok"} />
      <div className="brand">
        <div className="brand-title">Ghost</div>
        <div className={"brand-status " + health}>
          <span className="dot" />
          {statusText}
        </div>
      </div>
      <div className="spacer" />
      <button className="icon-btn" onClick={onCodex} title="Lore Codex" aria-label="Lore Codex">
        <BookIcon />
      </button>
      <button className="icon-btn" onClick={startConversation} title="New conversation" aria-label="New conversation">
        <PencilIcon />
      </button>
      <button className="icon-btn" onClick={onSettings} title="Settings" aria-label="Settings">
        <GearIcon />
      </button>
    </header>
  );
}
