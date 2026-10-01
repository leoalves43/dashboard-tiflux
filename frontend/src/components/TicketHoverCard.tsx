import { useCallback, useEffect, useRef, useState, type MouseEvent } from "react";
import { api } from "../api/client";
import { useFetch } from "../api/useFetch";
import { TicketDescription, TicketFields, TicketHeader } from "./TicketFields";

const HOVER_DELAY_MS = 400; // long enough that sweeping the mouse across rows opens nothing
const CARD_WIDTH = 420;
const POINTER_GAP = 16;

interface HoverTarget {
  ticketNumber: number;
  x: number;
  y: number;
}

/**
 * Shows a ticket after the pointer rests on its row. Example:
 *   const hover = useTicketHover(); <tr {...hover.rowProps(n)} /> {hover.target && <TicketHoverCard {...hover.target} />}
 */
export function useTicketHover() {
  const [target, setTarget] = useState<HoverTarget | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const pending = useRef<HoverTarget | null>(null);
  const cancel = useCallback(() => {
    window.clearTimeout(timer.current);
    pending.current = null;
    setTarget(null);
  }, []);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  // The card is fixed to the viewport, so any scroll (page or table) would leave it detached from its row.
  useEffect(() => {
    if (!target) return;
    window.addEventListener("scroll", cancel, true);
    return () => window.removeEventListener("scroll", cancel, true);
  }, [target, cancel]);

  const rowProps = (ticketNumber: number) => ({
    onMouseEnter: (event: MouseEvent) => {
      pending.current = { ticketNumber, x: event.clientX, y: event.clientY };
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => setTarget(pending.current), HOVER_DELAY_MS);
    },
    onMouseMove: (event: MouseEvent) => {
      if (pending.current) pending.current = { ticketNumber, x: event.clientX, y: event.clientY };
    },
    onMouseLeave: cancel,
  });
  return { target, rowProps, cancel };
}

function cardPosition(x: number, y: number) {
  const left = Math.max(POINTER_GAP, Math.min(x + POINTER_GAP, window.innerWidth - CARD_WIDTH - POINTER_GAP));
  // Below the pointer in the top half of the screen, above it in the bottom half, so it never overflows.
  return y < window.innerHeight / 2 ? { left, top: y + POINTER_GAP } : { left, bottom: window.innerHeight - y + POINTER_GAP };
}

export function TicketHoverCard({ ticketNumber, x, y }: HoverTarget) {
  const summary = useFetch(() => api.ticketSummary(ticketNumber), String(ticketNumber));
  return (
    <div className="hovercard" role="tooltip" style={cardPosition(x, y)}>
      {summary.data ? (
        <>
          <TicketHeader summary={summary.data} />
          <TicketFields summary={summary.data} />
          <TicketDescription ticketNumber={ticketNumber} />
        </>
      ) : (
        <div className={summary.error ? "error" : "muted"}>{summary.error ? "Chamado não encontrado." : "Carregando…"}</div>
      )}
    </div>
  );
}
