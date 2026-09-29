import { describe, expect, it } from "vitest";
import { buildHash, parseHash } from "../filters/route";
import { isoDate, matchPreset } from "../filters/dates";
import { fmtPeriod } from "../format";
import { exportUrl } from "./client";
import { EMPTY_FILTERS, filtersToParams, paramsToFilters } from "./query";
import type { Filters } from "./types";

const SAMPLE: Filters = {
  ...EMPTY_FILTERS,
  date_field: "solved",
  date_from: "2026-09-01",
  desk_ids: [1, 2],
  responsible_ids: [0],
  status_names: ["Em Atendimento"],
  situations: ["open"],
  sla: ["late"],
  stage_late: true,
  search: "nf-e",
};

describe("filters <-> query params", () => {
  it("uses repeated keys and omits defaults", () => {
    const params = filtersToParams(SAMPLE);
    expect(params.getAll("desk_ids")).toEqual(["1", "2"]);
    expect(params.get("stage_late")).toBe("true");
    expect(params.has("date_to")).toBe(false);
    expect(filtersToParams(EMPTY_FILTERS).toString()).toBe("");
  });

  it("round-trips through the URL", () => {
    expect(paramsToFilters(filtersToParams(SAMPLE))).toEqual(SAMPLE);
  });

  it("round-trips page and filters through the hash", () => {
    const route = parseHash(buildHash({ page: "late", filters: SAMPLE }));
    expect(route.page).toBe("late");
    expect(route.filters).toEqual(SAMPLE);
    expect(parseHash("#/unknown").page).toBe("overview");
  });
});

describe("exportUrl", () => {
  it("carries filters and sort for ticket exports", () => {
    const url = exportUrl({ kind: "tickets", sort: "late_days", direction: "desc" }, "xlsx", SAMPLE);
    expect(url.startsWith("/api/export/tickets/xlsx?")).toBe(true);
    expect(url).toContain("sort=late_days");
    expect(url).toContain("desk_ids=1&desk_ids=2");
  });

  it("passes granularity for series and kind for buckets", () => {
    expect(exportUrl({ kind: "timeseries", granularity: "week" }, "csv", EMPTY_FILTERS)).toBe("/api/export/timeseries/csv?granularity=week");
    expect(exportUrl({ kind: "buckets", bucket: "aging" }, "xlsx", EMPTY_FILTERS)).toBe("/api/export/buckets/aging/xlsx?");
  });

  it("targets the dimension for breakdowns", () => {
    expect(exportUrl({ kind: "breakdown", dimension: "desk" }, "csv", EMPTY_FILTERS)).toBe("/api/export/breakdown/desk/csv?");
  });
});

describe("date presets", () => {
  const today = new Date(2026, 8, 29);
  it("formats local dates", () => expect(isoDate(today)).toBe("2026-09-29"));
  it("recognises presets and custom ranges", () => {
    expect(matchPreset("", "", today)).toBe("all");
    expect(matchPreset("2026-09-01", "2026-09-29", today)).toBe("mtd");
    expect(matchPreset("2026-01-02", "2026-02-03", today)).toBe("custom");
  });
});

describe("fmtPeriod", () => {
  it("labels months and days without timezone drift", () => {
    expect(fmtPeriod("2026-09-01", "month")).toMatch(/set/);
    expect(fmtPeriod("2026-09-01", "day")).toBe("01/09/26");
  });
});
