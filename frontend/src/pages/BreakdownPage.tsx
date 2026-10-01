import { useCallback, useMemo, useState } from "react";
import { api } from "../api/client";
import type { BreakdownRow, Dimension, Filters } from "../api/types";
import { useFetch } from "../api/useFetch";
import { EChart } from "../charts/EChart";
import { horizontalBars, type BarSeries } from "../charts/options";
import { useChartTheme, type ChartTheme } from "../charts/theme";
import { BreakdownTable } from "../components/BreakdownTable";
import { Card, ExportButtons } from "../components/Card";
import { TicketTable } from "../components/TicketTable";
import { DIMENSION_LABEL, DRILLS } from "./drill";

type ChartView = "volume" | "late";
const TOP_N = 15;

function chartSeries(view: ChartView, rows: BreakdownRow[], theme: ChartTheme): BarSeries[] {
  if (view === "late") {
    return [
      { name: "Abertos em atraso (SLA)", color: theme.critical, values: rows.map((r) => r.open_late) },
      { name: "Estágio vencido", color: theme.serious, values: rows.map((r) => r.stage_late) },
    ];
  }
  return [
    { name: "Abertos", color: theme.series[0], values: rows.map((r) => r.open) },
    { name: "Fechados", color: theme.series[2], values: rows.map((r) => r.closed) },
  ];
}

function topRows(view: ChartView, rows: BreakdownRow[]): BreakdownRow[] {
  const score = (r: BreakdownRow) => (view === "late" ? r.open_late + r.stage_late : r.total);
  return [...rows].sort((a, b) => score(b) - score(a)).filter((r) => score(r) > 0).slice(0, TOP_N);
}

interface Props {
  dimension: Dimension;
  filters: Filters;
  onFilters: (next: Filters) => void;
}

/** Ranking chart + full table for one dimension (clients, desks, technicians, categories). */
export function BreakdownPage({ dimension, filters, onFilters }: Props) {
  const theme = useChartTheme();
  const [view, setView] = useState<ChartView>("volume");
  const result = useFetch((signal) => api.breakdown(dimension, filters, signal), JSON.stringify([dimension, filters]));
  const rows = useMemo(() => result.data ?? [], [result.data]);
  const top = useMemo(() => topRows(view, rows), [view, rows]);
  const option = useMemo(() => horizontalBars(theme, top.map((r) => r.name), chartSeries(view, top, theme)), [theme, top, view]);
  const drill = DRILLS[dimension];
  const select = useCallback((row: BreakdownRow) => drill && onFilters(drill(filters, row)), [drill, filters, onFilters]);
  const label = DIMENSION_LABEL[dimension];

  return (
    <>
      <Card title={`Top ${TOP_N} por ${label.toLowerCase()}`} loading={result.loading} error={result.error}
        subtitle={drill ? "Clique numa barra para filtrar o painel" : undefined}
        actions={
          <>
            <button type="button" className="btn" aria-pressed={view === "volume"} onClick={() => setView("volume")}>Volume</button>
            <button type="button" className="btn" aria-pressed={view === "late"} onClick={() => setView("late")}>Atrasos</button>
          </>
        }>
        <EChart option={option} className="chart chart-tall" ariaLabel={`Ranking por ${label}`}
          onItemClick={drill ? (i) => top[i] && select(top[i]) : undefined} />
      </Card>
      <Card title={`Detalhamento por ${label.toLowerCase()}`} subtitle={`${rows.length} itens`} loading={result.loading}
        actions={<ExportButtons target={{ kind: "breakdown", dimension }} filters={filters} />}>
        <BreakdownTable rows={rows} nameLabel={label} onSelect={drill ? select : undefined} />
      </Card>
      <TicketTable title="Chamados" filters={filters} />
    </>
  );
}
