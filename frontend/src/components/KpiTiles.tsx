import type { CSSProperties } from "react";
import type { Metrics } from "../api/types";
import { fmtCompact, fmtDecimal, fmtDuration, fmtPct } from "../format";

interface Tile {
  label: string;
  value: string;
  note?: string;
  tone: string; // CSS color token for stripe/wash (DESIGN.md "KPI tones")
  status?: string; // CSS color token, always paired with the note text
}

function buildTiles(m: Metrics): Tile[] {
  return [
    { label: "Total de chamados", value: fmtCompact(m.total), tone: "var(--series-7)" },
    { label: "Abertos", value: fmtCompact(m.open), note: `${fmtCompact(m.open_late)} em atraso`, status: "var(--critical)", tone: "var(--series-1)" },
    { label: "Fechados", value: fmtCompact(m.closed), note: `${fmtCompact(m.canceled)} cancelados`, tone: "var(--series-3)" },
    { label: "No SLA de solução", value: fmtPct(m.pct_sla), note: `${fmtCompact(m.on_time)} no prazo`, status: "var(--good)", tone: "var(--good)" },
    { label: "Atrasados (SLA)", value: fmtCompact(m.late), note: `${fmtCompact(m.no_sla)} sem SLA`, status: "var(--critical)", tone: "var(--critical)" },
    { label: "Média de dias de atraso", value: fmtDecimal(m.avg_late_days), note: `máx. ${fmtDecimal(m.max_late_days)} dias`, tone: "var(--critical)" },
    { label: "Estágio vencido (abertos)", value: fmtCompact(m.stage_late), status: "var(--serious)", note: "prazo do estágio", tone: "var(--serious)" },
    { label: "Tempo médio de resolução", value: fmtDuration(m.avg_resolution_hours), note: `aberto mais antigo: ${fmtDecimal(m.max_open_age_days)} d`, tone: "var(--series-4)" },
  ];
}

export function KpiTiles({ metrics }: { metrics: Metrics | undefined }) {
  if (!metrics) return <div className="kpis" aria-busy="true" />;
  return (
    <div className="kpis">
      {buildTiles(metrics).map((tile) => (
        <div key={tile.label} className="kpi" style={{ "--tone": tile.tone } as CSSProperties}>
          <div className="kpi-label">{tile.label}</div>
          <div className="kpi-value">{tile.value}</div>
          {tile.note && (
            <div className="kpi-note">
              {tile.status && <span className="dot" style={{ background: tile.status }} aria-hidden="true" />}
              {tile.note}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
