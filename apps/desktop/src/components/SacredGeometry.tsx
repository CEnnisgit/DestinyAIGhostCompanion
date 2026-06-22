import { GhostMark } from "./GhostMark";

// Deterministic pseudo-random so the starfield is stable between renders.
function rng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
}

function starfield(count: number) {
  const rand = rng(1337);
  return Array.from({ length: count }, () => ({
    x: rand() * 960,
    y: rand() * 600,
    r: rand() * 1.0 + 0.2,
    o: rand() * 0.45 + 0.1,
  }));
}

// Planet-spheres placed symmetrically on an orbital ring.
function orbit(cx: number, cy: number, radius: number, count: number, phase: number, size: number) {
  return Array.from({ length: count }, (_, i) => {
    const a = ((i * 360) / count + phase) * (Math.PI / 180);
    return { x: cx + Math.cos(a) * radius, y: cy + Math.sin(a) * radius, size };
  });
}

/// A clean, symmetric, sphere-themed backdrop: concentric orbital rings with
/// planet-spheres on them, and a faint starfield. The center is kept clear so
/// the Ghost has room to breathe.
export function SacredBackground() {
  const cx = 480;
  const cy = 300;
  const field = starfield(70);
  const rings = [150, 250, 360, 480, 620, 770];
  const orbits = [
    { r: 360, count: 6, phase: 30, size: 13, cls: "orbit-a" },
    { r: 480, count: 6, phase: 0, size: 10, cls: "orbit-b" },
    { r: 620, count: 6, phase: 30, size: 8, cls: "orbit-c" },
  ];

  return (
    <svg className="sacred-bg" viewBox="0 0 960 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <radialGradient id="planetGrad" cx="36%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#a6d4ff" stopOpacity="0.55" />
          <stop offset="55%" stopColor="#21314e" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#080e16" stopOpacity="0.5" />
        </radialGradient>
      </defs>

      {field.map((s, i) => (
        <circle key={`star${i}`} className="sg-star" cx={s.x} cy={s.y} r={s.r} style={{ opacity: s.o }} />
      ))}

      {rings.map((r) => (
        <circle key={`ring${r}`} className="sg-ring" cx={cx} cy={cy} r={r} />
      ))}

      {orbits.map((o) => (
        <g key={o.cls} className={`sg-orbit ${o.cls}`}>
          {orbit(cx, cy, o.r, o.count, o.phase, o.size).map((p, i) => (
            <g key={i}>
              <circle className="sg-planet" cx={p.x} cy={p.y} r={p.size} fill="url(#planetGrad)" />
              <circle className="sg-planet-rim" cx={p.x} cy={p.y} r={p.size} />
            </g>
          ))}
        </g>
      ))}
    </svg>
  );
}

/// The Ghost framed by a clean rotating rosette and a soft, breathing radiant
/// bloom of the Traveler's light — circular forms, no clutter.
export function GhostHalo() {
  const ticks = Array.from({ length: 24 }, (_, i) => i * 15);
  return (
    <div className="ghost-halo">
      <div className="halo-bloom" />
      <svg viewBox="0 0 200 200" className="halo-svg" aria-hidden="true">
        <g className="halo-spin">
          {ticks.map((a) => {
            const rad = (a * Math.PI) / 180;
            return (
              <line
                key={a}
                className="halo-tick"
                x1={100 + Math.cos(rad) * 72}
                y1={100 + Math.sin(rad) * 72}
                x2={100 + Math.cos(rad) * 86}
                y2={100 + Math.sin(rad) * 86}
              />
            );
          })}
          <circle className="halo-ring" cx="100" cy="100" r="86" />
        </g>
        <circle className="halo-ring faint" cx="100" cy="100" r="62" />
        <circle className="halo-ring" cx="100" cy="100" r="44" />
      </svg>
      <div className="halo-center">
        <GhostMark size={56} glow />
      </div>
    </div>
  );
}
