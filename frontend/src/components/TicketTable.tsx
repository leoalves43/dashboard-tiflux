import { useEffect, useState } from "react";
import { api, type TicketQuery } from "../api/client";
import type { Filters, TicketRow } from "../api/types";
import { useFetch } from "../api/useFetch";
import { fmtDateTime, fmtDecimal, fmtDuration, fmtInt, SITUATION_COLOR, SITUATION_LABEL, SLA_COLOR, SLA_LABEL } from "../format";
import { Pill } from "./Pill";
import { TicketHoverCard, useTicketHover } from "./TicketHoverCard";
import { Card, ExportButtons } from "./Card";

interface Column {
  key: keyof TicketRow;
  label: string;
  numeric?: boolean;
  wrap?: boolean;
  render: (row: TicketRow) => React.ReactNode;
}

const text = (value: string | null) => value ?? "–";

const COLUMNS: Column[] = [
  { key: "ticket_number", label: "Nº", numeric: true, render: (r) => r.ticket_number },
  { key: "title", label: "Título", wrap: true, render: (r) => text(r.title) },
  { key: "situation", label: "Situação", render: (r) => <Pill tone={SITUATION_COLOR[r.situation]}>{SITUATION_LABEL[r.situation]}</Pill> },
  { key: "sla_state", label: "SLA", render: (r) => <Pill tone={SLA_COLOR[r.sla_state]}>{SLA_LABEL[r.sla_state]}</Pill> },
  { key: "late_days", label: "Dias atraso", numeric: true, render: (r) => fmtDecimal(r.late_days) },
  { key: "stage_late_days", label: "Dias estágio vencido", numeric: true, render: (r) => fmtDecimal(r.stage_late_days) },
  { key: "client_name", label: "Cliente", render: (r) => text(r.client_name) },
  { key: "desk_name", label: "Mesa", render: (r) => text(r.desk_name) },
  { key: "responsible_name", label: "Técnico", render: (r) => r.responsible_name ?? "(sem responsável)" },
  { key: "stage_name", label: "Estágio", render: (r) => text(r.stage_name) },
  { key: "priority_name", label: "Prioridade", render: (r) => text(r.priority_name) },
  { key: "created_at", label: "Aberto em", render: (r) => fmtDateTime(r.created_at) },
  { key: "solve_expiration", label: "Prazo solução", render: (r) => fmtDateTime(r.solve_expiration) },
  { key: "solved_at", label: "Resolvido em", render: (r) => fmtDateTime(r.solved_at) },
  { key: "open_age_days", label: "Idade (d)", numeric: true, render: (r) => fmtDecimal(r.open_age_days) },
  { key: "resolution_hours", label: "Resolução", numeric: true, render: (r) => fmtDuration(r.resolution_hours) },
  { key: "requestor_name", label: "Solicitante", render: (r) => text(r.requestor_name) },
  { key: "services_catalog", label: "Catálogo", render: (r) => text(r.services_catalog) },
  { key: "created_by_way_of", label: "Canal", render: (r) => text(r.created_by_way_of) },
];
const PAGE_SIZES = [25, 50, 100, 200];

interface Props {
  title: string;
  subtitle?: string;
  filters: Filters;
  defaultSort?: Pick<TicketQuery, "sort" | "direction">;
}

/** Server-paged ticket list; exports use the same filters and sort, without paging. */
export function TicketTable({ title, subtitle, filters, defaultSort = { sort: "created_at", direction: "desc" } }: Props) {
  const [query, setQuery] = useState<TicketQuery>({ ...defaultSort, page: 1, page_size: 50 });
  const filtersKey = JSON.stringify(filters);
  // New filters shrink the result set, so go back to the first page.
  useEffect(() => setQuery((q) => (q.page === 1 ? q : { ...q, page: 1 })), [filtersKey]);
  const result = useFetch((signal) => api.tickets(filters, query, signal), JSON.stringify([filtersKey, query]));
  const data = result.data;
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const sortBy = (key: string) => setQuery((q) => ({
    ...q, page: 1, sort: key, direction: q.sort === key && q.direction === "desc" ? "asc" : "desc",
  }));
  const hover = useTicketHover();
  const arrow = (key: string) => (query.sort === key ? (query.direction === "desc" ? " ↓" : " ↑") : "");

  return (
    <Card title={title} subtitle={subtitle ?? (data ? `${fmtInt(data.total)} chamados` : undefined)}
      loading={result.loading} error={result.error}
      actions={<ExportButtons target={{ kind: "tickets", sort: query.sort, direction: query.direction }} filters={filters} />}>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>{COLUMNS.map((c) => (
              <th key={c.key} className={c.numeric ? "num" : undefined} onClick={() => sortBy(c.key)}>{c.label}{arrow(c.key)}</th>
            ))}</tr>
          </thead>
          <tbody>
            {data?.rows.map((row) => (
              <tr key={row.ticket_number} className="ticket-row" {...hover.rowProps(row.ticket_number)}>
                {COLUMNS.map((c) => (
                  <td key={c.key} className={c.numeric ? "num" : c.wrap ? "wrap" : undefined}>{c.render(row)}</td>
                ))}
              </tr>
            ))}
            {data && data.rows.length === 0 && <tr><td colSpan={COLUMNS.length} className="muted">Nenhum chamado</td></tr>}
          </tbody>
        </table>
      </div>
      {hover.target && <TicketHoverCard {...hover.target} />}
      <div className="pager">
        <button type="button" className="btn" disabled={query.page <= 1} onClick={() => setQuery((q) => ({ ...q, page: q.page - 1 }))}>Anterior</button>
        <span className="muted">Página {query.page} de {fmtInt(pages)}</span>
        <button type="button" className="btn" disabled={query.page >= pages} onClick={() => setQuery((q) => ({ ...q, page: q.page + 1 }))}>Próxima</button>
        <select className="input" aria-label="Itens por página" value={query.page_size}
          onChange={(e) => setQuery((q) => ({ ...q, page: 1, page_size: Number(e.target.value) }))}>
          {PAGE_SIZES.map((size) => <option key={size} value={size}>{size} por página</option>)}
        </select>
      </div>
    </Card>
  );
}
