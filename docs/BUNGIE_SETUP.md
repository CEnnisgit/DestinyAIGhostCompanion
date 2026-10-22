# Bungie setup

Register an application at https://www.bungie.net/en/Application. Keep its API key and client ID together: Bungie requires the API key associated with the client that obtained the access token.

Choose **Public** for the default Ghost Companion flow. No client secret is needed or sent. Ghost Companion generates a random PKCE verifier, sends an S256 challenge, and exchanges the code with `client_id` and `code_verifier`. State is random, bound to an HttpOnly browser cookie, expires after ten minutes, and can be consumed once. Start again after a server restart. OAuth attempts currently require a single server process (or sticky routing).

Bungie's [published OAuth documentation](https://github.com/Bungie-net/api/wiki/OAuth-Documentation) describes public clients but does not document PKCE support. Verify enforcement with Bungie before a production release; sending the PKCE parameters alone does not prove that Bungie enforces them. It also states that public clients receive no refresh token: users may need to sign in again when access expires.

Choose **Confidential** only for a hosted server that can protect a secret. Set both `BUNGIE_CLIENT_SECRET` and `GHOST_BUNGIE_TOKEN_PROXY=1` on that server. The callback then uses the secret server-side. `POST /oauth/token` accepts `{code,state}` for a previously started OAuth attempt and requires its cookie; `POST /oauth/refresh` accepts `{refresh_token}`. These routes return only token fields and are disabled by default (404). Never embed a confidential secret in browser, desktop, or iOS bundles.

## Permissions

Select scopes in the Bungie application portal; do not send a dynamic `scope` parameter. Enable ReadBasicUserProfile and ReadDestinyInventoryAndVault for profile and inventory access, and MoveEquipDestinyItems for inventory actions. Enable ReadUserData when using private profile data, and only add other permissions for features you intend to expose. Review portal permission names when registering.

## Redirects

Register the exact case-sensitive redirect URI in the portal and set `BUNGIE_REDIRECT_URI` to match. Bungie's documentation describes a single registered URI; use separate registrations for different deployment targets if needed.

- Web: `https://<host>/oauth/callback`.
- Development: `http://127.0.0.1:3000/oauth/callback`. The callback must reach the FastAPI callback route (use a reverse proxy when the frontend owns that port). Alternatively register the backend callback port directly.
- Desktop: `http://127.0.0.1:<port>/oauth/callback`, with a loopback listener on the registered port and the system browser.
- iOS: `ghostcompanion://oauth/callback` or a claimed HTTPS universal link. These are deployment designs; verify Bungie's registration restrictions and implement the native callback handler before using them. This repository implements the browser/loopback callback, not native iOS routing.

For split frontend/backend deployments, set `GHOST_UI_ORIGINS` to the frontend's exact origin and configure `VITE_API_URL` to the backend. Use the same hostname in local development (avoid mixing localhost and 127.0.0.1) so the SameSite OAuth cookie is sent. Hosted deployments should use HTTPS and preferably serve API and UI on the same site.

## Environment and device settings

- `BUNGIE_API_KEY`: server API key for hosted mode. Takes precedence over device headers.
- `BUNGIE_CLIENT_ID`: public or confidential application ID. Falls back to the device Settings client ID.
- `BUNGIE_REDIRECT_URI`: exact registered redirect; defaults to the backend callback URL.
- `BUNGIE_CLIENT_SECRET`: confidential server secret, used only with proxy opt-in.
- `GHOST_BUNGIE_TOKEN_PROXY`: blank/off by default; `1` enables confidential exchanges and proxy routes.
- `GHOST_UI_ORIGINS`: comma-separated trusted frontend origins for CORS and popup delivery.

In desktop mode enter the Bungie API key and client ID in Settings. They remain in browser localStorage and are sent as `X-Bungie-API-Key` and `X-Bungie-Client-ID` on requests. The server never writes these settings to disk or environment. A Bungie operation with neither a server API key nor a device key returns 503. Linked Bungie OAuth tokens continue to use the existing server session database.
