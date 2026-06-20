import { useState } from "react";
import { GhostProvider } from "./store";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import { SettingsModal } from "./components/SettingsModal";

export function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <GhostProvider>
      <div className="app">
        <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
        <div className="main">
          <Header onMenu={() => setMenuOpen(true)} onSettings={() => setSettingsOpen(true)} />
          <ChatView />
        </div>
        {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}
      </div>
    </GhostProvider>
  );
}
