import { useState } from "react";
import { api } from "./api/client";
import type { Dimension, Filters } from "./api/types";
import { useFetch } from "./api/useFetch";
import { TicketTable } from "./components/TicketTable";
import { TopBar } from "./components/TopBar";
import { FilterBar } from "./filters/FilterBar";
import { useRoute, type PageId } from "./filters/route";
import { BreakdownPage } from "./pages/BreakdownPage";
import { DIMENSION_LABEL } from "./pages/drill";
import { LatePage } from "./pages/LatePage";
import { OverviewPage } from "./pages/OverviewPage";

const CATEGORY_DIMENSIONS: Dimension[] = ["priority", "stage", "status", "catalog", "channel"];
const PAGE_DIMENSION: Partial<Record<PageId, Dimension>> = { clients: "client", desks: "desk", technicians: "responsible" };

function CategoriesPage({ filters, onFilters }: { filters: Filters; onFilters: (f: Filters) => void }) {
  const [dimension, setDimension] = useState<Dimension>("priority");
  return (
    <>
      <div className="filterbar" role="group" aria-label="Agrupar por">
        <span className="filter-label">Agrupar por</span>
        {CATEGORY_DIMENSIONS.map((d) => (
          <button key={d} type="button" className="btn" aria-pressed={dimension === d} onClick={() => setDimension(d)}>
            {DIMENSION_LABEL[d]}
          </button>
        ))}
      </div>
      <BreakdownPage dimension={dimension} filters={filters} onFilters={onFilters} />
    </>
  );
}

function PageBody({ page, filters, onFilters }: { page: PageId; filters: Filters; onFilters: (f: Filters) => void }) {
  const dimension = PAGE_DIMENSION[page];
  if (dimension) return <BreakdownPage dimension={dimension} filters={filters} onFilters={onFilters} />;
  if (page === "late") return <LatePage filters={filters} onFilters={onFilters} />;
  if (page === "categories") return <CategoriesPage filters={filters} onFilters={onFilters} />;
  if (page === "tickets") return <TicketTable title="Chamados" filters={filters} />;
  return <OverviewPage filters={filters} onFilters={onFilters} />;
}

export function App() {
  const [route, navigate] = useRoute();
  const options = useFetch((s) => api.options(s), "options");
  const setFilters = (filters: Filters) => navigate({ filters });
  return (
    <>
      <TopBar page={route.page} onPage={(page) => navigate({ page })} />
      <main className="content">
        <FilterBar filters={route.filters} options={options.data} onChange={setFilters} />
        <PageBody page={route.page} filters={route.filters} onFilters={setFilters} />
      </main>
    </>
  );
}
