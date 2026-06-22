// Client for the Ghost Companion Rust backend (apps/server).

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
  constructor(public baseURL: string) {}

  private url(path: string): string {
    return new URL(path, this.baseURL).toString();
  }

  private async postJSON<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(this.url(path), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`POST ${path} failed (${res.status})`);
    return res.json();
  }

  // --- Cross-device chat sync ---

  async listConversations(membershipId: string): Promise<SyncedThreadSummary[]> {
    const res = await fetch(this.url(`/conversations?membership_id=${encodeURIComponent(membershipId)}`));
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
    const res = await fetch(
      this.url(`/conversations/${encodeURIComponent(id)}?membership_id=${encodeURIComponent(membershipId)}`),
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
      { method: "DELETE" },
    );
  }

  /// Sends a chat message; when conversationId is given the server persists the
  /// turn (so it syncs across devices) and grounds the reply in live game data.
  async chat(message: string, membershipId?: string, conversationId?: string): Promise<string> {
    const data = await this.postJSON<{ reply: string }>("/chat", {
      message,
      membership_id: membershipId,
      conversation_id: conversationId,
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

  voiceSocketURL(opts: { membershipId?: string; characterId?: string } = {}): string {
    const u = new URL(this.url("/ws/voice"));
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    if (opts.membershipId) u.searchParams.set("membership_id", opts.membershipId);
    if (opts.characterId) u.searchParams.set("character_id", opts.characterId);
    return u.toString();
  }

  async characters(membershipId: string): Promise<CharacterSummary[]> {
    const res = await fetch(this.url(`/characters?membership_id=${encodeURIComponent(membershipId)}`));
    if (!res.ok) throw new Error(`characters request failed (${res.status})`);
    return res.json();
  }

  async profileSummary(membershipId: string): Promise<string> {
    const res = await fetch(this.url(`/profile/summary?membership_id=${encodeURIComponent(membershipId)}`));
    if (!res.ok) throw new Error(`profile request failed (${res.status})`);
    const data = (await res.json()) as { summary: string };
    return data.summary;
  }

  async activitySummary(membershipId: string): Promise<ActivitySummary> {
    const res = await fetch(this.url(`/activity/summary?membership_id=${encodeURIComponent(membershipId)}`));
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
