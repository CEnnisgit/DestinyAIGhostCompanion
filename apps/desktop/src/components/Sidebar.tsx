import { useGhost } from "../store";
import { GhostMark } from "./GhostMark";
import { PlusIcon, CloseIcon } from "./Icons";

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { conversations, selectedId, selectConversation, deleteConversation, startConversation } = useGhost();

  return (
    <>
      {open && <div className="scrim" onClick={onClose} />}
      <aside className={"sidebar" + (open ? " open" : "")}>
        <div className="sidebar-head">
          <span>Conversations</span>
          <button
            className="icon-btn"
            onClick={() => {
              startConversation();
              onClose();
            }}
            title="New conversation"
          >
            <PlusIcon />
          </button>
        </div>
        <div className="conv-list">
          {conversations.map((c) => (
            <div key={c.id} className={"conv" + (c.id === selectedId ? " active" : "")}>
              <button
                className="conv-main"
                onClick={() => {
                  selectConversation(c.id);
                  onClose();
                }}
              >
                <GhostMark size={18} />
                <div className="conv-text">
                  <div className="conv-title">{c.title || "New Conversation"}</div>
                  <div className="conv-sub">{c.messages.length ? c.messages[c.messages.length - 1].text : "Empty"}</div>
                </div>
              </button>
              <button className="conv-del" onClick={() => deleteConversation(c.id)} title="Delete">
                <CloseIcon />
              </button>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}
