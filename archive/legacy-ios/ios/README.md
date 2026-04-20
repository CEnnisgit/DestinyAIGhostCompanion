# Ghost Companion — iOS

Native SwiftUI client for the Destiny AI Ghost Companion FastAPI backend.

## Requirements

- macOS with Xcode 15 or later
- iOS 17 deployment target
- A running Ghost Companion backend reachable from your device or simulator
- A Bungie application registered at <https://www.bungie.net/en/Application> with `ghostcompanion://oauth/callback` set as an allowed redirect URI

## Quick start (recommended)

The Swift source, `Info.plist`, and asset catalog live under `GhostCompanion/`. The `.xcodeproj` is **not** committed — regenerate it from `project.yml` with [XcodeGen](https://github.com/yonaskolb/XcodeGen):

```bash
brew install xcodegen
cd ios
xcodegen generate
open GhostCompanion.xcodeproj
```

Then in Xcode:

1. Select the `GhostCompanion` target → **Signing & Capabilities** → set your Team.
2. Bundle Identifier stays `com.ghostcompanion.ios` (Keychain service name is derived from it).
3. Build and run on an iOS 17 simulator or device.

Re-run `xcodegen generate` any time you add or rename source files.

## Manual setup (fallback)

If you don't want to install XcodeGen, you can hand-wire the project:

1. In Xcode, choose **File → New → Project → iOS → App**.
2. Set:
   - **Product Name:** `GhostCompanion`
   - **Interface:** SwiftUI
   - **Language:** Swift
   - **Bundle Identifier:** `com.ghostcompanion.ios`
   - **Minimum Deployment:** iOS 17.0
3. Save the project inside `ios/` (so the new `GhostCompanion.xcodeproj` sits next to this README).
4. When Xcode finishes, delete the auto-generated `ContentView.swift`, `GhostCompanionApp.swift`, `Assets.xcassets`, and `Info.plist` it created inside the target folder — we'll replace them with the ones in this repo.
5. Drag the contents of `ios/GhostCompanion/` (everything: `GhostCompanionApp.swift`, `Info.plist`, `Assets.xcassets`, and the `Theme/`, `Models/`, `Networking/`, `Storage/`, `Auth/`, `Voice/`, `State/`, `Views/`, `Utilities/` folders) into the Xcode project navigator. Tick **Create groups** and **Add to target: GhostCompanion**.
6. In the target's **Info** tab, confirm that `Info.plist` is the one from this repo (`GhostCompanion/Info.plist`). Set it explicitly under **Build Settings → Info.plist File** if needed.
7. In **Signing & Capabilities**, set your Team. Keep the Bundle Identifier as `com.ghostcompanion.ios` (the Keychain service name is derived from it).
8. Add the `GhostCompanionTests` folder to a new **Unit Test** target named `GhostCompanionTests` if you want to run the smoke tests.
9. Build and run on an iOS 17 simulator or device.

## First run

1. The app opens to **Server Setup**. Enter the base URL of your backend — for example `http://192.168.1.10:8000` — and tap **Connect**. The app hits `/health` to validate.
2. Tap **Sign in with Bungie**. An `ASWebAuthenticationSession` opens Bungie's OAuth page; after you authorize, the callback returns to `ghostcompanion://oauth/callback`, the app posts the code to `/oauth/callback`, and the returned JWT is stored in Keychain.
3. Start a new chat, send a message, and you should see streaming tokens fill the assistant bubble.

## OAuth configuration

Register the redirect URI **exactly** at the Bungie portal:

```
ghostcompanion://oauth/callback
```

If you cannot modify the Bungie application, add a backend route `/oauth/callback/mobile` that 302-redirects to `ghostcompanion://oauth/callback?code=...` and point the iOS app at that instead (flagged in the plan as a fallback — not wired up by default).

## Voice

- **STT:** `SFSpeechRecognizer` runs on-device where supported, with a fallback that records m4a and uploads via `POST /stt` (converted to 16-bit PCM WAV).
- **TTS:** `AVSpeechSynthesizer` speaks assistant replies when the selected voice is `system`. ElevenLabs/pyttsx3 voices listed by the backend play server-side and will not be audible on iOS — see the open items section below.

## Info.plist keys already set

- `NSMicrophoneUsageDescription`
- `NSSpeechRecognitionUsageDescription`
- `NSLocalNetworkUsageDescription`
- `NSAppTransportSecurity.NSAllowsLocalNetworking = true`
- `CFBundleURLTypes` with scheme `ghostcompanion`

## Bungie API reference

All Bungie traffic is proxied through the FastAPI backend (`ghost/bungie.py`) — iOS never carries an `X-API-Key`. Treat the local `bungie_api_reference.json` as a point-in-time snapshot and cross-check against the live spec before adding fields to `Models/`:

- <https://github.com/Bungie-net/api>
- <https://bungie-net.github.io>
- <https://github.com/Bungie-net/api/wiki/OAuth-Documentation>
- <https://www.bungie.net/en/Application>

**Quarterly TODO:** re-sync `bungie_api_reference.json` against `Bungie-net/api` and diff breaking changes before cutting a new iOS build.

## Known limitations / follow-ups

- **TTS parity:** ElevenLabs voices are played on the server host, not on the iOS client. A future backend change could return audio bytes for iOS to play directly.
- **HTTPS:** Shipping outside of local networks requires a TLS-terminated backend. ATS exceptions are limited to local networking.
- **Bundle ID changes orphan Keychain entries:** the Keychain service string uses `Bundle.main.bundleIdentifier`. Changing the bundle id requires signing in again.
- **`.xcodeproj` not committed:** each clone creates its own so signing/team settings don't leak.
