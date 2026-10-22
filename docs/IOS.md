# iOS

The Capacitor wrapper lives in `frontend/ios/`. It uses the placeholder bundle ID
`com.example.ghostcompanion` and display name **Ghost Companion**. No signing
credentials or developer account are included. Node 22+, Xcode compatible with
Capacitor 8, and an installed iOS Simulator runtime are required on macOS.
The native project uses Swift Package Manager; do not add Pods or build outputs.

## Build and server

From `frontend/`:

```sh
npm ci
VITE_API_URL=https://your-hosted-server.example npm run build:ios
npx cap sync ios
npx cap open ios
```

`VITE_API_URL` is required for `build:ios` and must be HTTPS. It is embedded at
build time; changing it requires rebuilding and syncing. The regular web build
retains its existing URL default. Never embed API keys in Vite environment
variables. Use a server reachable from the device, not localhost. Configure it
with `GHOST_MODE=hosted` and `GHOST_UI_ORIGINS=capacitor://localhost` (append web
origins separated by commas if needed). CORS only permits explicitly configured
origins. Native Settings stores AI and Bungie keys in the iOS Keychain via
`@aparajita/capacitor-secure-storage`; desktop keyring and web localStorage retain
their existing behavior. Native secure storage failures prevent Settings edits.
Legacy native credentials migrate out of localStorage after a successful Keychain
write. The app session token also uses Keychain on native. Keychain values may
survive uninstall; clear credentials before giving a device to someone else.
The server receives keys over HTTPS for requests; choose a server you trust.

## Bungie OAuth

Use a Bungie **public client** with PKCE, without a client secret. Register
`ghostcompanion://oauth/callback` as its redirect with Bungie, subject to Bungie's
current registration requirements. If the portal does not accept custom schemes,
resolve that registration requirement before production; this scaffold does not
claim approval by Bungie. Set the public client ID and API key in Settings or
configure the server's public client ID. The native app requests exactly this
redirect; the server rejects other client-supplied redirects. The web redirect
continues to use `BUNGIE_REDIRECT_URI` or the server callback URL.

The app opens authorization through `@capacitor/browser` and receives the
registered scheme through `@capacitor/app`'s `appUrlOpen` listener. It checks the
callback host/path, state, and attempt expiry before exchanging the code. The
server creates S256 PKCE, keeps the verifier for ten minutes, and consumes each
attempt once. Native attempts use a random session proof and the configured
Capacitor origin rather than relying on browser cookies across WebViews. The
proof stays in app sessionStorage for the active attempt. Interrupted sign-in
should be restarted. Do not enable the confidential token proxy for this public
client flow. Test cancellation, invalid state, expiry, and real Bungie sign-in on
a device before release; CI uses no Bungie credentials.

## Simulator CI

`.github/workflows/ios.yml` runs on manual dispatch and relevant pull requests.
It builds with `https://example.invalid`, syncs the checked-in native scaffold,
builds without signing, selects an available iPhone simulator, installs and
launches the app, and uploads a zipped simulator `.app` plus `ios-sim.png`.
The placeholder API cannot serve data; this is a launch check, not a live OAuth
or backend integration test. The simulator app cannot be installed on a physical
device or submitted to the App Store. Xcode/simulator execution requires macOS.

## Signing and distribution

For physical devices and distribution, obtain an Apple Developer account yourself.
Register a unique bundle ID in your team, replace the placeholder ID in Capacitor
config and Xcode, and confirm the URL scheme remains registered in Info.plist.
Select your team in Xcode Signing & Capabilities and configure development and
App Store provisioning/signing. Keep certificates, profiles, account credentials,
and signing keys outside the repository. Validate a signed device build against
your hosted server before archiving a Release build.

When ready, create the app record in App Store Connect, archive and validate in
Xcode, and upload using your own signing credentials. Use TestFlight for internal
and external testing, then prepare App Store metadata, privacy disclosures,
review access/instructions, and submit manually. Nothing in this repository
creates accounts, uploads a build, or submits for review.

Review the current Bungie API terms and trademark permissions before release.
Do not imply Bungie endorsement or use Bungie/Destiny names, logos, screenshots,
or other protected assets without appropriate rights. The wrapper display name
is Ghost Companion; existing product code has not been renamed. Explain the app's
companion functionality and provide reviewers a working hosted service. Disclose
which third-party AI provider receives prompts and keys, how users remove keys,
and what the hosted server stores. Keychain protects keys at rest on the device;
it does not make requests invisible to the hosted server or selected provider.
Assess App Store requirements for AI content, privacy, account deletion where
applicable, and useful native functionality before submission.

## Dependency and container checks

Capacitor core/ios/cli are pinned at 8.5.3; app is 8.1.2, browser 8.0.5, and
secure-storage 8.0.1 targets Capacitor 8. The CLI's `xcode` dependency uses a
`uuid` 11.1.1 override to remove its vulnerable older version while retaining the
CommonJS `v4()` API used by xcode. Recheck the override when upgrading Capacitor.

Docker CI builds the image, checks hosted `/health` and security headers, then
fails on fixable HIGH/CRITICAL vulnerabilities. The runtime upgrades Debian
packages and pip/setuptools/wheel during build. Trivy action v0.35.0 is pinned to
`57a97c7e7821a5776cebc9bb87c984fa69cba8f1`, verified with
`git ls-remote https://github.com/aquasecurity/trivy-action 'refs/tags/*'` and the
[upstream incident advisory](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23).
The advisory identifies v0.35.0 as unaffected by the March 2026 tag compromise;
older tags, including v0.33.1, should not be selected merely by version number.
The scanner is explicitly set to v0.69.3, avoiding the compromised v0.69.4 release.
