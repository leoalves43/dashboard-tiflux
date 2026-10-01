import type { ReactNode } from "react";
import { api } from "../api/client";
import type { TicketSummary } from "../api/types";
import { useFetch } from "../api/useFetch";
import { fmtDateTime, SITUATION_COLOR, SITUATION_LABEL } from "../format";
import { htmlToText } from "../richText";
import { Pill } from "./Pill";

const dash = (value: string | null) => value || "–";

const FIELDS: { label: string; value: (t: TicketSummary) => string }[] = [
  { label: "Solicitante", value: (t) => dash(t.requestor_name) },
  { label: "Cliente", value: (t) => dash(t.client_name) },
  { label: "Mesa", value: (t) => dash(t.desk_name) },
  { label: "Prioridade", value: (t) => dash(t.priority_name) },
  { label: "Status", value: (t) => dash(t.status_name) },
  { label: "Estágio", value: (t) => dash(t.stage_name) },
  { label: "Técnico responsável", value: (t) => t.responsible_name ?? "(sem responsável)" },
  { label: "Aberto em", value: (t) => fmtDateTime(t.created_at) },
];

interface TicketHeaderProps {
  ticketNumber: number;
  summary: TicketSummary | undefined;
  action?: ReactNode;
}

/**
 * Nº + título + situação; `action` sits at the far right (e.g. the modal's close button).
 * Same element tree while loading, so a focused `action` survives the summary arriving.
 */
export function TicketHeader({ ticketNumber, summary, action }: TicketHeaderProps) {
  return (
    <div className="ticket-head">
      <span className="ticket-number">#{ticketNumber}</span>
      <h2 className="ticket-title">{summary ? summary.title ?? "(sem título)" : "Carregando…"}</h2>
      {summary && <Pill tone={SITUATION_COLOR[summary.situation]}>{SITUATION_LABEL[summary.situation]}</Pill>}
      {action}
    </div>
  );
}

/** The 8 local summary fields of spec 002. Example: <TicketFields summary={s} /> */
export function TicketFields({ summary }: { summary: TicketSummary }) {
  return (
    <dl className="fields">
      {FIELDS.map((field) => (
        <div key={field.label}>
          <dt className="field-label">{field.label}</dt>
          <dd className="field-value" style={{ margin: 0 }}>{field.value(summary)}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Description is read live from Tiflux (list payloads omit it); cached per ticket for the session. */
export function TicketDescription({ ticketNumber }: { ticketNumber: number }) {
  const result = useFetch(() => api.ticketDescription(ticketNumber), String(ticketNumber));
  if (result.error) return <div className="error description">Não foi possível carregar a descrição do Tiflux.</div>;
  if (!result.data) return <div className="muted description">Carregando descrição…</div>;
  return <div className="description">{htmlToText(result.data.description) || "Sem descrição."}</div>;
}
