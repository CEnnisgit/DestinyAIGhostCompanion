-- Track where each lore entry came from so official Bungie API content is
-- preferred over the curated paraphrase fallback.
--   'bungie'  = Bungie manifest / D1 Grimoire (authoritative, verbatim)
--   'import'  = user-provided JSONL dataset
--   'curated' = hand-written paraphrased seed (fallback only)
ALTER TABLE destiny_lore ADD COLUMN IF NOT EXISTS source TEXT;
