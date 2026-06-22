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

export class GhostBackend {
  constructor(public baseURL: string) {}

  private url(path: string): string {
    return new URL(path, this.baseURL).toString();
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
