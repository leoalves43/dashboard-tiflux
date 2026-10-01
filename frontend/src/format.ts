import type { SlaState, Situation } from "./api/types";

const intFormat = new Intl.NumberFormat("pt-BR");
const compactFormat = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const decimalFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1, minimumFractionDigits: 1 });
const dateTimeFormat = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

export const SITUATION_LABEL: Record<Situation, string> = {
  open: "Aberto", closed: "Fechado", canceled: "Cancelado",
};
export const SLA_LABEL: Record<SlaState, string> = {
  late: "Atrasado", on_time: "No prazo", no_sla: "Sem SLA",
};
/** CSS token per situation, following the series roles in DESIGN.md. */
export const SITUATION_COLOR: Record<Situation, string> = {
  open: "var(--series-1)", closed: "var(--series-3)", canceled: "var(--series-2)",
};
/** CSS token per SLA state (status colors are reserved for status — see DESIGN.md). */
export const SLA_COLOR: Record<SlaState, string> = {
  late: "var(--critical)", on_time: "var(--good)", no_sla: "var(--neutral)",
};

export const fmtInt = (value: number | null | undefined): string =>
  value === null || value === undefined ? "–" : intFormat.format(value);

export const fmtCompact = (value: number | null | undefined): string =>
  value === null || value === undefined ? "–" : value < 10000 ? intFormat.format(value) : compactFormat.format(value);

export const fmtDecimal = (value: number | null | undefined): string =>
  value === null || value === undefined ? "–" : decimalFormat.format(value);

export const fmtPct = (value: number | null | undefined): string =>
  value === null || value === undefined ? "–" : `${decimalFormat.format(value)}%`;

export const fmtDateTime = (iso: string | null | undefined): string =>
  iso ? dateTimeFormat.format(new Date(iso)) : "–";

/** Hours -> "3,5 d" beyond two days so long resolution times stay readable. */
export function fmtDuration(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return "–";
  return hours >= 48 ? `${decimalFormat.format(hours / 24)} d` : `${decimalFormat.format(hours)} h`;
}

const BYTE_UNITS = ["B", "KB", "MB", "GB"];

/** Attachment sizes: fmtBytes(101411) === "99,0 KB". */
export function fmtBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return "–";
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < BYTE_UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return unit === 0 ? `${value} B` : `${decimalFormat.format(value)} ${BYTE_UNITS[unit]}`;
}

const monthFormat =new Intl.DateTimeFormat("pt-BR", { month: "short", year: "numeric", timeZone: "UTC" });
const dayFormat = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit", timeZone: "UTC" });

/** Axis label for a YYYY-MM-DD period start: "set. de 2026" for months, "29/09/26" otherwise. */
export function fmtPeriod(period: string, granularity: "day" | "week" | "month"): string {
  const date = new Date(`${period}T00:00:00Z`);
  return granularity === "month" ? monthFormat.format(date) : dayFormat.format(date);
}
