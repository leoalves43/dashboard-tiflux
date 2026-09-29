import { useCallback, useEffect, useState } from "react";
import { filtersToParams, paramsToFilters } from "../api/query";
import type { Filters } from "../api/types";

export const PAGES = [
  { id: "overview", label: "Visão geral" },
  { id: "clients", label: "Clientes" },
  { id: "desks", label: "Mesas" },
  { id: "technicians", label: "Técnicos" },
  { id: "late", label: "Atrasos (SLA)" },
  { id: "categories", label: "Categorias" },
  { id: "tickets", label: "Chamados" },
] as const;
export type PageId = (typeof PAGES)[number]["id"];

interface Route {
  page: PageId;
  filters: Filters;
}

/** Hash format: #/<page>?<filters>. Keeping filters in the URL makes every view shareable. */
export function parseHash(hash: string): Route {
  const [path, query = ""] = hash.replace(/^#\/?/, "").split("?");
  const known = PAGES.find((page) => page.id === path);
  return { page: known ? known.id : "overview", filters: paramsToFilters(new URLSearchParams(query)) };
}

export function buildHash(route: Route): string {
  const query = filtersToParams(route.filters).toString();
  return `#/${route.page}${query ? `?${query}` : ""}`;
}

export function useRoute(): [Route, (next: Partial<Route>) => void] {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));

  useEffect(() => {
    const onChange = () => setRoute(parseHash(window.location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const navigate = useCallback((next: Partial<Route>) => {
    const current = parseHash(window.location.hash);
    window.location.hash = buildHash({ ...current, ...next });
    if (next.page && next.page !== current.page) window.scrollTo({ top: 0 });
  }, []);

  return [route, navigate];
}
