# Ghost Companion — Privacy Policy

_Last updated: 2026-06-22_

Ghost Companion ("the app") is an unofficial, fan-made companion for Destiny 2.
This policy explains what data the app handles and why. Host this document at a
public URL (e.g. `https://ghostcompanion.app/privacy`) and reference that URL in
App Store Connect and in the app's Settings screen.

## Who we are

Ghost Companion is an independent project. **It is not affiliated with, endorsed
by, or sponsored by Bungie, Inc.** Destiny and the Ghost are trademarks of
Bungie, Inc. Game data is accessed through Bungie's official, public API under
their API Terms of Use.

## What data we access

- **Bungie account data (via OAuth).** When you sign in with Bungie, we receive
  an OAuth access/refresh token that lets the app read your Destiny profile on
  your behalf: your characters, inventory, triumphs/records, and activity history
  (including activity dates and the other players in your fireteams). The app
  uses this solely to answer your questions and personalize your Ghost. We never
  ask for your Bungie password — authentication is handled entirely by Bungie.
- **Conversations.** Chats you have with the Ghost are stored on our backend,
  associated with your Bungie membership id, so they sync across your devices.
- **Microphone / speech (optional).** If you use voice input, speech is
  transcribed to text so the app can understand your command. Transcription uses
  Apple's on-device speech recognition where available.

## What we do NOT do

- We do not sell or share your personal data with third parties for advertising.
- We do not collect your Bungie password.
- We do not access data unrelated to Destiny.

## Third parties

- **Bungie API** — game data is read from `bungie.net`. Your use of Bungie's
  services is governed by Bungie's own privacy policy and terms.
- **Language model provider** — to generate conversational answers, the text of
  your message and relevant retrieved game/lore context may be sent to the
  configured language-model provider (e.g. OpenAI). Do not include sensitive
  personal information in messages.

## Data retention & deletion

- Your stored conversations remain until you delete them in the app or request
  account deletion.
- Signing out removes your session and stored Bungie tokens from the device.
- To request deletion of server-side data, contact the address below.

## Security

Bungie tokens and session credentials are transmitted over HTTPS and stored
server-side. Sessions are short-lived, signed tokens; the production backend
requires a valid session for any access to your data.

## Children

The app is not directed at children under 13.

## Contact

Questions or deletion requests: **support@ghostcompanion.app**

_Replace the contact address and policy URL with your real values before
submitting to the App Store._
