import { useMemo, useState } from "react";
import { api } from "../api/client";
import type { BucketRow, Filters, Granularity } from "../api/types";
import { useFetch } from "../api/useFetch";
import { EChart } from "../charts/EChart";
import { columns, timeLines } from "../charts/options";
import { useChartTheme } from "../charts/theme";
import { Card, ExportButtons } from "../components/Card";
import { KpiTiles } from "../components/KpiTiles";
import { fmtPeriod } from "../format";
import { BreakdownPage } from "./BreakdownPage";

const GRANULARITY_LABEL: Record<Granularity, string> = { day: "Dia", week: "Semana", month: "Mês" };

function BucketChart({ title, subtitle, rows, name }: { title: string; subtitle: string; rows: BucketRow[]; name: string }) {
  const theme = useChartTheme();
  const option = useMemo(
    () => columns(theme, rows.map((r) => r.bucket), rows.map((r) => r.count), theme.ordinal, name),
    [theme, rows, name],
  );
  return (
    <Card title={title} subtitle={subtitle}>
      <EChart option={option} ariaLabel={title} />
    </Card>
  );
}

function TrendCard({ filters }: { filters: Filters }) {
  const theme = useChartTheme();
  const [granularity, setGranularity] = useState<Granularity>("month");
  const result = useFetch((s) => api.timeseries(filters, granularity, s), JSON.stringify([filters, granularity]));
  const option = useMemo(() => {
    const points = result.data ?? [];
    return timeLines(theme, points.map((p) => fmtPeriod(p.period, granularity)), [
      { name: "Abertos", color: theme.series[0], values: points.map((p) => p.created) },
      { name: "Resolvidos", color: theme.series[2], values: points.map((p) => p.solved) },
    ]);
  }, [theme, result.data, granularity]);
  return (
    <Card title="Chamados abertos x resolvidos" subtitle="Por data de abertura e de resolução" loading={result.loading} error={result.error}
      actions={(Object.keys(GRANULARITY_LABEL) as Granularity[]).map((g) => (
        <button key={g} type="button" className="btn" aria-pressed={granularity === g} onClick={() => setGranularity(g)}>
          {GRANULARITY_LABEL[g]}
        </button>
      ))}>
      <EChart option={option} ariaLabel="Série temporal de chamados abertos e resolvidos" />
    </Card>
  );
}

export function OverviewPage({ filters, onFilters }: { filters: Filters; onFilters: (next: Filters) => void }) {
  const key = JSON.stringify(filters);
  const kpis = useFetch((s) => api.kpis(filters, s), key);
  const late = useFetch((s) => api.buckets("late", filters, s), key);
  const aging = useFetch((s) => api.buckets("aging", filters, s), key);
  return (
    <>
      <Card title="Indicadores" subtitle="SLA de solução; chamados sem prazo contam como 'sem SLA'"
        loading={kpis.loading} error={kpis.error} actions={<ExportButtons target={{ kind: "kpis" }} filters={filters} />}>
        <KpiTiles metrics={kpis.data} />
      </Card>
      <TrendCard filters={filters} />
      <div className="grid-2">
        <BucketChart title="Abertos em atraso por dias de atraso" subtitle="Dias corridos além do prazo de solução" rows={late.data ?? []} name="Chamados" />
        <BucketChart title="Backlog aberto por idade" subtitle="Dias desde a abertura" rows={aging.data ?? []} name="Chamados" />
      </div>
      <BreakdownPage dimension="desk" filters={filters} onFilters={onFilters} />
    </>
  );
}
