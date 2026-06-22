import { GhostMark } from "./GhostMark";

/// Faint full-bleed "director" backdrop: orbital rings, a fine grid, and a
/// radial dotted burst from a sun mandala — Destiny's sacred-geometry motif.
export function SacredBackground() {
  const sun = { x: 880, y: 70 };
  const spokes = Array.from({ length: 56 }, (_, i) => (i * 360) / 56);
  const grid = { h: [120, 240, 360, 480], v: [160, 320, 480, 640, 800] };
  const rings = [130, 230, 350, 480, 620, 770];

  return (
    <svg className="sacred-bg" viewBox="0 0 960 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {grid.h.map((y) => (
        <line key={`h${y}`} className="sg-grid" x1="0" y1={y} x2="960" y2={y} />
      ))}
      {grid.v.map((x) => (
        <line key={`v${x}`} className="sg-grid" x1={x} y1="0" x2={x} y2="600" />
      ))}

      {rings.map((r) => (
        <circle key={`ring${r}`} className="sg-ring" cx="280" cy="660" r={r} />
      ))}

      {spokes.map((a) => {
        const rad = (a * Math.PI) / 180;
        return (
          <line
            key={`s${a}`}
            className="sg-spoke"
            x1={sun.x}
            y1={sun.y}
            x2={sun.x + Math.cos(rad) * 980}
            y2={sun.y + Math.sin(rad) * 980}
          />
        );
      })}

      <circle className="sg-mandala" cx={sun.x} cy={sun.y} r="40" />
      <circle className="sg-mandala" cx={sun.x} cy={sun.y} r="26" />
      <circle className="sg-mandala-core" cx={sun.x} cy={sun.y} r="6" />
    </svg>
  );
}

/// The Ghost framed by a rotating rosette of concentric rings + radial ticks,
/// like a planet node in the Destiny director.
export function GhostHalo() {
  const ticks = Array.from({ length: 24 }, (_, i) => i * 15);
  return (
    <div className="ghost-halo">
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
