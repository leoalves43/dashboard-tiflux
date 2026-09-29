import { useEffect, useState } from "react";
import { EMPTY_FILTERS } from "../api/query";
import type { FilterOptions, Filters, Option, SlaState, Situation } from "../api/types";
import { SITUATION_LABEL, SLA_LABEL } from "../format";
import { DATE_PRESETS, matchPreset } from "./dates";
import { MultiSelect, type SelectOption } from "./MultiSelect";

interface Props {
  filters: Filters;
  options: FilterOptions | undefined;
  onChange: (next: Filters) => void;
}

const UNASSIGNED: SelectOption<number> = { value: 0, label: "(Sem responsável)" };

const idOptions = (items: Option[] | undefined): SelectOption<number>[] =>
  (items ?? []).map((item) => ({ value: item.id, label: item.name ?? `#${item.id}` }));
const textOptions = (items: string[] | undefined): SelectOption<string>[] =>
  (items ?? []).map((item) => ({ value: item, label: item }));
const labelOptions = <K extends string>(labels: Record<K, string>): SelectOption<K>[] =>
  (Object.keys(labels) as K[]).map((key) => ({ value: key, label: labels[key] }));

function DateControls({ filters, onChange }: Omit<Props, "options">) {
  const preset = matchPreset(filters.date_from, filters.date_to);
  const applyPreset = (id: string) => {
    const found = DATE_PRESETS.find((p) => p.id === id);
    if (!found) return;
    const [date_from, date_to] = found.range(new Date());
    onChange({ ...filters, date_from, date_to });
  };
  return (
    <>
      <select className="input" aria-label="Campo de data" value={filters.date_field}
        onChange={(e) => onChange({ ...filters, date_field: e.target.value as Filters["date_field"] })}>
        <option value="created">Abertura</option>
        <option value="solved">Resolução</option>
      </select>
      <select className="input" aria-label="Período" value={preset} onChange={(e) => applyPreset(e.target.value)}>
        {DATE_PRESETS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
        {preset === "custom" && <option value="custom">Personalizado</option>}
      </select>
      <input className="input" type="date" aria-label="De" value={filters.date_from}
        onChange={(e) => onChange({ ...filters, date_from: e.target.value })} />
      <input className="input" type="date" aria-label="Até" value={filters.date_to}
        onChange={(e) => onChange({ ...filters, date_to: e.target.value })} />
    </>
  );
}

/** Debounced so typing does not fire one request per keystroke. */
function SearchBox({ value, onCommit }: { value: string; onCommit: (text: string) => void }) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  useEffect(() => {
    if (draft === value) return;
    const timer = window.setTimeout(() => onCommit(draft), 400);
    return () => window.clearTimeout(timer);
  }, [draft, value, onCommit]);
  return (
    <input className="input" type="search" placeholder="Buscar nº, título, cliente…" aria-label="Busca"
      value={draft} onChange={(e) => setDraft(e.target.value)} />
  );
}

export function FilterBar({ filters, options, onChange }: Props) {
  const set = <K extends keyof Filters>(key: K) => (value: Filters[K]) => onChange({ ...filters, [key]: value });
  const hasFilters = JSON.stringify(filters) !== JSON.stringify(EMPTY_FILTERS);
  return (
    <section className="filterbar" aria-label="Filtros">
      <DateControls filters={filters} onChange={onChange} />
      <MultiSelect label="Mesa" options={idOptions(options?.desks)} selected={filters.desk_ids} onChange={set("desk_ids")} />
      <MultiSelect label="Cliente" options={idOptions(options?.clients)} selected={filters.client_ids} onChange={set("client_ids")} />
      <MultiSelect label="Técnico" options={[UNASSIGNED, ...idOptions(options?.technicians)]}
        selected={filters.responsible_ids} onChange={set("responsible_ids")} />
      <MultiSelect label="Prioridade" options={textOptions(options?.priorities)} selected={filters.priority_names} onChange={set("priority_names")} />
      <MultiSelect label="Estágio" options={textOptions(options?.stages)} selected={filters.stage_names} onChange={set("stage_names")} />
      <MultiSelect<Situation> label="Situação" options={labelOptions(SITUATION_LABEL)} selected={filters.situations} onChange={set("situations")} />
      <MultiSelect<SlaState> label="SLA" options={labelOptions(SLA_LABEL)} selected={filters.sla} onChange={set("sla")} />
      <button type="button" className="btn" aria-pressed={filters.stage_late}
        onClick={() => onChange({ ...filters, stage_late: !filters.stage_late })}>
        Estágio vencido
      </button>
      <SearchBox value={filters.search} onCommit={set("search")} />
      {hasFilters && <button type="button" className="btn" onClick={() => onChange(EMPTY_FILTERS)}>Limpar filtros</button>}
    </section>
  );
}
