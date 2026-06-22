import { useState } from "react";
import { GhostProvider } from "./store";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import { SettingsModal } from "./components/SettingsModal";
import { LoreCodex } from "./components/LoreCodex";
import { SacredBackground } from "./components/SacredGeometry";

export function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [codexOpen, setCodexOpen] = useState(false);

  return (
    <GhostProvider>
      <div className="app">
        <SacredBackground />
        <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
        <div className="main">
          <Header
            onMenu={() => setMenuOpen(true)}
            onSettings={() => setSettingsOpen(true)}
            onCodex={() => setCodexOpen(true)}
          />
          <ChatView />
        </div>
        {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}
        {codexOpen && <LoreCodex onClose={() => setCodexOpen(false)} />}
      </div>
    </GhostProvider>
  );
}
