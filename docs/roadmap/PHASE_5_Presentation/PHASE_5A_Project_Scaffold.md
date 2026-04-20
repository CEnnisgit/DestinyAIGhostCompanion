# Phase 5A: Project Scaffold

> **Status:** 🔲 Not Started
> **Objective:** Set up the modern frontend toolchain that serves both Electron Desktop and Web targets from a single codebase.
> **Location:** `apps/desktop/`
> **Depends On:** Phase 4A (Docker/Postgres running), Phase 4C (WebSocket server available)

---

## Context for the Agent

The repository currently has two legacy frontend directories:
- `frontend/` — A Create React App (CRA) project. CRA is deprecated. This will be replaced.
- `webapp/` — A standalone `index.html` with an excellent Destiny-themed design system. This will be harvested in Phase 5B.

Your job is to scaffold a modern **Vite + React + TypeScript** project inside `apps/desktop/` that can run as both a web app and an Electron desktop app.

## Prerequisites
- [ ] Node.js 18+ installed.
- [ ] The Rust backend from Phase 4 is running on `http://localhost:8080`.

## Deliverables

### 1. Initialize Vite + React + TypeScript
```bash
cd apps/
npx -y create-vite@latest desktop -- --template react-ts
cd desktop
npm install
```

### 2. Add Electron
```bash
npm install --save-dev electron electron-builder concurrently wait-on
```

Create `apps/desktop/electron/main.ts`:
```typescript
import { app, BrowserWindow } from 'electron';
import path from 'path';

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    frame: false,          // Frameless for the Destiny aesthetic
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // In dev, load from Vite dev server. In prod, load the built index.html.
  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173');
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
```

### 3. Add npm scripts to `package.json`
```json
{
  "scripts": {
    "dev": "vite",
    "dev:electron": "concurrently \"vite\" \"wait-on http://localhost:5173 && electron .\"",
    "build": "vite build",
    "build:electron": "vite build && electron-builder"
  }
}
```

### 4. Configure `electron-builder` in `package.json`
```json
{
  "build": {
    "appId": "com.ghostcompanion.desktop",
    "productName": "Ghost Companion",
    "win": {
      "target": "nsis",
      "icon": "public/ghost-icon.png"
    },
    "files": ["dist/**/*", "electron/**/*"]
  }
}
```

### 5. Environment Configuration
Create `apps/desktop/.env.example`:
```
VITE_API_BASE_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080/ws/voice
```

### 6. Proxy Configuration for Web Dev
In `apps/desktop/vite.config.ts`:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
      '/ws': {
        target: 'ws://localhost:8080',
        ws: true,
      },
    },
  },
});
```

## Verification
- [ ] `npm run dev` serves the Vite React app on `http://localhost:5173`.
- [ ] `npm run dev:electron` opens an Electron window loading the Vite dev server.
- [ ] The default Vite landing page renders in both targets.
- [ ] `npm run build` produces a `dist/` folder.

## Next Phase
Once verified, proceed to → [Phase 5B: Design System](./PHASE_5B_Design_System.md)
