import { useEffect, useState } from "react";
import { api, type TicketQuery } from "../api/client";
import type { Filters } from "../api/types";
import { useFetch } from "../api/useFetch";
import { visibleKeys } from "../columns/columnLayout";
import { browserStorage, useColumnLayout } from "../columns/useColumnLayout";
import { fmtInt } from "../format";
import { ColumnEditor } from "./ColumnEditor";
import { columnLabel, columnsFor, DEFAULT_TICKET_LAYOUT } from "./ticketColumns";
import { TicketHoverCard, useTicketHover } from "./TicketHoverCard";
import { TicketModal } from "./TicketModal";
import { Card, ExportButtons } from "./Card";

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
  const [openTicket, setOpenTicket] = useState<number | null>(null);
  const open = (ticketNumber: number) => {
    hover.cancel();
    setOpenTicket(ticketNumber);
  };
  const { layout, setLayout, reset } = useColumnLayout(DEFAULT_TICKET_LAYOUT, browserStorage());
  const shownKeys = visibleKeys(layout);
  const columns = columnsFor(shownKeys);
  const arrow = (key: string) => (query.sort === key ? (query.direction === "desc" ? " ↓" : " ↑") : "");

  return (
    <Card title={title} subtitle={subtitle ?? (data ? `${fmtInt(data.total)} chamados` : undefined)}
      loading={result.loading} error={result.error}
      actions={<>
        <ColumnEditor layout={layout} labelOf={columnLabel} onChange={setLayout} onReset={reset} />
        <ExportButtons target={{ kind: "tickets", sort: query.sort, direction: query.direction, columns: shownKeys }} filters={filters} />
      </>}>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>{columns.map((c) => (
              <th key={c.key} className={c.numeric ? "num" : undefined} onClick={() => sortBy(c.key)}>{c.label}{arrow(c.key)}</th>
            ))}</tr>
          </thead>
          <tbody>
            {data?.rows.map((row) => (
              <tr key={row.ticket_number} className="ticket-row" tabIndex={0} {...hover.rowProps(row.ticket_number)}
                onClick={() => open(row.ticket_number)} onKeyDown={(e) => e.key === "Enter" && open(row.ticket_number)}>
                {columns.map((c) => (
                  <td key={c.key} className={c.numeric ? "num" : c.wrap ? "wrap" : undefined}>{c.render(row)}</td>
                ))}
              </tr>
            ))}
            {data && data.rows.length === 0 && <tr><td colSpan={columns.length} className="muted">Nenhum chamado</td></tr>}
          </tbody>
        </table>
      </div>
      {hover.target && <TicketHoverCard {...hover.target} />}
      {openTicket !== null && <TicketModal ticketNumber={openTicket} onClose={() => setOpenTicket(null)} />}
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
