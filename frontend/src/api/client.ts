import { filtersToParams } from "./query";
import type {
  BreakdownRow, BucketRow, Dimension, ExportFormat, FilterOptions, Filters, Granularity,
  Metrics, SeriesPoint, SyncStatus, TicketActivity, TicketPage, TicketSummary,
} from "./types";

export interface TicketQuery {
  sort: string;
  direction: "asc" | "desc";
  page: number;
  page_size: number;
}

async function getJson<T>(path: string, params?: URLSearchParams, signal?: AbortSignal): Promise<T> {
  const url = params && [...params].length ? `${path}?${params}` : path;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`GET ${url} -> ${response.status}: ${(await response.text()).slice(0, 200)}`);
  }
  return (await response.json()) as T;
}

// Per-ticket results are cached for the session: hovering the same row again costs no request
// (description and activity come live from Tiflux and share its rate limit with the sync).
const ticketCache = new Map<string, Promise<unknown>>();

function cachedTicketJson<T>(path: string): Promise<T> {
  const cached = ticketCache.get(path);
  if (cached) return cached as Promise<T>;
  const request = getJson<T>(path);
  request.catch(() => ticketCache.delete(path)); // failures are retried on the next open
  ticketCache.set(path, request);
  return request;
}

/** Thin typed wrapper over the backend REST API. Example: api.kpis(filters, signal) */
export const api = {
  options: (signal?: AbortSignal) => getJson<FilterOptions>("/api/options", undefined, signal),
  syncStatus: (signal?: AbortSignal) => getJson<SyncStatus>("/api/sync-status", undefined, signal),
  kpis: (f: Filters, signal?: AbortSignal) => getJson<Metrics>("/api/kpis", filtersToParams(f), signal),
  timeseries: (f: Filters, granularity: Granularity, signal?: AbortSignal) =>
    getJson<SeriesPoint[]>("/api/timeseries", filtersToParams(f, { granularity }), signal),
  buckets: (kind: "late" | "aging", f: Filters, signal?: AbortSignal) =>
    getJson<BucketRow[]>(`/api/buckets/${kind}`, filtersToParams(f), signal),
  breakdown: (dimension: Dimension, f: Filters, signal?: AbortSignal) =>
    getJson<BreakdownRow[]>(`/api/breakdown/${dimension}`, filtersToParams(f), signal),
  tickets: (f: Filters, q: TicketQuery, signal?: AbortSignal) =>
    getJson<TicketPage>("/api/tickets", filtersToParams(f, { ...q }), signal),
  ticketSummary: (n: number) => cachedTicketJson<TicketSummary>(`/api/tickets/${n}`),
  ticketDescription: (n: number) => cachedTicketJson<{ description: string | null }>(`/api/tickets/${n}/description`),
  // Not cached: each modal open shows the latest follow-ups (spec 002, criterion 8).
  ticketActivity: (n: number, signal?: AbortSignal) => getJson<TicketActivity>(`/api/tickets/${n}/activity`, undefined, signal),
};

export type ExportTarget =
  | { kind: "tickets"; sort?: string; direction?: "asc" | "desc" }
  | { kind: "breakdown"; dimension: Dimension }
  | { kind: "kpis" }
  | { kind: "timeseries"; granularity: Granularity }
  | { kind: "buckets"; bucket: "late" | "aging" };

/** URL that downloads the full filtered view (never just the visible page). */
export function exportUrl(target: ExportTarget, format: ExportFormat, filters: Filters): string {
  if (target.kind === "breakdown") {
    return `/api/export/breakdown/${target.dimension}/${format}?${filtersToParams(filters)}`;
  }
  if (target.kind === "kpis") return `/api/export/kpis/${format}?${filtersToParams(filters)}`;
  if (target.kind === "timeseries") {
    return `/api/export/timeseries/${format}?${filtersToParams(filters, { granularity: target.granularity })}`;
  }
  if (target.kind === "buckets") return `/api/export/buckets/${target.bucket}/${format}?${filtersToParams(filters)}`;
  const extra = { sort: target.sort ?? "created_at", direction: target.direction ?? "desc" };
  return `/api/export/tickets/${format}?${filtersToParams(filters, extra)}`;
}
