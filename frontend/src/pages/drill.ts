import type { BreakdownRow, Dimension, Filters } from "../api/types";

type Drill = (filters: Filters, row: BreakdownRow) => Filters;

const addNumber = (list: number[], key: string) => {
  const id = Number(key);
  return list.includes(id) ? list : [...list, id];
};
const addText = (list: string[], key: string) => (list.includes(key) ? list : [...list, key]);

/** How clicking a breakdown row narrows the global filters; dimensions without a filter are absent. */
export const DRILLS: Partial<Record<Dimension, Drill>> = {
  client: (f, row) => ({ ...f, client_ids: addNumber(f.client_ids, row.key) }),
  desk: (f, row) => ({ ...f, desk_ids: addNumber(f.desk_ids, row.key) }),
  responsible: (f, row) => ({ ...f, responsible_ids: addNumber(f.responsible_ids, row.key) }),
  priority: (f, row) => ({ ...f, priority_names: addText(f.priority_names, row.key) }),
  stage: (f, row) => ({ ...f, stage_names: addText(f.stage_names, row.key) }),
};

export const DIMENSION_LABEL: Record<Dimension, string> = {
  client: "Cliente",
  desk: "Mesa",
  responsible: "Técnico",
  priority: "Prioridade",
  stage: "Estágio",
  status: "Status",
  catalog: "Catálogo de serviço",
  channel: "Canal de abertura",
};
