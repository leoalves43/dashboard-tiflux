import { useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { TicketActivity, TicketFile, TicketFollowup } from "../api/types";
import { useFetch } from "../api/useFetch";
import { fmtBytes, fmtDateTime } from "../format";
import { htmlToText } from "../richText";
import { TicketDescription, TicketFields, TicketHeader } from "./TicketFields";

type CommunicationKind = TicketFollowup["kind"];

// Public = answers exchanged with the client; internal = notes between technicians (as tabs in Tiflux).
const COMMUNICATION_STYLE: Record<CommunicationKind, { tab: string; empty: string; tone: string }> = {
  answer: { tab: "Pública", empty: "Nenhuma comunicação pública.", tone: "var(--series-1)" },
  internal: { tab: "Interna", empty: "Nenhuma comunicação interna.", tone: "var(--series-4)" },
};
const COMMUNICATION_KINDS: CommunicationKind[] = ["answer", "internal"];

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

function CommunicationItem({ followup }: { followup: TicketFollowup }) {
  return (
    <article className="followup" style={{ "--tone": COMMUNICATION_STYLE[followup.kind].tone } as CSSProperties}>
      <div className="followup-head">
        <span className="followup-author">{followup.author ?? "–"}</span>
        <span className="muted">{fmtDateTime(followup.created_at)}</span>
      </div>
      <div className="description">{htmlToText(followup.text) || "(sem texto)"}</div>
      {followup.files.length > 0 && <FileList files={followup.files} />}
    </article>
  );
}

function Communications({ followups }: { followups: TicketFollowup[] }) {
  const [kind, setKind] = useState<CommunicationKind>("answer");
  const shown = followups.filter((f) => f.kind === kind);
  const count = (k: CommunicationKind) => followups.filter((f) => f.kind === k).length;
  return (
    <section className="modal-section">
      <div className="card-head">
        <h3>Comunicações</h3>
        <div className="card-actions" role="group" aria-label="Tipo de comunicação">
          {COMMUNICATION_KINDS.map((k) => (
            <button key={k} type="button" className="btn" aria-pressed={kind === k} onClick={() => setKind(k)}>
              {COMMUNICATION_STYLE[k].tab} ({count(k)})
            </button>
          ))}
        </div>
      </div>
      {shown.length ? (
        <div className="timeline">{shown.map((f) => <CommunicationItem key={f.id} followup={f} />)}</div>
      ) : <p className="muted">{COMMUNICATION_STYLE[kind].empty}</p>}
    </section>
  );
}

function ActivityContent({ activity }: { activity: TicketActivity }) {
  return (
    <>
      <section className="modal-section">
        <h3>Anexos ({activity.files.length})</h3>
        {activity.files.length ? <FileList files={activity.files} /> : <p className="muted">Nenhum anexo.</p>}
      </section>
      <Communications followups={activity.followups} />
    </>
  );
}

/** Attachments + communications, live from Tiflux on every open (not cached, so new answers show up). */
function TicketActivitySections({ ticketNumber }: { ticketNumber: number }) {
  const result = useFetch((signal) => api.ticketActivity(ticketNumber, signal), String(ticketNumber));
  if (result.error) return <p className="error modal-section">Não foi possível carregar anexos e comunicações do Tiflux.</p>;
  if (!result.data) return <p className="muted modal-section">Carregando anexos e comunicações do Tiflux…</p>;
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
