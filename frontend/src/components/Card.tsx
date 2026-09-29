import type { ReactNode } from "react";
import { exportUrl, type ExportTarget } from "../api/client";
import type { Filters } from "../api/types";

interface CardProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  loading?: boolean;
  error?: string;
  children: ReactNode;
}

export function Card({ title, subtitle, actions, loading, error, children }: CardProps) {
  return (
    <section className={`card${loading ? " loading" : ""}`} aria-busy={loading}>
      <header className="card-head">
        <div>
          <h2 className="card-title">{title}</h2>
          {subtitle && <div className="card-sub">{subtitle}</div>}
        </div>
        {actions && <div className="card-actions">{actions}</div>}
      </header>
      {error && <div className="error" role="alert">Erro ao carregar: {error}</div>}
      {children}
    </section>
  );
}

/** CSV/XLSX links for the full filtered view. Example: <ExportButtons target={{kind:"kpis"}} filters={f} /> */
export function ExportButtons({ target, filters }: { target: ExportTarget; filters: Filters }) {
  return (
    <>
      <a className="btn" href={exportUrl(target, "xlsx", filters)} download>XLSX</a>
      <a className="btn" href={exportUrl(target, "csv", filters)} download>CSV</a>
    </>
  );
}
