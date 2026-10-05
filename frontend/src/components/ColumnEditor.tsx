import { type RefObject, useEffect, useRef, useState } from "react";
import { type ColumnLayout, isLastVisible, moveColumn, toggleColumn } from "../columns/columnLayout";

interface ColumnEditorProps {
  layout: ColumnLayout;
  labelOf: (key: string) => string;
  onChange: (layout: ColumnLayout) => void;
  onReset: () => void;
}

/** Closes the popover on Esc or on a pointer press outside `container`. */
function useDismiss(container: RefObject<HTMLElement | null>, open: boolean, onClose: () => void) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    const onPointer = (e: PointerEvent) => !container.current?.contains(e.target as Node) && onClose();
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [container, open, onClose]);
}

/**
 * "Colunas" button + popover to show/hide and reorder table columns (spec 004, DESIGN.md "Column editor").
 * Example: <ColumnEditor layout={layout} labelOf={columnLabel} onChange={setLayout} onReset={reset} />
 */
export function ColumnEditor({ layout, labelOf, onChange, onReset }: ColumnEditorProps) {
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const close = useRef(() => setOpen(false)).current;
  useDismiss(container, open, close);
  return (
    <div className="column-editor" ref={container}>
      <button type="button" className="btn" aria-expanded={open} aria-haspopup="dialog" onClick={() => setOpen((o) => !o)}>
        Colunas
      </button>
      {open && <ColumnPanel layout={layout} labelOf={labelOf} onChange={onChange} onReset={onReset} />}
    </div>
  );
}

function ColumnPanel({ layout, labelOf, onChange, onReset }: ColumnEditorProps) {
  const [dragFrom, setDragFrom] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState<number | null>(null);
  const clearDrag = () => {
    setDragFrom(null);
    setDragOver(null);
  };
  const drop = (to: number) => {
    if (dragFrom !== null) onChange(moveColumn(layout, dragFrom, to));
    clearDrag();
  };
  return (
    <div className="column-panel" role="dialog" aria-label="Editar colunas">
      <ol className="column-list">
        {layout.map((slot, index) => (
          <li key={slot.key} className={`column-item${dragOver === index ? " drag-over" : ""}`} draggable
            onDragStart={() => setDragFrom(index)} onDragEnd={clearDrag}
            onDragOver={(e) => { e.preventDefault(); setDragOver(index); }} onDrop={() => drop(index)}>
            <span className="drag-handle" aria-hidden="true">⋮⋮</span>
            <label className="column-toggle">
              <input type="checkbox" checked={slot.visible} disabled={isLastVisible(layout, slot.key)}
                onChange={() => onChange(toggleColumn(layout, slot.key))} />
              {labelOf(slot.key)}
            </label>
            <MoveButtons index={index} count={layout.length} label={labelOf(slot.key)}
              onMove={(to) => onChange(moveColumn(layout, index, to))} />
          </li>
        ))}
      </ol>
      <button type="button" className="btn" onClick={onReset}>Restaurar padrão</button>
    </div>
  );
}

function MoveButtons({ index, count, label, onMove }: { index: number; count: number; label: string; onMove: (to: number) => void }) {
  return (
    <span className="column-move">
      <button type="button" className="btn" aria-label={`Mover ${label} para cima`} disabled={index === 0}
        onClick={() => onMove(index - 1)}>↑</button>
      <button type="button" className="btn" aria-label={`Mover ${label} para baixo`} disabled={index === count - 1}
        onClick={() => onMove(index + 1)}>↓</button>
    </span>
  );
}
