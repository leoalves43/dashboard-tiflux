import { useMemo, useState } from "react";
import type { BreakdownRow, Metrics } from "../api/types";
import { fmtDecimal, fmtDuration, fmtInt, fmtPct } from "../format";

type SortKey = keyof Metrics | "name";

interface Column {
  key: SortKey;
  label: string;
  render: (row: BreakdownRow) => string;
}

const COLUMNS: Column[] = [
  { key: "total", label: "Total", render: (r) => fmtInt(r.total) },
  { key: "open", label: "Abertos", render: (r) => fmtInt(r.open) },
  { key: "closed", label: "Fechados", render: (r) => fmtInt(r.closed) },
  { key: "canceled", label: "Cancelados", render: (r) => fmtInt(r.canceled) },
  { key: "late", label: "Atrasados", render: (r) => fmtInt(r.late) },
  { key: "open_late", label: "Abertos em atraso", render: (r) => fmtInt(r.open_late) },
  { key: "pct_sla", label: "% no SLA", render: (r) => fmtPct(r.pct_sla) },
  { key: "avg_late_days", label: "Média dias atraso", render: (r) => fmtDecimal(r.avg_late_days) },
  { key: "max_late_days", label: "Máx. dias atraso", render: (r) => fmtDecimal(r.max_late_days) },
  { key: "stage_late", label: "Estágio vencido", render: (r) => fmtInt(r.stage_late) },
  { key: "avg_resolution_hours", label: "Tempo médio resolução", render: (r) => fmtDuration(r.avg_resolution_hours) },
  { key: "max_open_age_days", label: "Aberto + antigo (d)", render: (r) => fmtDecimal(r.max_open_age_days) },
];

function compare(a: BreakdownRow, b: BreakdownRow, key: SortKey): number {
  const left = a[key];
  const right = b[key];
  if (typeof left === "string" || typeof right === "string") return String(left ?? "").localeCompare(String(right ?? ""));
  return (left ?? -Infinity) - (right ?? -Infinity);
}

interface Props {
  rows: BreakdownRow[];
  nameLabel: string;
  onSelect?: (row: BreakdownRow) => void;
}

/** Client-side sortable table (breakdowns are small: one row per client/desk/technician). */
export function BreakdownTable({ rows, nameLabel, onSelect }: Props) {
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: "total", desc: true });
  const sorted = useMemo(() => {
    const copy = [...rows].sort((a, b) => compare(a, b, sort.key));
    return sort.desc ? copy.reverse() : copy;
  }, [rows, sort]);
  const toggle = (key: SortKey) => setSort((prev) => ({ key, desc: prev.key === key ? !prev.desc : key !== "name" }));
  const arrow = (key: SortKey) => (sort.key === key ? (sort.desc ? " ↓" : " ↑") : "");

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th onClick={() => toggle("name")}>{nameLabel}{arrow("name")}</th>
            {COLUMNS.map((c) => <th key={c.key} className="num" onClick={() => toggle(c.key)}>{c.label}{arrow(c.key)}</th>)}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.key} className={onSelect ? "clickable" : undefined} onClick={() => onSelect?.(row)}
              title={onSelect ? "Clique para filtrar o painel por este item" : undefined}>
              <td>{row.name}</td>
              {COLUMNS.map((c) => <td key={c.key} className="num">{c.render(row)}</td>)}
            </tr>
          ))}
          {sorted.length === 0 && <tr><td colSpan={COLUMNS.length + 1} className="muted">Sem dados para os filtros atuais</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
