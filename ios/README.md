# iOS App

Ghost Companion now includes a native SwiftUI iPhone client in `ios/`.

## What It Uses

- The existing FastAPI backend remains the source of truth.
- Bungie OAuth still happens through the backend.
- Inventory actions still flow through preview then execute automatically.
- Chat uses the existing `/chat/stream` endpoint.

## Generate The Xcode Project

This folder uses XcodeGen so the project can live cleanly in the repo without hand-editing `.xcodeproj` files here on Windows.

On a Mac:

```bash
cd ios
xcodegen generate
open GhostCompanion.xcodeproj
```

## Required App Setup

- Set the backend base URL in the app to a server your simulator or iPhone can reach.
- Configure the Bungie redirect URI to point to your backend mobile callback:
  - `https://your-server.example.com/oauth/mobile/callback`
  - or `http://<lan-ip>:8000/oauth/mobile/callback` for local device testing
- The native app expects the custom callback scheme `ghostcompanion://auth`.

## Current Mobile Scope

- Typed chat
- Conversation list / open / create
- Inventory browsing
- Equip / vault / move / postmaster pull
- Backend account status and app settings

Voice parity is not complete on iPhone yet. The mobile app is structured for it, but this pass prioritizes typed chat and gear management first.
