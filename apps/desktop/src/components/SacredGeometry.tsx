import { GhostMark } from "./GhostMark";

// Deterministic pseudo-random so the starfield is stable between renders.
function stars(count: number) {
  let seed = 1337;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  return Array.from({ length: count }, () => ({
    x: rand() * 960,
    y: rand() * 600,
    r: rand() * 1.1 + 0.2,
    o: rand() * 0.5 + 0.1,
  }));
}

// Points of an N-point star (alternating outer/inner radius), centered at (cx, cy).
function starPoints(cx: number, cy: number, outer: number, inner: number, points: number) {
  const pts: string[] = [];
  for (let i = 0; i < points * 2; i += 1) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (i * Math.PI) / points - Math.PI / 2;
    pts.push(`${(cx + Math.cos(a) * r).toFixed(1)},${(cy + Math.sin(a) * r).toFixed(1)}`);
  }
  return pts.join(" ");
}

/// A symmetric, radially-centered sacred-geometry backdrop: a starfield, a
/// Flower-of-Life seed, concentric rings, evenly-spaced radial spokes, and a
/// faceted star — all centered for a divine, balanced feel.
export function SacredBackground() {
  const cx = 480;
  const cy = 300;
  const field = stars(90);
  const rings = [70, 150, 240, 340, 450, 580, 720];
  const spokes = Array.from({ length: 48 }, (_, i) => (i * 360) / 48);
  // Flower of Life seed: a central circle ringed by six, hexagonally.
  const seedR = 40;
  const seed = [[cx, cy], ...Array.from({ length: 6 }, (_, i) => {
    const a = (i * Math.PI) / 3;
    return [cx + Math.cos(a) * seedR, cy + Math.sin(a) * seedR];
  })];

  return (
    <svg className="sacred-bg" viewBox="0 0 960 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {field.map((s, i) => (
        <circle key={`star${i}`} className="sg-star" cx={s.x} cy={s.y} r={s.r} style={{ opacity: s.o }} />
      ))}

      {/* Symmetric concentric rings */}
      {rings.map((r) => (
        <circle key={`ring${r}`} className="sg-ring" cx={cx} cy={cy} r={r} />
      ))}

      {/* Evenly-spaced radial spokes from the center */}
      {spokes.map((deg) => {
        const a = (deg * Math.PI) / 180;
        return (
          <line
            key={`s${deg}`}
            className="sg-spoke"
            x1={cx + Math.cos(a) * 70}
            y1={cy + Math.sin(a) * 70}
            x2={cx + Math.cos(a) * 760}
            y2={cy + Math.sin(a) * 760}
          />
        );
      })}

      {/* Centered faceted star + Flower-of-Life seed + core */}
      <polygon className="sg-star-seal" points={starPoints(cx, cy, 120, 56, 12)} />
      {seed.map(([x, y], i) => (
        <circle key={`seed${i}`} className="sg-seed" cx={x} cy={y} r={seedR} />
      ))}
      <circle className="sg-mandala" cx={cx} cy={cy} r="34" />
    </svg>
  );
}

/// The Ghost framed by a rotating rosette + a soft radiant bloom of light.
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
        <g className="halo-spin-rev">
          <polygon className="halo-star" points={starPoints(100, 100, 60, 30, 8)} />
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
