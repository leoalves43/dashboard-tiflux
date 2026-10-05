import type { ReactNode } from "react";
import type { TicketRow } from "../api/types";
import type { ColumnLayout } from "../columns/columnLayout";
import { fmtDateTime, fmtDecimal, fmtDuration, fmtInt, SITUATION_COLOR, SITUATION_LABEL, SLA_COLOR, SLA_LABEL } from "../format";
import { Pill } from "./Pill";

export interface TicketColumn {
  key: keyof TicketRow;
  label: string;
  numeric?: boolean;
  wrap?: boolean;
  // Status, Prazo estágio and Reaberturas used to exist only in exports; they start hidden (spec 004).
  hiddenByDefault?: boolean;
  render: (row: TicketRow) => ReactNode;
}

const text = (value: string | null) => value ?? "–";

/** Every column the ticket table can show, in default order. Keys match the backend LIST_COLUMNS. */
export const TICKET_COLUMNS: TicketColumn[] = [
  { key: "ticket_number", label: "Nº", numeric: true, render: (r) => r.ticket_number },
  { key: "title", label: "Título", wrap: true, render: (r) => text(r.title) },
  { key: "situation", label: "Situação", render: (r) => <Pill tone={SITUATION_COLOR[r.situation]}>{SITUATION_LABEL[r.situation]}</Pill> },
  { key: "status_name", label: "Status", hiddenByDefault: true, render: (r) => text(r.status_name) },
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
  { key: "stage_expiration", label: "Prazo estágio", hiddenByDefault: true, render: (r) => fmtDateTime(r.stage_expiration) },
  { key: "solved_at", label: "Resolvido em", render: (r) => fmtDateTime(r.solved_at) },
  { key: "open_age_days", label: "Idade (d)", numeric: true, render: (r) => fmtDecimal(r.open_age_days) },
  { key: "resolution_hours", label: "Resolução", numeric: true, render: (r) => fmtDuration(r.resolution_hours) },
  { key: "requestor_name", label: "Solicitante", render: (r) => text(r.requestor_name) },
  { key: "services_catalog", label: "Catálogo", render: (r) => text(r.services_catalog) },
  { key: "created_by_way_of", label: "Canal", render: (r) => text(r.created_by_way_of) },
  { key: "reopen_count", label: "Reaberturas", numeric: true, hiddenByDefault: true,
    render: (r) => (r.reopen_count === null ? "–" : fmtInt(r.reopen_count)) },
];

export const DEFAULT_TICKET_LAYOUT: ColumnLayout = TICKET_COLUMNS.map((c) => ({ key: c.key, visible: !c.hiddenByDefault }));

const COLUMN_BY_KEY = new Map<string, TicketColumn>(TICKET_COLUMNS.map((c) => [c.key, c]));

/** Column definitions for the visible keys, in layout order. Example: columnsFor(["title"]) */
export function columnsFor(keys: string[]): TicketColumn[] {
  return keys.flatMap((key) => COLUMN_BY_KEY.get(key) ?? []);
}

export function columnLabel(key: string): string {
  return COLUMN_BY_KEY.get(key)?.label ?? key;
}
