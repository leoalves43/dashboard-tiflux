import { useMemo, useState } from "react";
import { api } from "../api/client";
import type { Filters } from "../api/types";
import { useFetch } from "../api/useFetch";
import { EChart } from "../charts/EChart";
import { columns } from "../charts/options";
import { useChartTheme } from "../charts/theme";
import { Card } from "../components/Card";
import { TicketTable } from "../components/TicketTable";
import { BreakdownPage } from "./BreakdownPage";

type LateMode = "open_late" | "all_late" | "stage_late";

const MODES: Record<LateMode, { label: string; apply: (f: Filters) => Filters; sort: string }> = {
  open_late: { label: "Abertos em atraso (SLA)", sort: "late_days", apply: (f) => ({ ...f, situations: ["open"], sla: ["late"] }) },
  all_late: { label: "Todos atrasados (inclui fechados)", sort: "late_days", apply: (f) => ({ ...f, sla: ["late"] }) },
  stage_late: { label: "Estágio vencido", sort: "stage_late_days", apply: (f) => ({ ...f, situations: ["open"], stage_late: true }) },
};

/** Late tickets: day-range chart, who/where is late, and the full list sorted by days late. */
export function LatePage({ filters, onFilters }: { filters: Filters; onFilters: (next: Filters) => void }) {
  const theme = useChartTheme();
  const [mode, setMode] = useState<LateMode>("open_late");
  const scoped = MODES[mode].apply(filters);
  const buckets = useFetch((s) => api.buckets("late", filters, s), JSON.stringify(filters));
  const option = useMemo(() => {
    const rows = buckets.data ?? [];
    return columns(theme, rows.map((r) => r.bucket), rows.map((r) => r.count), theme.ordinal, "Chamados");
  }, [theme, buckets.data]);

  return (
    <>
      <Card title="Abertos em atraso por dias de atraso" subtitle="Dias corridos além do prazo de solução (SLA)"
        loading={buckets.loading} error={buckets.error}>
        <EChart option={option} ariaLabel="Chamados em atraso por faixa de dias" />
      </Card>
      <div className="filterbar" role="group" aria-label="Tipo de atraso">
        {(Object.keys(MODES) as LateMode[]).map((m) => (
          <button key={m} type="button" className="btn" aria-pressed={mode === m} onClick={() => setMode(m)}>{MODES[m].label}</button>
        ))}
      </div>
      <TicketTable key={mode} title={`Chamados — ${MODES[mode].label.toLowerCase()}`} filters={scoped}
        defaultSort={{ sort: MODES[mode].sort, direction: "desc" }} />
      {/* Drilling keeps only the chosen technician; the mode's own scope must not leak into global filters. */}
      <BreakdownPage dimension="responsible" filters={scoped}
        onFilters={(next) => onFilters({ ...filters, responsible_ids: next.responsible_ids })} />
    </>
  );
}
