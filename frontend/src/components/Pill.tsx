import type { CSSProperties, ReactNode } from "react";

/** Tinted label with a dot; color never stands alone. Example: <Pill tone="var(--good)">No prazo</Pill> */
export function Pill({ tone, children }: { tone: string; children: ReactNode }) {
  return (
    <span className="pill" style={{ "--tone": tone } as CSSProperties}>
      <span className="dot" aria-hidden="true" />
      {children}
    </span>
  );
}
