# Ghost Companion — iOS Client

> **Status:** 🟢 In progress (Phase 5, iOS) — scaffold + sign-in + on-device voice
> **Stack:** Swift 5.9 / SwiftUI, talks to `apps/server` over HTTP + WebSocket

Native iOS companion app connecting to the Rust backend. Chosen over the
roadmap's Electron presentation to target the iOS App Store.

## Structure

```
GhostCompanion/
  App/         GhostCompanionApp (entry, injects stores)
  Auth/        AuthStore — Bungie OAuth via ASWebAuthenticationSession
  Networking/  GhostBackend — /health, /auth/login, /ws/voice
  Models/      VoiceTurn — Codable WS frames + ChatMessage
  State/       GhostSession (connectivity + voice socket), KeychainStore
  Voice/       VoiceRecognizer — on-device SFSpeechRecognizer capture
  Views/       RootView, VoiceChatView, SettingsView
  Theme/       GhostTheme
  Assets.xcassets/  AppIcon + AccentColor
```

## Build & run

```bash
cd apps/ios
xcodegen generate          # regenerates GhostCompanion.xcodeproj (gitignored)
open GhostCompanion.xcodeproj
```

Command-line build for the simulator (no signing needed):

```bash
xcodebuild -project GhostCompanion.xcodeproj -scheme GhostCompanion \
  -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17' \
  CODE_SIGNING_ALLOWED=NO build
```

Point the app at your backend in **Settings** (default `http://localhost:8080`
for a backend running on your Mac). Use an **HTTPS** URL for production — the
localhost ATS exception in `Info.plist` is dev-only.

## Bungie sign-in

The native flow needs the backend to redirect to the app's URL scheme. Set on
the server:

```
GHOST_MOBILE_CALLBACK=ghostcompanion://auth
```

and register the backend's `/auth/callback` as the redirect URI in your Bungie
application. Then **Settings → Sign in with Bungie**.

## Before App Store submission

- Set `DEVELOPMENT_TEAM` in `project.yml` (needs an Apple Developer account).
- Drop a real 1024×1024 icon into `Assets.xcassets/AppIcon.appiconset`.
- Remove the localhost ATS exception; ship against HTTPS.
- Add a privacy policy + App Privacy labels (Bungie account, microphone/speech).

See `archive/legacy-ios/` for the original experimental Swift app.
