import { useEffect, useRef, type CSSProperties } from "react";
import { api } from "../api/client";
import type { TicketActivity, TicketFile, TicketFollowup } from "../api/types";
import { useFetch } from "../api/useFetch";
import { fmtBytes, fmtDateTime } from "../format";
import { htmlToText } from "../richText";
import { Pill } from "./Pill";
import { TicketDescription, TicketFields, TicketHeader } from "./TicketFields";

const FOLLOWUP_STYLE: Record<TicketFollowup["kind"], { label: string; tone: string }> = {
  answer: { label: "Resposta", tone: "var(--series-1)" },
  internal: { label: "Interna", tone: "var(--series-4)" },
};

function FileList({ files }: { files: TicketFile[] }) {
  return (
    <ul className="file-list">
      {files.map((file) => (
        <li key={file.id}>
          {file.url ? <a href={file.url} target="_blank" rel="noreferrer noopener">{file.file_name ?? "arquivo"}</a> : file.file_name}
          <span className="file-meta">{[file.content_type, fmtBytes(file.size)].filter(Boolean).join(" · ")}</span>
        </li>
      ))}
    </ul>
  );
}

function FollowupItem({ followup }: { followup: TicketFollowup }) {
  const style = FOLLOWUP_STYLE[followup.kind];
  return (
    <article className="followup" style={{ "--tone": style.tone } as CSSProperties}>
      <div className="followup-head">
        <Pill tone={style.tone}>{style.label}</Pill>
        <span className="followup-author">{followup.author ?? "–"}</span>
        <span className="muted">{fmtDateTime(followup.created_at)}</span>
      </div>
      <div className="description">{htmlToText(followup.text) || "(sem texto)"}</div>
      {followup.files.length > 0 && <FileList files={followup.files} />}
    </article>
  );
}

function ActivityContent({ activity }: { activity: TicketActivity }) {
  return (
    <>
      <section className="modal-section">
        <h3>Anexos ({activity.files.length})</h3>
        {activity.files.length ? <FileList files={activity.files} /> : <p className="muted">Nenhum anexo.</p>}
      </section>
      <section className="modal-section">
        <h3>Follow-ups ({activity.followups.length})</h3>
        {activity.followups.length ? (
          <div className="timeline">{activity.followups.map((f) => <FollowupItem key={`${f.kind}-${f.id}`} followup={f} />)}</div>
        ) : <p className="muted">Nenhum follow-up.</p>}
      </section>
    </>
  );
}

/** Attachments + follow-ups, live from Tiflux on every open (not cached, so new answers show up). */
function TicketActivitySections({ ticketNumber }: { ticketNumber: number }) {
  const result = useFetch((signal) => api.ticketActivity(ticketNumber, signal), String(ticketNumber));
  if (result.error) return <p className="error modal-section">Não foi possível carregar anexos e follow-ups do Tiflux.</p>;
  if (!result.data) return <p className="muted modal-section">Carregando anexos e follow-ups do Tiflux…</p>;
  return <ActivityContent activity={result.data} />;
}

/**
 * Full ticket view in a native <dialog>: Esc, focus trap and focus return come from the browser.
 * Example: {open !== null && <TicketModal ticketNumber={open} onClose={() => setOpen(null)} />}
 */
export function TicketModal({ ticketNumber, onClose }: { ticketNumber: number; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const summary = useFetch(() => api.ticketSummary(ticketNumber), String(ticketNumber));
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  // The dialog's `close` event is async and browsers may defer it (seen in a background tab, Chrome 154),
  // so unmounting is driven here; Esc arrives through the synchronous `cancel` event instead.
  const close = () => {
    dialog.current?.close(); // restores focus to the row that opened it
    onClose();
  };
  const closeButton = <button type="button" className="btn" onClick={close}>Fechar</button>;

  return (
    // A click whose target is the <dialog> itself landed on the backdrop, outside the panel content.
    <dialog ref={dialog} className="modal" aria-label={`Chamado ${ticketNumber}`}
      onCancel={(event) => { event.preventDefault(); close(); }}
      onClick={(event) => event.target === dialog.current && close()}>
      <TicketHeader ticketNumber={ticketNumber} summary={summary.data} action={closeButton} />
      {summary.error && <p className="error">Chamado não encontrado no banco local.</p>}
      {summary.data && <TicketFields summary={summary.data} />}
      <section className="modal-section">
        <h3>Descrição</h3>
        <TicketDescription ticketNumber={ticketNumber} />
      </section>
      <TicketActivitySections ticketNumber={ticketNumber} />
    </dialog>
  );
}
