# Deploy Ghost Companion to `ghostcompanion.com`

This repo can now be deployed as a single web service that serves:

- the React frontend from `frontend/build`
- the FastAPI API from `server.py`
- the Bungie OAuth callback on the same domain

## Recommended host

Use Render as a Docker web service. The repo includes [`render.yaml`](./render.yaml) and a production [`Dockerfile`](./Dockerfile).

## Required environment variables

Set these in Render before going live:

- `BUNGIE_API_KEY`
- `BUNGIE_CLIENT_ID`
- `BUNGIE_CLIENT_SECRET`
- `GHOST_TOKEN_KEY`
- `XAI_API_KEY`

These are already defined in [`render.yaml`](./render.yaml) as non-synced secrets:

- `PUBLIC_APP_URL=https://ghostcompanion.com`
- `BUNGIE_REDIRECT_URI=https://ghostcompanion.com/oauth/callback`
- `PORT=10000`

## Bungie developer portal

In your Bungie application settings, register this exact redirect URI:

`https://ghostcompanion.com/oauth/callback`

If Bungie has your old localhost callback saved, production sign-in will fail until this is updated.

## Render deploy steps

1. Push this repo to GitHub.
2. In Render, create the service with `New > Blueprint` and select this repo.
3. Confirm the Docker web service from [`render.yaml`](./render.yaml).
4. Add the secret env vars listed above.
5. Deploy and wait for `/health` to return `ok: true`.

## Domain setup

After the first deploy, Render will assign an `onrender.com` hostname.

1. In the Render service settings, confirm `ghostcompanion.com` is listed under Custom Domains.
2. In your DNS provider, point `ghostcompanion.com` to the Render target shown in the dashboard.
3. Remove any conflicting `AAAA` records.
4. Verify the domain in Render and wait for TLS issuance.

## Model provider choice

For a hosted website, use `Grok` by setting `XAI_API_KEY`.

The app used to default to local Ollama, which is fine on desktop but wrong for a public hosted site. The UI and backend now prefer a hosted-capable provider when one is configured.
