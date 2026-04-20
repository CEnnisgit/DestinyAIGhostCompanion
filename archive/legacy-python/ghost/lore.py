from __future__ import annotations

"""Lightweight lore retriever for Destiny content.

This module loads plain-text or Markdown lore snippets from ``data/lore`` and
returns the top-k passages for a query using a simple word-overlap scoring.

The design intentionally avoids heavy dependencies so it works in desktop
bundles. You can later swap the scorer for embeddings/FAISS without changing
the public API.
"""

import os
from pathlib import Path
from typing import List, Tuple
import re

_LORE_DIR = Path(os.getcwd()) / "data" / "lore"
_DOCS: list[tuple[str, str]] | None = None  # (id, text)


def _normalize(text: str) -> list[str]:
    text = text.lower()
    # keep alphanumerics and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if t]


def _load_docs() -> list[tuple[str, str]]:
    global _DOCS
    if _DOCS is not None:
        return _DOCS
    docs: list[tuple[str, str]] = []
    if not _LORE_DIR.exists():
        _DOCS = []
        return _DOCS
    for p in _LORE_DIR.rglob("*.md"):
        try:
            docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            pass
    for p in _LORE_DIR.rglob("*.txt"):
        try:
            docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            pass
    _DOCS = docs
    return _DOCS


def search(query: str, k: int = 3) -> List[Tuple[str, str, float]]:
    """Return top-k lore passages for ``query``.

    Returns a list of tuples: (doc_id, snippet, score)
    """
    docs = _load_docs()
    if not docs or not query.strip():
        return []
    q_tokens = _normalize(query)
    if not q_tokens:
        return []
    q_set = set(q_tokens)
    scored: list[tuple[str, str, float]] = []
    for doc_id, text in docs:
        # Sentence-level snippets for better granularity
        parts = re.split(r"(?<=[.!?])\s+", text)
        best = ("", 0.0)
        for s in parts:
            tks = set(_normalize(s))
            if not tks:
                continue
            overlap = len(q_set & tks)
            if overlap == 0:
                continue
            score = overlap / max(3, len(tks))
            if score > best[1]:
                best = (s.strip(), score)
        if best[1] > 0:
            scored.append((doc_id, best[0], best[1]))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:k]

