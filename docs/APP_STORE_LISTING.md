# App Store Connect — Listing Draft

Paste-ready metadata for the App Store Connect record. Character limits are
Apple's; every field below fits its limit.

---

## App name (30 chars max)

> Ghost Companion for Destiny

(26 chars. "Destiny" in a descriptive "for X" phrasing is standard for companion
apps and consistent with Bungie's API ToS, which permits third-party apps but
not implied endorsement — the disclaimer appears in the description, in-app, and
in the privacy policy.)

## Subtitle (30 chars max)

> Your AI Ghost. Lore & gear.

(27 chars.)

## Category

- Primary: **Utilities**
- Secondary: **Reference**

## Description (4000 chars max)

> Every Guardian deserves a Ghost.
>
> Ghost Companion puts an AI Ghost in your pocket — a conversational companion
> for Destiny that knows the lore, knows your Guardian, and can actually move
> your gear.
>
> TALK TO YOUR GHOST
> Ask anything, by voice or text. Your Ghost answers in character, grounded in
> the game's actual lore archive — not guesses. It remembers the conversation,
> so you can follow up naturally.
>
> IT KNOWS YOUR LEGEND
> Sign in with Bungie and your Ghost greets you by your record: your class, your
> light, your hours, your recent runs. Ask "what did I play this week?" or
> "who was in my fireteam for the raid?"
>
> QUICK GEAR SWAPS
> "Equip my hand cannon." "Pull my postmaster." "Send that to the vault." Your
> Ghost does it in-game while you stay on the couch — no vault screen spelunking.
>
> THE LORE CODEX
> Browse the recorded history of the Destiny universe — from the Traveler's
> arrival to the war against the Witness — across twenty categories, with
> full-text search and official Grimoire entries from both Destiny 1 and
> Destiny 2. Or tap "Surprise me" and wander.
>
> SYNCED EVERYWHERE
> Your conversations follow you across devices when you sign in. Sign out and
> they stay private to the device.
>
> BUILT LIKE IT SHOULD BE
> • Voice recognition runs on your device whenever your language supports it
> • Your Bungie sign-in uses official Bungie OAuth — we never see your password
> • Delete your account (and everything we store) any time, right in Settings
>
> Ghost Companion is an unofficial, fan-made app. It is not affiliated with,
> endorsed by, or sponsored by Bungie, Inc. Destiny, the Destiny logo, and the
> Ghost are trademarks of Bungie, Inc. Game data is provided by the official
> Bungie API. A free Bungie account is required for personalized features;
> lore browsing works without signing in.

## Keywords (100 chars max)

> destiny,ghost,guardian,lore,grimoire,vault,loadout,raid,bungie,companion,exotic,triumph

(92 chars. Don't waste keyword space on "destiny 2" — multi-word terms are
matched from combinations of single keywords.)

## Promotional text (170 chars max, editable without a new build)

> The Ghost that knows your legend: lore answers with receipts, your career at
> a glance, and gear swaps by voice — without leaving the couch.

## Support URL

`https://github.com/CEnnisgit/DestinyAIGhostCompanion` (or a dedicated page)

## Privacy Policy URL

Host `PRIVACY.md` publicly first (GitHub Pages works; App Review just needs a
reachable URL). Placeholder in-app is `https://ghostcompanion.app/privacy` —
**the Settings link and this field must match wherever it's actually hosted.**

## Age rating

Answer the questionnaire honestly; expected outcome **12+** (infrequent/mild
fantasy violence via Destiny imagery/lore text). Everything else: None.

---

## App Privacy ("nutrition labels")

Declare **Data Linked to You**:

| Data type | Category | Purpose | Notes |
|---|---|---|---|
| User ID | Identifiers | App Functionality | Bungie membership id, keys tokens + conversations |
| Other User Content | User Content | App Functionality | Chat messages, stored server-side for cross-device sync |
| Gameplay Content | User Content | App Functionality | Destiny characters/inventory/activity read via Bungie API |

Declare **NOT collected**: location, contacts, browsing history, purchases,
health, financial info, photos, emails, phone number, name.

**Audio**: microphone audio is processed for transcription but not stored or
transmitted by us (on-device where the language supports it; otherwise Apple's
speech service under Apple's policy). Only the resulting *text* is sent, as part
of chat — covered by "Other User Content" above.

**Tracking**: **No** (nothing is used for cross-app tracking or advertising).
No third-party analytics SDKs are present.

Chat text is sent to the configured LLM provider (e.g. OpenAI) to generate
replies — that's disclosed in the privacy policy; in the labels it stays under
App Functionality (it is not "tracking" and not shared for advertising).

---

## App Review — Sign-In Information + Notes

Fill the **Sign-in required** fields with a throwaway Bungie account that owns
at least one Destiny 2 character with gear (create it fresh; do NOT hand over a
real account). Suggested review notes:

> Ghost Companion is a companion app for the game Destiny 2, using Bungie's
> official public API (https://bungie-net.github.io). Sign in with the provided
> demo Bungie account via the in-app "Sign in with Bungie" button (official
> Bungie OAuth in a system browser sheet).
>
> • Voice/chat: ask e.g. "Tell me about the Traveler" (lore) or "What did I
>   play recently?" (activity history).
> • Lore Codex: book icon — browsable without any sign-in.
> • Gear commands ("equip", "vault", "pull postmaster") move items on the demo
>   account's Destiny character, visible in-game.
> • Account deletion: Settings → Delete Account (erases server-side data and
>   revokes sessions).
>
> The app is an unofficial fan project and displays a "not affiliated with
> Bungie" disclaimer in Settings, the App Store description, and the privacy
> policy. No Bungie logos or artwork are used in the icon or branding.

---

## Screenshots (required sizes)

| Slot | Device class | Pixels | Source simulator |
|---|---|---|---|
| 6.9" (required) | iPhone 16 Pro Max / 15 Pro Max | 1320 × 2868 | iPhone 16 Pro Max |
| 6.5" (required until 6.9" covers it — upload if asked) | iPhone 11 Pro Max / XS Max | 1242 × 2688 | iPhone 11 Pro Max |

Suggested shots (portrait, in order):
1. Chat with the Ghost mid-conversation (lore answer with intent tag)
2. Empty state with the personalized Guardian dossier greeting
3. Lore Codex category browser
4. A lore entry with OFFICIAL badge
5. Activity Log timeline
6. Voice input active (mic live, transcript forming)

No device frames or marketing text needed for v1 — clean app captures are fine.

---

## Version info

- Version: `1.0`, Build: `1` (already set in Info.plist)
- Copyright: `© 2026 Chris Ennis`
- What's New: n/a for first release
