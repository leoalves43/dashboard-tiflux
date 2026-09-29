import type { Metrics } from "../api/types";
import { fmtCompact, fmtDecimal, fmtDuration, fmtPct } from "../format";

interface Tile {
  label: string;
  value: string;
  note?: string;
  status?: string; // CSS color token, always paired with the note text
}

function buildTiles(m: Metrics): Tile[] {
  return [
    { label: "Total de chamados", value: fmtCompact(m.total) },
    { label: "Abertos", value: fmtCompact(m.open), note: `${fmtCompact(m.open_late)} em atraso`, status: "var(--critical)" },
    { label: "Fechados", value: fmtCompact(m.closed), note: `${fmtCompact(m.canceled)} cancelados` },
    { label: "No SLA de solução", value: fmtPct(m.pct_sla), note: `${fmtCompact(m.on_time)} no prazo`, status: "var(--good)" },
    { label: "Atrasados (SLA)", value: fmtCompact(m.late), note: `${fmtCompact(m.no_sla)} sem SLA`, status: "var(--critical)" },
    { label: "Média de dias de atraso", value: fmtDecimal(m.avg_late_days), note: `máx. ${fmtDecimal(m.max_late_days)} dias` },
    { label: "Estágio vencido (abertos)", value: fmtCompact(m.stage_late), status: "var(--serious)", note: "prazo do estágio" },
    { label: "Tempo médio de resolução", value: fmtDuration(m.avg_resolution_hours), note: `aberto mais antigo: ${fmtDecimal(m.max_open_age_days)} d` },
  ];
}

export function KpiTiles({ metrics }: { metrics: Metrics | undefined }) {
  if (!metrics) return <div className="kpis" aria-busy="true" />;
  return (
    <div className="kpis">
      {buildTiles(metrics).map((tile) => (
        <div key={tile.label} className="kpi">
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
