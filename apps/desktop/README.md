# Ghost Companion — Web Client

> **Status:** 🟢 In progress (Phase 5, web) — chat UI, history, browser voice
> **Stack:** Vite + React + TypeScript (Electron desktop wrapper is a later step)

A browser version of Ghost Companion that talks to the same Rust backend
(`apps/server`). Same GPT-style conversation experience and Destiny-blue theme as
the iOS app.

## Run

```bash
cd apps/desktop
npm install
npm run dev        # dev server on http://localhost:5173
# or:
npm run build      # type-check + production build to dist/
npm run preview    # serve the production build on :4173
```

Set the backend URL in **Settings** (default `http://localhost:8080`). The backend
enables permissive CORS so the browser can call it.

## What's here

- `src/store.tsx` — conversations + WebSocket + health, persisted to `localStorage`
- `src/api.ts` — backend client (`/health`, `/ws/voice`, `/characters`, `/auth/login`)
- `src/hooks/useSpeech.ts` — browser `SpeechRecognition` voice input
- `src/components/` — Header, Sidebar (history), ChatView, Composer, SettingsModal, GhostMark
- `src/styles/theme.css` — the Destiny-blue design tokens + layout

## Deploy

`npm run build` emits a static `dist/` — host it anywhere (Netlify, Vercel, Render
static site, an S3 bucket). Point Settings at your deployed backend URL.

## Not yet wired (web)

- Bungie sign-in (the backend redirects OAuth to the iOS scheme; a web callback
  mode is a follow-up) and the character picker that depends on it.
