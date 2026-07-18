// Client for the Ghost Companion Rust backend (apps/server).

/// 429 from the backend: over the per-Guardian chat budget. Transient — the
/// server is fine, retry after a few seconds. Kept distinct so the UI doesn't
/// report a healthy rate limit as an outage.
export class RateLimitedError extends Error {
  constructor() {
    super("rate limited");
    this.name = "RateLimitedError";
  }
}

export interface CharacterSummary {
  characterId: string;
  classType: number;
  className: string;
  light: number;
}

export interface LoreEntry {
  name: string;
  description: string;
  category?: string;
  source?: string;
}

export interface LoreCategory {
  category: string;
  count: number;
}

export interface ActivityRecord {
  name: string;
  mode: string;
  period: string;
  completed: boolean;
  fireteam: string[];
  game: "Destiny1" | "Destiny2";
}

export interface ActivitySummary {
  narrative: string;
  recent: ActivityRecord[];
}

export interface SyncedThreadSummary {
  id: string;
  title: string;
  updated_at: string;
}

export interface SyncedMessage {
  id: string;
  role: "guardian" | "ghost";
  text: string;
  intent?: string | null;
  created_at: string;
}

export interface SyncedThread {
  id: string;
  title: string;
  updated_at: string;
  messages: SyncedMessage[];
}

export class GhostBackend {
  constructor(public baseURL: string, private sessionToken?: string) {}

  private url(path: string): string {
    return new URL(path, this.baseURL).toString();
  }

  /// Headers for an authenticated request — attaches the session bearer when set.
  private headers(extra?: Record<string, string>): Record<string, string> {
    const h: Record<string, string> = { ...(extra ?? {}) };
    if (this.sessionToken) h["Authorization"] = `Bearer ${this.sessionToken}`;
    return h;
  }

  /// Authenticated GET helper.
  private authedGet(path: string): Promise<Response> {
    return fetch(this.url(path), { headers: this.headers() });
  }

  private async postJSON<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(this.url(path), {
      method: "POST",
      headers: this.headers({ "content-type": "application/json" }),
      body: JSON.stringify(body),
    });
    if (res.status === 429) throw new RateLimitedError();
    if (!res.ok) throw new Error(`POST ${path} failed (${res.status})`);
    return res.json();
  }

  // --- Cross-device chat sync ---

  async listConversations(membershipId: string): Promise<SyncedThreadSummary[]> {
    const res = await this.authedGet(`/conversations?membership_id=${encodeURIComponent(membershipId)}`);
    if (!res.ok) throw new Error(`list conversations failed (${res.status})`);
    return (await res.json()).threads;
  }

  async createConversation(membershipId: string, title?: string): Promise<SyncedThreadSummary> {
    const data = await this.postJSON<{ thread: SyncedThreadSummary }>("/conversations", {
      membership_id: membershipId,
      title,
    });
    return data.thread;
  }

  async getConversation(membershipId: string, id: string): Promise<SyncedThread> {
    const res = await this.authedGet(
      `/conversations/${encodeURIComponent(id)}?membership_id=${encodeURIComponent(membershipId)}`,
    );
    if (!res.ok) throw new Error(`get conversation failed (${res.status})`);
    return (await res.json()).thread;
  }

  async renameConversation(membershipId: string, id: string, title: string): Promise<void> {
    await this.postJSON(`/conversations/${encodeURIComponent(id)}`, {
      membership_id: membershipId,
      title,
    }).catch(() => {});
  }

  async deleteConversation(membershipId: string, id: string): Promise<void> {
    await fetch(
      this.url(`/conversations/${encodeURIComponent(id)}?membership_id=${encodeURIComponent(membershipId)}`),
      { method: "DELETE", headers: this.headers() },
    );
  }

  /// Sends a chat message; when conversationId is given the server persists the
  /// turn (so it syncs across devices) and grounds the reply in live game data.
  /// When characterId is given, the Ghost can do quick gear swaps on it.
  async chat(
    message: string,
    membershipId?: string,
    conversationId?: string,
    characterId?: string,
  ): Promise<string> {
    const data = await this.postJSON<{ reply: string }>("/chat", {
      message,
      membership_id: membershipId,
      conversation_id: conversationId,
      character_id: characterId,
    });
    return data.reply;
  }

  async health(): Promise<boolean> {
    const res = await fetch(this.url("/health"));
    return res.ok && (await res.text()).includes("ok");
  }

  loginURL(): string {
    return this.url("/auth/login");
  }

  /// Revoke this session server-side (best-effort) so the token can't be reused.
  async logout(): Promise<void> {
    await fetch(this.url("/auth/logout"), { method: "POST", headers: this.headers() }).catch(() => {});
  }

  /// `DELETE /account` — permanently erase the Guardian's server-side data
  /// (Bungie tokens + synced conversations) and revoke their live sessions.
  /// Unlike `logout`, failure is thrown rather than swallowed: the caller must
  /// not tell the user their account was deleted unless the server said so.
  async deleteAccount(): Promise<void> {
    const res = await fetch(this.url("/account"), { method: "DELETE", headers: this.headers() });
    if (!res.ok) throw new Error(`account deletion failed (${res.status})`);
  }

  voiceSocketURL(opts: { membershipId?: string; characterId?: string } = {}): string {
    const u = new URL(this.url("/ws/voice"));
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    if (this.sessionToken) u.searchParams.set("session", this.sessionToken);
    if (opts.membershipId) u.searchParams.set("membership_id", opts.membershipId);
    if (opts.characterId) u.searchParams.set("character_id", opts.characterId);
    return u.toString();
  }

  async characters(membershipId: string): Promise<CharacterSummary[]> {
    const res = await this.authedGet(`/characters?membership_id=${encodeURIComponent(membershipId)}`);
    if (!res.ok) throw new Error(`characters request failed (${res.status})`);
    return res.json();
  }

  async profileSummary(membershipId: string): Promise<string> {
    const res = await this.authedGet(`/profile/summary?membership_id=${encodeURIComponent(membershipId)}`);
    if (!res.ok) throw new Error(`profile request failed (${res.status})`);
    const data = (await res.json()) as { summary: string };
    return data.summary;
  }

  async activitySummary(membershipId: string): Promise<ActivitySummary> {
    const res = await this.authedGet(`/activity/summary?membership_id=${encodeURIComponent(membershipId)}`);
    if (!res.ok) throw new Error(`activity request failed (${res.status})`);
    return res.json();
  }

  async loreCategories(): Promise<LoreCategory[]> {
    const res = await fetch(this.url("/lore/categories"));
    if (!res.ok) throw new Error(`lore categories failed (${res.status})`);
    return res.json();
  }

  async loreBrowse(category: string): Promise<LoreEntry[]> {
    const res = await fetch(this.url(`/lore/browse?category=${encodeURIComponent(category)}`));
    if (!res.ok) throw new Error(`lore browse failed (${res.status})`);
    return res.json();
  }

  async loreSearch(query: string): Promise<LoreEntry[]> {
    const res = await fetch(this.url(`/lore/search?q=${encodeURIComponent(query)}`));
    if (!res.ok) throw new Error(`lore search failed (${res.status})`);
    return res.json();
  }

  async loreRandom(n = 6): Promise<LoreEntry[]> {
    const res = await fetch(this.url(`/lore/random?n=${n}`));
    if (!res.ok) throw new Error(`lore random failed (${res.status})`);
    return res.json();
  }
}
