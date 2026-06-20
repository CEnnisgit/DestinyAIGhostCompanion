export function GhostMark({ size = 28, glow = false }: { size?: number; glow?: boolean }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className={glow ? "ghost-mark glow" : "ghost-mark"}
      aria-hidden="true"
    >
      <g transform="rotate(45 50 50)">
        <rect x="22" y="22" width="56" height="56" rx="10" fill="none" stroke="var(--accent)" strokeWidth="6" />
        <rect
          x="34"
          y="34"
          width="32"
          height="32"
          rx="7"
          fill="none"
          stroke="var(--accent)"
          strokeOpacity="0.45"
          strokeWidth="4"
        />
      </g>
      <circle cx="50" cy="50" r="9" fill="var(--accent-bright)" />
    </svg>
  );
}
