-- Cross-device chat sync: conversations are stored server-side, keyed by the
-- owning Guardian (Bungie membership id), so they follow the user across web,
-- iOS, and desktop. Backs the chats domain's ChatStorePort.
CREATE TABLE IF NOT EXISTS chat_threads (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT 'New Conversation',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Listing a user's threads, most-recently-updated first.
CREATE INDEX IF NOT EXISTS chat_threads_owner_idx ON chat_threads (owner_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id   UUID NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,          -- 'guardian' | 'ghost'
    body        TEXT NOT NULL,
    intent      TEXT,                   -- optional intent label from the backend
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Replaying a thread in order.
CREATE INDEX IF NOT EXISTS chat_messages_thread_idx ON chat_messages (thread_id, created_at);
