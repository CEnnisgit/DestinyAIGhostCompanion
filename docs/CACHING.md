Caching in Simple Terms

What is caching?
- Caching is just “remembering” a recent answer so we don’t have to ask the server again right away.
- We set a short time window for how long we keep that answer. When time is up, we fetch fresh data.

Where we cache
- Manifest (game definitions): Big, slow to download, changes rarely.
  - We keep it in memory for a while (manifest_ttl). This speeds up any feature that needs definitions.
- Profile data (your Guardian overview): Often requested a lot in a short time.
  - We keep each unique profile request for a short time (profile_ttl) to avoid repeated network calls.
- Item definitions (single inventory item info by hash):
  - We keep them in memory and also save them to a small JSON file under `cache/item_defs.json` so repeated runs can reuse them.

How it works in code (BungieClient)
- Manifest cache: `_manifest_cache = (data, expiry_timestamp)`
  - If there’s a cached value and it hasn’t expired, return it.
  - Otherwise, fetch from the API, store it with a new expiry, and return it.
- Profile cache: `_profile_cache[(membership_type, membership_id, components)] = (data, expiry)`
  - The “key” includes which profile and which ‘components’ you asked for, because those change the answer.
- Item definition cache: `_entity_cache` (in-memory) and `cache/item_defs.json` (on disk)
  - We first check memory, then disk, then fall back to the network. After we fetch, we save it to both memory and disk.

Why not cache everything forever?
- The game state and profile data change as you move items and play. We only cache briefly so the app stays responsive without going stale.

When you might change TTLs
- If you’re doing a lot of repeated calls (like listing inventory and then quickly looking at details), increasing `profile_ttl` from 60 to ~120 seconds might reduce network calls. If you need up-to-the-second freshness, lower it.

How to clear caches
- Manifest/profile: restart the app or wait for the TTL to expire.
- Item definitions on disk: delete `cache/item_defs.json` and they’ll be re-fetched.

