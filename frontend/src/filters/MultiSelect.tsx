import { useEffect, useMemo, useRef, useState } from "react";

export interface SelectOption<V extends string | number> {
  value: V;
  label: string;
}

interface Props<V extends string | number> {
  label: string;
  options: SelectOption<V>[];
  selected: V[];
  onChange: (next: V[]) => void;
}

function useCloseOnOutsideClick(ref: React.RefObject<HTMLElement | null>, close: () => void): void {
  useEffect(() => {
    const onDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) close();
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [ref, close]);
}

/** Searchable checkbox dropdown. Example: <MultiSelect label="Mesa" options={...} selected={ids} onChange={set} /> */
export function MultiSelect<V extends string | number>({ label, options, selected, onChange }: Props<V>) {
  const [open, setOpen] = useState(false);
  const [term, setTerm] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);
  useCloseOnOutsideClick(rootRef, () => setOpen(false));

  const visible = useMemo(() => {
    const needle = term.trim().toLowerCase();
    return needle ? options.filter((o) => o.label.toLowerCase().includes(needle)) : options;
  }, [options, term]);

  const toggle = (value: V) =>
    onChange(selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value]);

  return (
    <div className="dropdown" ref={rootRef}>
      <button type="button" className="btn" aria-expanded={open} onClick={() => setOpen(!open)}>
        {label}
        {selected.length > 0 && <span className="count-pill">{selected.length}</span>}
      </button>
      {open && (
        <div className="dropdown-panel" role="listbox" aria-multiselectable="true" aria-label={label}>
          <input className="input" autoFocus placeholder="Buscar…" value={term}
            onChange={(e) => setTerm(e.target.value)} />
          {selected.length > 0 && (
            <button type="button" className="btn" style={{ marginTop: "var(--sp-2)" }} onClick={() => onChange([])}>
              Limpar seleção
            </button>
          )}
          <div className="dropdown-list">
            {visible.map((option) => (
              <label key={String(option.value)} className="option">
                <input type="checkbox" checked={selected.includes(option.value)}
                  onChange={() => toggle(option.value)} />
                {option.label}
              </label>
            ))}
            {visible.length === 0 && <div className="muted">Nada encontrado</div>}
          </div>
        </div>
      )}
    </div>
  );
}
