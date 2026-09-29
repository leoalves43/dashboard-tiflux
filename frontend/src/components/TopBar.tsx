import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useFetch } from "../api/useFetch";
import { PAGES, type PageId } from "../filters/route";
import { fmtDateTime, fmtInt } from "../format";
import { applyTheme, readStoredTheme, type ThemeChoice as Theme } from "../themePreference";

const SYNC_POLL_MS = 60_000;

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readStoredTheme);
  useEffect(() => applyTheme(theme), [theme]);
  const next: Record<Theme, Theme> = { system: "light", light: "dark", dark: "system" };
  const label: Record<Theme, string> = { system: "Tema: sistema", light: "Tema: claro", dark: "Tema: escuro" };
  return <button type="button" className="btn" onClick={() => setTheme(next[theme])}>{label[theme]}</button>;
}

function SyncBadge() {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setTick((t) => t + 1), SYNC_POLL_MS);
    return () => window.clearInterval(timer);
  }, []);
  const status = useFetch((s) => api.syncStatus(s), String(tick)).data;
  if (!status) return null;
  const color = status.backfill_done ? "var(--good)" : "var(--serious)";
  const text = status.backfill_done
    ? `Atualizado ${fmtDateTime(status.last_incremental)}`
    : `Carga inicial em andamento (${fmtInt(status.tickets)} chamados)`;
  return <span className="badge muted"><span className="dot" style={{ background: color }} aria-hidden="true" />{text}</span>;
}

export function TopBar({ page, onPage }: { page: PageId; onPage: (page: PageId) => void }) {
  return (
    <header className="topbar">
      <span className="brand">Dashboard Tiflux</span>
      <nav className="tabs" aria-label="Seções">
        {PAGES.map((p) => (
          <button key={p.id} type="button" className="tab" aria-current={p.id === page ? "page" : undefined} onClick={() => onPage(p.id)}>
            {p.label}
          </button>
        ))}
      </nav>
      <div className="topbar-end">
        <SyncBadge />
        <ThemeToggle />
      </div>
    </header>
  );
}
