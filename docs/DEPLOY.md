# Ghost Companion hosting and desktop packages

## Hosted container

Build with `docker build -t ghost-companion .`. The image builds Vite with
`VITE_API_URL=/`, serves `frontend/build` and SPA routes from FastAPI, and runs as
UID 10001. Expose the container's `PORT` (8000 by default) behind HTTPS. The
container health check uses `/health`. Only core Python requirements are installed.

Set these in the host's secret/environment settings, never in the image or Git:

| Variable | Configuration |
| --- | --- |
| `GHOST_MODE` | `hosted` (already set by the Dockerfile); otherwise defaults to desktop |
| `JWT_SECRET` | Required in hosted mode; generate a long random value, keep stable across restarts |
| `GHOST_UI_ORIGINS` | Exact comma-separated HTTPS UI origins; no wildcard. Empty permits same-origin requests only |
| `BUNGIE_CLIENT_ID` | Registered Bungie OAuth application's ID |
| `BUNGIE_REDIRECT_URI` | Exact registered public HTTPS URL ending in `/oauth/callback` |
| `PORT` | Host-assigned listening port, defaults to 8000 |
| `GHOST_DB_PATH` | SQLite file, defaults to `data/app.db`; parent must exist and be writable |
| `GHOST_MAX_BODY_BYTES` | Body limit including streamed bodies; defaults to 1048576 |
| `GHOST_RATE_CAPACITY` | Per-client/user bucket capacity; defaults to 60 requests |
| `GHOST_RATE_REFILL_PER_SECOND` | Refill rate; defaults to 1 request/second |
| `GHOST_AI_BASE_URLS` | Optional exact HTTPS base URLs for administrator-approved compatible AI services |
| `FORWARDED_ALLOW_IPS` | Trusted reverse proxy addresses; defaults to 127.0.0.1. Do not trust arbitrary direct clients |

Users provide AI and Bungie API keys through Settings. Hosted mode does not use
local token files, server microphones, speech synthesis, audio diagnostics,
fine-tuning, or Ollama/local providers. Default public AI endpoints are allowed;
custom endpoints require the administrator allowlist. Avoid shared AI environment
keys; `GHOST_ALLOW_ENV_AI_KEY` is off by default. If Bungie requires a confidential
client, enable `GHOST_BUNGIE_TOKEN_PROXY=1` and configure `BUNGIE_CLIENT_SECRET`
through the host's secrets UI. Do not expose that secret to the frontend.

Bungie account IDs identify hosted users; conversation ownership is checked before
writing messages, and OAuth tokens are stored by user ID. Each chat creates its
own assistant, provider client, and caches. Web credentials use browser
localStorage with a visible warning; use a trusted origin over HTTPS.

Use one process/replica with a persistent writable volume for SQLite and back it
up: mount `/app/data` owned by UID 10001. Logs are written to `/app/logs` and stdout.
Free hosts with ephemeral disks lose accounts, tokens, and history on restart.
The in-memory limiter and pending OAuth attempts are process-local and reset on
restart; multiple workers/replicas require an external shared limiter, shared
OAuth-attempt store, and a production shared database before scaling. Health
checks and CORS preflight are exempt from rate limiting.

For a local container check, provide the variables above via your local secret
manager or a gitignored env file, publish a port, and request `/health`. No
hosting account or deployment is created by the repository workflows.

## Host options

Check current limits before choosing; free offerings change and provider API
usage may still incur charges.

- **Fly.io:** use the Dockerfile, configure the service's internal port, HTTPS,
  secrets, and a volume for `/app/data`. New users get a limited trial rather than
  a general ongoing free allowance. See [trial](https://fly.io/docs/about/free-trial/)
  and [pricing](https://fly.io/docs/about/pricing/).
- **Render:** create a Docker web service with `/health` as its health path and
  the environment above. Free services sleep after 15 idle minutes, have quotas,
  and use ephemeral filesystems; durable history needs a storage-supported plan.
  See [free service restrictions](https://render.com/docs/free).
- **Railway:** use the Dockerfile and Railway-provided `PORT`, configure HTTPS,
  environment variables, and durable storage. The trial currently grants $5 for
  up to 30 days, then a Free plan with $1 monthly credit; this does not guarantee
  continuous operation within the credit. See [trial and Free plan](https://docs.railway.com/pricing/free-trial).

## Desktop

`.github/workflows/desktop.yml` builds unsigned Windows and macOS artifacts on
manual dispatch, version tags, and desktop-related pull requests. Windows uses
`ghost_desktop.spec` plus Inno Setup; macOS uses the same spec's `.app` bundle and
`hdiutil` to make a DMG. Artifacts are uploaded without publishing a release.
Unsigned builds may trigger OS trust prompts; signing/notarization is not set up.

Desktop serves the app from loopback. `/config` reports mode and keyring support.
When available, Settings migrates browser keys to the OS keyring under service
`ghost-companion`, removes them from localStorage, and loads them into browser
memory for request headers. GET/PUT/DELETE `/local/secrets` require a loopback
client, loopback Host, and same-origin browser requests. A missing/unusable
keyring falls back to browser storage with a warning. Keyring errors return
generic messages and never log key values. Delete keys by clearing their fields
or calling DELETE from a trusted local client.

## Frontend and tests

`VITE_API_URL` omitted preserves `http://127.0.0.1:8000` for development; an explicit
empty value or `/` enables relative same-origin requests. `npm run test:e2e`
builds the frontend, starts `vite preview`, and runs Chromium with mocked APIs.
Run `npx playwright install chromium` first. Core tests use fake credentials,
isolated databases, and a fake keyring; no real provider calls are required.
