# App Store Launch Checklist — Ghost Companion (iOS)

What's done in code vs. what still needs your accounts, secrets, and decisions.

## ✅ Done in code

- App icon (1024px) + accent color asset catalog.
- App Transport Security scoped to a `localhost` dev exception only (no
  blanket `NSAllowsArbitraryLoads`).
- Microphone + speech usage strings present.
- OAuth URL scheme (`ghostcompanion://auth`) registered.
- Version/build set (`1.0` / `1`), launch screen, portrait orientation,
  app category.
- Default backend is configurable via the `GhostBackendURL` Info.plist key
  (falls back to localhost for dev).
- "Not affiliated with Bungie" disclaimer + Privacy Policy link in Settings
  (and the web app).
- Privacy policy text drafted in `PRIVACY.md`.
- Backend security: signed sessions; production enforces auth
  (`GHOST_REQUIRE_AUTH=1` + `GHOST_SESSION_SECRET`).

## ⛳ Needs you (accounts / secrets / decisions)

1. **Apple Developer Program** ($99/yr). Then set `DEVELOPMENT_TEAM` in
   `apps/ios/project.yml` to your Team ID and re-run `xcodegen generate`.
2. **Production backend deploy** over HTTPS (see "Backend" below). Then set the
   `GhostBackendURL` Info.plist value (and the web app's default URL) to that
   domain, and remove the localhost ATS exception for the release build.
3. **Bungie application config** (https://www.bungie.net/en/Application):
   - Redirect URL → `https://<your-domain>/auth/callback`.
   - OAuth Client Type → Confidential (we use a client secret).
   - Set `GHOST_MOBILE_CALLBACK=ghostcompanion://auth` and
     `GHOST_WEB_CALLBACK=https://<your-web-app>` on the server.
4. **Host the privacy policy** (`PRIVACY.md`) at a public URL and update the URL
   used in `SettingsView.swift`, `SettingsModal.tsx`, and App Store Connect.
   Replace the placeholder support email.
5. **App Store Connect**: create the app record, fill the App Privacy
   "nutrition labels" (Bungie account data via OAuth; chats; microphone/speech),
   description, keywords, support URL, and upload screenshots
   (6.7" + 6.1" + iPad if you later support it — currently iPhone-only).
6. **TestFlight**: archive in Xcode → upload → internal test → fix anything →
   submit for review.

## Backend (production)

- Deploy `apps/server` (Docker; `render.yaml`/`Dockerfile` exist) with a managed
  Postgres. Run migrations on boot (automatic).
- Required env: `DATABASE_URL`, `BUNGIE_API_KEY`, `BUNGIE_CLIENT_ID`,
  `BUNGIE_CLIENT_SECRET`, `GHOST_SESSION_SECRET` (`openssl rand -hex 32`),
  `GHOST_REQUIRE_AUTH=1`, `GHOST_MOBILE_CALLBACK`, `GHOST_WEB_CALLBACK`,
  and an LLM key (`LLM_API_KEY`/`OPENAI_API_KEY`).
- Optional: `GHOST_MANIFEST_SYNC=1` to ingest the Destiny manifest (lore + item +
  activity definitions) for offline, rate-limit-free name resolution.

## Bungie API Terms reminders

- Third-party apps are allowed but must not imply Bungie endorsement. The
  disclaimer is in Settings; keep Bungie logos out of the icon/marketing.
- Respect Bungie's rate limits (the manifest ingestion exists to minimize calls).
