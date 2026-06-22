import { useEffect, useMemo, useState } from "react";
import { GhostBackend, type LoreCategory, type LoreEntry } from "../api";
import { useGhost } from "../store";
import { CloseIcon } from "./Icons";

export function LoreCodex({ onClose }: { onClose: () => void }) {
  const { backendURL } = useGhost();
  const backend = useMemo(() => new GhostBackend(backendURL), [backendURL]);

  const [categories, setCategories] = useState<LoreCategory[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [entries, setEntries] = useState<LoreEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const selectCategory = (category: string) => {
    setActive(category);
    setQuery("");
    setLoading(true);
    backend
      .loreBrowse(category)
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  };

  const runSearch = (q: string) => {
    setQuery(q);
    if (!q.trim()) {
      if (active) selectCategory(active);
      return;
    }
    setActive(null);
    setLoading(true);
    backend
      .loreSearch(q)
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    backend
      .loreCategories()
      .then((cats) => {
        setCategories(cats);
        if (cats.length) selectCategory(cats[0].category);
      })
      .catch(() => setCategories([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backend]);

  return (
    <div className="scrim center" onClick={onClose}>
      <div className="modal codex" onClick={(e) => e.stopPropagation()}>
        <div className="codex-head">
          <h3>Lore Codex</h3>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <CloseIcon />
          </button>
        </div>

        <input
          className="text-input"
          placeholder="Search the Codex…"
          value={query}
          onChange={(e) => runSearch(e.target.value)}
          spellCheck={false}
        />

        <div className="codex-body">
          <div className="codex-cats">
            {categories.map((c) => (
              <button
                key={c.category}
                className={"cat-chip" + (c.category === active ? " active" : "")}
                onClick={() => selectCategory(c.category)}
              >
                {c.category}
                <span className="cat-count">{c.count}</span>
              </button>
            ))}
          </div>

          <div className="codex-entries">
            {loading && <p className="muted">Loading…</p>}
            {!loading && entries.length === 0 && <p className="muted">No entries.</p>}
            {entries.map((e, i) => (
              <div key={i} className="lore-entry">
                <div className="lore-entry-head">
                  <span className="lore-name">{e.name}</span>
                  {e.category && <span className="lore-cat">{e.category}</span>}
                </div>
                <p className="lore-desc">{e.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
