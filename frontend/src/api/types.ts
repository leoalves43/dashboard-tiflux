export type Situation = "open" | "closed" | "canceled";
export type SlaState = "late" | "on_time" | "no_sla";
export type Dimension =
  | "client" | "desk" | "responsible" | "priority" | "stage" | "status" | "catalog" | "channel";
export type Granularity = "day" | "week" | "month";
export type ExportFormat = "csv" | "xlsx";

/** Mirrors backend app/filters.py TicketFilters. Empty arrays mean "no filter". */
export interface Filters {
  date_field: "created" | "solved";
  date_from: string;
  date_to: string;
  desk_ids: number[];
  client_ids: number[];
  responsible_ids: number[];
  priority_names: string[];
  stage_names: string[];
  status_names: string[];
  situations: Situation[];
  sla: SlaState[];
  stage_late: boolean;
  search: string;
}

export interface Metrics {
  total: number;
  open: number;
  closed: number;
  canceled: number;
  late: number;
  on_time: number;
  no_sla: number;
  pct_sla: number | null;
  open_late: number;
  stage_late: number;
  avg_late_days: number | null;
  max_late_days: number | null;
  avg_resolution_hours: number | null;
  max_open_age_days: number | null;
}

export interface BreakdownRow extends Metrics {
  key: string;
  name: string;
}

export interface SeriesPoint {
  period: string;
  created: number;
  solved: number;
}

export interface BucketRow {
  bucket: string;
  count: number;
}

export interface TicketRow {
  ticket_number: number;
  title: string | null;
  situation: Situation;
  status_name: string | null;
  stage_name: string | null;
  priority_name: string | null;
  desk_name: string | null;
  client_name: string | null;
  responsible_name: string | null;
  requestor_name: string | null;
  services_catalog: string | null;
  created_by_way_of: string | null;
  created_at: string | null;
  solved_at: string | null;
  solve_expiration: string | null;
  stage_expiration: string | null;
  sla_state: SlaState;
  late_days: number | null;
  stage_late_days: number | null;
  open_age_days: number | null;
  resolution_hours: number | null;
  reopen_count: number | null;
}

export interface TicketPage {
  total: number;
  page: number;
  page_size: number;
  rows: TicketRow[];
}

export interface Option {
  id: number;
  name: string | null;
}

export interface FilterOptions {
  desks: Option[];
  clients: Option[];
  technicians: Option[];
  priorities: string[];
  stages: string[];
  statuses: string[];
}

export interface SyncStatus {
  backfill_done: boolean;
  last_incremental: string | null;
  tickets: number;
  last_write: string | null;
}

/** Local fields shown in the hover card and the modal header (GET /api/tickets/{n}). */
export interface TicketSummary {
  ticket_number: number;
  title: string | null;
  situation: Situation;
  requestor_name: string | null;
  requestor_email: string | null;
  client_name: string | null;
  desk_name: string | null;
  priority_name: string | null;
  status_name: string | null;
  stage_name: string | null;
  responsible_name: string | null;
  created_at: string | null;
}

export interface TicketFile {
  id: number;
  file_name: string | null;
  content_type: string | null;
  size: number | null;
  url: string | null;
}

export interface TicketFollowup {
  kind: "answer" | "internal";
  id: number;
  author: string | null;
  created_at: string | null;
  text: string | null;
  files: TicketFile[];
}

/** Live from Tiflux (GET /api/tickets/{n}/activity), not stored locally. */
export interface TicketActivity {
  files: TicketFile[];
  followups: TicketFollowup[];
}
