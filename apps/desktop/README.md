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

## Bungie sign-in (web)

**Settings → Sign in with Bungie** sends the browser to the backend `/auth/login`
with the app's return URL; the backend round-trips it via OAuth `state` and
redirects back with `?membership_id=...`, which the app captures. For this to
work the backend must allowlist the web origin:

```
GHOST_WEB_CALLBACK=http://localhost:5173,https://your-web-app.example
```

Once signed in, Settings shows your characters; the selected one is sent to
`/ws/voice` for equips (same as iOS).

## Deploy

`npm run build` emits a static `dist/` — host it anywhere (Netlify, Vercel, Render
static site, an S3 bucket). Point Settings at your deployed backend URL, and add
that web origin to `GHOST_WEB_CALLBACK` on the backend.
