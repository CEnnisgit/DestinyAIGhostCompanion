// Client for the Ghost Companion Rust backend (apps/server).

export interface CharacterSummary {
  characterId: string;
  classType: number;
  className: string;
  light: number;
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
}
