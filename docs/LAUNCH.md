# Launch Runbook — Ghost Companion

End-to-end steps to take the Rust backend + iOS app from this repo to the App
Store. Ordered so each step unblocks the next.

---

## 1. Register a Bungie application

1. Go to <https://www.bungie.net/en/Application> → **Create New App**.
2. **OAuth Client Type:** Confidential.
3. **Redirect URL:** `https://<your-backend-domain>/auth/callback`
   (you'll know the domain after step 2; you can edit this later).
4. **Scope:** at least *Read your Destiny vault and inventory* and *Move or equip
   your Destiny gear*.
5. Note the **API Key**, **OAuth client_id**, and **OAuth client_secret**.

---

## 2. Deploy the backend (Render)

The repo ships [`render.yaml`](../render.yaml) (Docker web service + Postgres) and a
production [`Dockerfile`](../Dockerfile).

1. Push this branch to GitHub.
2. Render dashboard → **New → Blueprint** → select the repo. It provisions:
   - `ghost-companion-api` (Docker web service)
   - `ghost-companion-db` (Postgres 16, with `pgvector`)
3. Set the secret env vars (marked `sync: false`) in the dashboard:
   - `BUNGIE_API_KEY`, `BUNGIE_CLIENT_ID`, `BUNGIE_CLIENT_SECRET`
   - `LLM_API_KEY` (OpenAI or any OpenAI-compatible key)
4. Deploy. On boot the server **auto-runs migrations** and (because
   `GHOST_MANIFEST_SYNC=1`) downloads + embeds the Destiny manifest.
5. Verify: `curl https://<domain>/health` → `ok`.
6. Go back to the Bungie app settings and set the **Redirect URL** to
   `https://<domain>/auth/callback` exactly.

**Notes**
- The server listens on `$PORT` (Render injects it).
- `GHOST_MOBILE_CALLBACK=ghostcompanion://auth` makes `/auth/callback` redirect to
  the iOS app after login (already set in `render.yaml`).
- Postgres data persists across deploys (managed DB). The manifest only
  re-downloads when Bungie publishes a new version (`manifest_metadata`).

### Env var reference

| Var | Required | Purpose |
|-----|----------|---------|
| `DATABASE_URL` | yes | Postgres connection (from the managed DB) |
| `BUNGIE_API_KEY` / `BUNGIE_CLIENT_ID` / `BUNGIE_CLIENT_SECRET` | yes | Bungie API + OAuth |
| `GHOST_MOBILE_CALLBACK` | for iOS | App URL scheme for the OAuth redirect |
| `LLM_API_KEY` | for voice | OpenAI-compatible key |
| `LLM_BASE_URL` / `LLM_MODEL` | no | Override LLM provider/model (ADR-007) |
| `EMBEDDING_MODEL` / `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` | for lore | RAG embeddings (falls back to `LLM_*`/`OPENAI_API_KEY`) |
| `GHOST_MANIFEST_SYNC` | no | `1` to download + embed the manifest on boot |
| `GHOST_PERSONALITY` | no | `warlock` (default) / `titan` / `hunter` / `failsafe` |
| `GHOST_WS_DEV_TOKEN` | no | If set, `/ws/voice` requires this token |

---

## 3. Point the iOS app at the backend

In the app's **Settings → Backend**, set the Base URL to `https://<domain>`.
(Default is `http://localhost:8080` for development.)

Before archiving for release, edit `apps/ios/GhostCompanion/Info.plist` and
**remove the `localhost` ATS exception** — production is HTTPS and shouldn't need
it.

---

## 4. Build & sign the iOS app

1. `cd apps/ios && xcodegen generate && open GhostCompanion.xcodeproj`
2. Set `DEVELOPMENT_TEAM` in `project.yml` (your Apple Developer Team ID), then
   regenerate. Requires an **Apple Developer Program** membership ($99/yr).
3. Confirm the bundle id `com.cennis.ghostcompanion` is registered in your account
   with **Sign in with Apple**/associated capabilities as needed (none required
   beyond default; the app uses `ghostcompanion://` URL scheme + microphone +
   speech, all declared in `Info.plist`).
4. Select a real device / **Any iOS Device**, **Product → Archive**.

---

## 5. TestFlight → App Store

1. Xcode Organizer → **Distribute App → App Store Connect → Upload**.
2. In **App Store Connect**, create the app record (bundle id above).
3. Fill in **App Privacy** ("nutrition labels"):
   - **Bungie account data** via OAuth (linked to identity; used for app
     functionality).
   - **Microphone / Speech** (on-device; used for voice commands; not linked,
     not used for tracking).
4. Add a **Privacy Policy URL** (required). Cover: Bungie OAuth tokens stored
   server-side, on-device speech, no ad tracking.
5. Add screenshots, description, keywords. Include a clear **"Not affiliated with
   or endorsed by Bungie, Inc."** disclaimer (the app already shows one in
   Settings).
6. Submit a build to **TestFlight**, smoke-test the real flows (sign-in, voice,
   lore, equip), then submit for **App Store review**.

---

## 6. Pre-submit smoke test (against the live backend)

- [ ] `GET /health` → `ok`
- [ ] Sign in with Bungie completes and returns to the app
- [ ] Settings shows your characters; pick an active one
- [ ] "Tell me about the Last City" → lore answer (RAG)
- [ ] "Equip <weapon> on my <class>" → equips in-game (verify in Destiny / DIM)
- [ ] Voice: tap the mic, speak a command, confirm transcription + response

---

## Trademark / policy note

Bungie's API Terms of Use permit third-party apps but prohibit implying Bungie
endorsement and using Bungie marks/logos in a confusing way. Keep the "not
affiliated" disclaimer, avoid Bungie logos in the icon/branding, and review the
current [Bungie API ToS](https://www.bungie.net/en/Clan/Detail/3936606) before
submitting.
