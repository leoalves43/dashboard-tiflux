import type { Filters } from "./types";

export const EMPTY_FILTERS: Filters = {
  date_field: "created",
  date_from: "",
  date_to: "",
  desk_ids: [],
  client_ids: [],
  responsible_ids: [],
  priority_names: [],
  stage_names: [],
  situations: [],
  sla: [],
  stage_late: false,
  search: "",
};

type FilterKey = keyof Filters;
const NUMBER_LISTS: FilterKey[] = ["desk_ids", "client_ids", "responsible_ids"];
const TEXT_LISTS: FilterKey[] = ["priority_names", "stage_names", "situations", "sla"];

/** Filters -> URLSearchParams in the repeated-key form FastAPI expects (desk_ids=1&desk_ids=2). */
export function filtersToParams(filters: Filters, extra: Record<string, string | number> = {}): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (Array.isArray(value)) value.forEach((item) => params.append(key, String(item)));
    else if (typeof value === "boolean") { if (value) params.set(key, "true"); }
    else if (value !== "" && value !== EMPTY_FILTERS[key as FilterKey]) params.set(key, String(value));
  }
  for (const [key, value] of Object.entries(extra)) params.set(key, String(value));
  return params;
}

/** Inverse of filtersToParams; unknown keys are ignored so old links keep working. */
export function paramsToFilters(params: URLSearchParams): Filters {
  const filters: Filters = { ...EMPTY_FILTERS };
  const record = filters as unknown as Record<string, unknown>;
  for (const key of NUMBER_LISTS) {
    record[key] = params.getAll(key).map(Number).filter((n) => Number.isFinite(n));
  }
  for (const key of TEXT_LISTS) record[key] = params.getAll(key);
  filters.date_field = params.get("date_field") === "solved" ? "solved" : "created";
  filters.date_from = params.get("date_from") ?? "";
  filters.date_to = params.get("date_to") ?? "";
  filters.stage_late = params.get("stage_late") === "true";
  filters.search = params.get("search") ?? "";
  return filters;
}
